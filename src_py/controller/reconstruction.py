#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
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
import src_py.utilities.CXDVizNX as cx
import pylibconfig2 as cfg
import os
import scipy.fftpack as sf
import src_py.cyth.bridge_cpu as bridge_cpu
import src_py.cyth.bridge_opencl as bridge_opencl
#import src_py.cyth.bridge_cuda as bridge_cuda
#import tifffile as tf


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'prepare_data',
           'fast_module_reconstruction',
           'write_simple',
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
    
def fast_module_reconstruction(proc, data, conf):
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
    # elif proc == 'cuda':
    #     bridge = bridge_cuda

    data = np.swapaxes(data,1,2)

    dims = data.shape
    dims1 = (dims[2], dims[1], dims[0])
    fast_module = bridge.PyBridge()

    data_l = data.flatten().tolist()
    fast_module.start_calc(data_l, dims1, conf)
    er = fast_module.get_errors()
    image_r = np.asarray(fast_module.get_image_r())
    image_i = np.asarray(fast_module.get_image_i())
    image = image_r + 1j*image_i
    # normalize image
    mx = max(np.absolute(image).ravel().tolist())
    image = image/mx
    support = np.asarray(fast_module.get_support())
    coherence = np.asarray(fast_module.get_coherence())

    image = np.reshape(image, dims)
    support = np.reshape(support, dims)

    image = np.swapaxes(image, 2,0)
    support = np.swapaxes(support, 2,0)
    image = np.swapaxes(image, 1, 0)
    support = np.swapaxes(support, 1, 0)

    if coherence.shape[0] > 1:
        coh_size = int(round(coherence.shape[0] ** (1. / 3.)))
        coh_dims = (coh_size, coh_size, coh_size,)
        coherence = np.reshape(coherence, coh_dims)
        coherence = np.swapaxes(coherence, 2, 0)
        coherence = np.swapaxes(coherence, 1, 0)
    else:
        coherence = None

    return image, support, coherence, er


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

    config_map = read_config(conf)
    if config_map is None:
        print ("can't read configuration file")
        return None, None

    data = prepare_data(config_map, data)

    try:
        action = config_map.action
    except AttributeError:
        action = 2

    try:
        save_results = config_map.save_results
        try:
            save_dir = config_map.save_dir
            if not save_dir.endswith('/'):
                save_dir = save_dir + '/'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
        except AttributeError:
            print ("save_dir not configured")
    except AttributeError:
        save_results = False

    if action == 1 or save_results:
        np.save(save_dir+'/data.npy', data)

    image, support, coherence, errors = fast_module_reconstruction(proc, data, conf)

    # try:
    #     save_results = config_map.save_data
    #     if save_results:
    #         np.save('image.npy', image)
    #         np.save('support.npy', support)
    # except AttributeError:
    #     pass

    # try:
    #     res_dir = config_map.res_dir
    #     if not res_dir.endswith('/'):
    #         res_dir = res_dir + '/'
    #     if not os.path.exists(res_dir):
    #         os.makedirs(res_dir)
    # except AttributeError:
    #     res_dir = ''
    write_simple(image, save_dir + "simple_amp_ph.vtk")
    write_simple(support, save_dir + "simple_support.vtk")

    cx.save_CX(conf, image, support, save_dir + 'cx')

    if coherence is not None:
        write_simple(coherence, save_dir + "simple_coh.vtk")

    # plot error


    print 'image, support shape', image.shape, support.shape


    

