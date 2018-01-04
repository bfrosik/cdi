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
import src_py.utilities.CXDVizNX as cx
import scipy.fftpack as sf
import matplotlib.pyplot as plt
import src_py.cyth.bridge_cpu as bridge_cpu
import src_py.cyth.bridge_opencl as bridge_opencl
# import src_py.cyth.bridge_cuda as bridge_cuda


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['fast_module_reconstruction',
           'write_simple',
           'reconstruction']


def fast_module_reconstruction(proc, data, conf, image=None, support=None, coherence=None):
    """
    This function calls a bridge method corresponding to the requested processor type. The bridge method is an access
    to the CFM (Calc Fast Module). When reconstruction is completed the function retrieves results from the CFM.
    The data received is max centered and the array is ordered "C". The CFM requires data zero-frequency component at
    the center of the spectrum and "F" array order. Thus the data is modified at the beginning.
    
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

    stage = 0
    if image is not None:
        stage = 1

    # shift data
    data=sf.fftshift(data)
    data = np.swapaxes(data,1,2)

    dims = data.shape
    dims1 = (dims[2], dims[1], dims[0])
    fast_module = bridge.PyBridge()

    data_l = data.flatten().tolist()
    fast_module.start_calc(data_l, dims1, conf, stage)
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


def reconstruction(proc, conf, data, image, support, coherence):
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

    if image is None:
        image, support, coherence, errors = fast_module_reconstruction(proc, data, conf)
    else:
        image, support, coherence, errors = fast_module_reconstruction(proc, data, conf, image, support, coherence)


    cx.save_CX(conf, image, support)

    errors.pop(0)
    plt.plot(errors)
    plt.ylabel('errors')
    plt.show()

    print 'image, support shape', image.shape, support.shape

    return image, support, coherence, errors


