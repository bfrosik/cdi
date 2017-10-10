#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.
This module controls the reconstruction process. The user has to provide parameters such as type of processor, data, and configuration.
The processor specifies which library will be used by CFM (Calc Fast Module) that performs the processor intensive calculations. The module
can be run on cpu, or gpu. Depending on the gpu hardware and library, one can use opencl or cuda library.
The module starts the data preparation routines, calls for reconstruction using the CFM, and prepares the reconstructed data for
visualization.
"""

import numpy as np
import src_py.utilities.utils as ut
import src_py.utilities.CXDVizNX as CX
import pylibconfig2 as cfg
import os
import scipy.fftpack as sf
import scipy.io as sio
#import src_py.cyth.bridge_cpu as bridge_cpu
import src_py.cyth.bridge_opencl as bridge_opencl
import tifffile as tf


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'prepare_data',
           'do_reconstruction',
           'reconstruction']

def read_config(config):
    """
    This function gets configuration file. It checks if the file exists and parses it into a map.
    
    Parameters
    ----------
    config : str
        configuration file name, including path
        
    Returns
    -------
    config_map : dict
        a map containing parsed configuration, None if the given file does not exist
    """
    
    if os.path.isfile(config):
        with open(config, 'r') as f:
            config_map = cfg.Config(f.read())
            return config_map;
    else:
        return None

def prepare_data(config_map, data):
    """
    This function prepares raw data for reconstruction. It uses configured parameters. The preparation consists of the following steps:
    1. clearing the noise - the values below an amplitude threshold are set to zero
    2. removing the "aliens" - aliens are areas that are effect of interference. The area is manually set in a configuration file 
    after inspecting the data.
    3. binning - adding amplitudes of several consecutive points. Binning can be done in any dimension.
    4. amplitudes are set to sqrt
    5. centering - finding the greatest amplitude and locating it at a center of new array. Typically several new rows/columns/slices
    are added. These are filled with zeros. When changing the dimension the code finds the smallest possible dimension that is 
    supported by opencl library (multiplier of 2, 3, and 5).
    6. shift in place - shift the zero-frequency component to the center of the spectrum
    
    Parameters
    ----------
    config_map : dict
        configuration map
        
    data : array
        a 3D np array containing experiment data
        
    Returns
    -------
    data : array
        a 3D np array containing data after the preprocessing
    """
    
    # zero out the noise
    data = np.where(data < config_map.amp_threshold, 0, data)
    print (data.shape)

    # zero out the aliens
    try:
        aliens = config_map.aliens
        for alien in aliens:
            data[alien[0]:alien[3], alien[1]:alien[4], alien[2]:alien[5]]=0
    except AttributeError:
        pass

    # do binning
    try:
        binsizes = config_map.binning
        data = ut.binning(data, binsizes)
    except AttributeError:
        pass

    # square root data
    data = np.sqrt(data)

    # get centered array
    try:
        center_shift = tuple(config_map.center_shift)
    except AttributeError:
        center_shift = (0,0,0)

    data = ut.get_centered(data, center_shift)

    # zero pad array
    try:
        pad = tuple(config_map.zero_pad)
    except AttributeError:
        center_shift = (0,0,0)
    data = ut.zero_pad(data, pad)

    # shift data
    data=sf.fftshift(data)
    return data
    
def prepare_data1(config_map, data):
    rdata=tf.imread("/home/phoebus/BFROSIK/CDI/S149/Staff14-3_S0149.tif")
    rdata=np.where( rdata < 2, 0, rdata)

#Crop in first dim around brightest pixel. This speeds things up a lot. 
    cdata=rdata[76-32:76+32,:,:]
    dims=cdata.shape
    print "dims/2", np.array(dims)/2.
    # do binning
    try:
        binsizes = config_map.binning
        cdata = ut.binning(cdata, binsizes)
    except AttributeError:
        pass
    data=np.sqrt(cdata)

#Sqrt and center the brightest pixel in the other two dims
    print np.unravel_index(np.argmax(cdata), cdata.shape)
#data=np.roll(data, -1, 0)
    data=np.roll(data, 10, 1)
    data=np.roll(data, -5, 2)
    print 'data max before shift',data[0,0,0], data.max()
    data=np.fft.fftshift(data)
    print 'data max after shift',data[0,0,0], data.max()
    return data

def prepare_data2(config_map, data):
    print np.unravel_index(np.argmax(data), data.shape)
#data=np.roll(data, -1, 0)
    #data=np.roll(data, 10, 1)
    #data=np.roll(data, -5, 2)
    data=np.roll(data, 1, 0)
    data=np.roll(data, 1, 1)
    data=np.roll(data, 1, 2)
    data=np.fft.fftshift(data)
    print 'data at 0 and max', data[0,0,0], data.max()
    return data

def do_reconstruction(proc, data, conf):
    """
    This function calls a bridge method corresponding to the requested processor type. The bridge method is an access to the CFM
    (Calc Fast Module). When reconstruction is completed the function retrieves results from the CFM.
    
    Parameters
    ----------
    proc : str
        a string indicating the processor type
        
    data : array
        a 3D np array containing pre-processed experiment data
        
    conf : dict
        configuration map
        
    Returns
    -------
    image_r : array
        a 3D np real part array containing reconstructed image
        
    image_i : array
        a 3D np imaginary part array containing reconstructed image
        
    er : array
        a vector containing mean error for each iteration
    """
    if proc == 'cpu':
        bridge = bridge_cpu
    elif proc == 'opencl': 
        bridge = bridge_opencl

    data = np.swapaxes(data,1,2)

    dims = data.shape
    dims1 = (dims[2], dims[1], dims[0])
    print 'data norm in reconstruction',  sum(sum(sum(abs(data)**2)))
    fast_module = bridge.PyBridge()

    data_l = data.flatten().tolist()
    fast_module.start_calc(data_l, dims1, conf)
    er = fast_module.get_errors()
    image_r = np.asarray(fast_module.get_image_r())
    image_i = np.asarray(fast_module.get_image_i())
    support = np.asarray(fast_module.get_support())
    coherence = np.asarray(fast_module.get_coherence())

    image_r = np.reshape(image_r, dims)
    image_i = np.reshape(image_i, dims)
    support = np.reshape(support, dims)

    image_r = np.swapaxes(image_r, 2,0)
    image_i = np.swapaxes(image_i, 2,0)
    support = np.swapaxes(support, 2,0)

    return image_r, image_i, er, support, coherence


def write_simple(arr, filename):
    from tvtk.api import tvtk, write_data

    id=tvtk.ImageData()
    id.point_data.scalars=abs(arr.ravel(order='F'))
    id.dimensions=arr.shape
    write_data(id, filename)

def reconstruction(proc, filename, conf):
    """
    This function is called by the user. It checks whether the data is valid and configuration file exists.
    It calls function to pre-process the data, and then to run reconstruction.
    The reconstruction results, image and errors are returned.
    
    Parameters
    ----------
    proc : str
        a string indicating the processor type
        
    filename : str
        name of a file containing experiment data
        
    conf : str
        configuration file name
        
    Returns
    -------
    image : array
        a 3D np array containing reconstructed image
        
    er : array
        a vector containing mean error for each iteration
    """

    data = ut.get_array_from_tif(filename)
    if len(data.shape) > 3:
        print ("this program supports 3d images only")
        return None, None

    config_map = read_config(conf)
    if config_map is None:
        print ("can't read configuration file")
        return None, None

    data = prepare_data2(config_map, data)
    tf.imsave("data.tif", np.ceil(100 * data).astype(np.int32))
    write_simple(data, "simple_data.vtk")
    dims = data.shape
    print 'data size', data.shape

    image_r, image_i, errors, support, coherence = do_reconstruction(proc, data, conf)

    image = image_r + 1j*image_i
    # save image and support in .mat files
    image_dict = {}
    support_dict = {}
    image_dict['pnm'] = image
    sio.savemat('/local/bfrosik/test/pnm.mat', image_dict)
    support_dict['support'] = support
    sio.savemat('/local/bfrosik/test/support.mat', support_dict)

    try:
        prefix = config_map.res
    except AttributeError:
        prefix = ''
    write_simple(image, prefix + "simple_amp_ph.vtk")
    write_simple(support, prefix + "simple_support.vtk")

    CX.save_CX(conf, image, prefix + 'img_cx_test')
    CX.save_CX(conf, support, prefix + 'support_cx_test')
    CX.save_trans_CX(conf, image, support, prefix + 'cx_xfer_test')

    if coherence is not None and len(coherence.shape) > 1:
        coh_size = int(round(coherence.shape[0]**(1./3.)))
        coh_dims = (coh_size, coh_size, coh_size,)
        coherence = np.reshape(coherence, coh_dims)
        coherence = np.swapaxes(coherence, 2, 0)
        write_simple(coherence, prefix + "simple_coh.vtk")
        # x_pad_pre = (dims[0] - coh_size)/2
        # x_pad_post = dims[0] - x_pad_pre - coh_size
        # y_pad_pre = (dims[1] - coh_size)/2
        # y_pad_post = dims[1] - x_pad_pre - coh_size
        # z_pad_pre = (dims[2] - coh_size)/2
        # z_pad_post = dims[2] - x_pad_pre - coh_size
        # coh = np.lib.pad(coherence, ((x_pad_pre, x_pad_post),(y_pad_pre, y_pad_post), (z_pad_pre, z_pad_post)), 'constant', constant_values=((0.0,0.0),(0.0,0.0),(0.0,0.0)))
        # coh = ut.flip(coh,0)
        # coh = ut.flip(coh,1)
        # coh = ut.flip(coh,2)
        # fft_coh = sf.ifftn(np.fft.fftshift(coh))
        # np.fft.fftshift(fft_coh)
        tf.imsave("coherence.tif", np.ceil(1000*abs(coherence)).astype(np.int32))


    print 'image, support shape', image.shape, support.shape


    

