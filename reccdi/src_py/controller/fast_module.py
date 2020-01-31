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
import scipy.fftpack as sf
# import reccdi.src_py.cyth.bridge_cpu as bridge_cpu
# import reccdi.src_py.cyth.bridge_opencl as bridge_opencl
# import reccdi.src_py.cyth.bridge_cuda as bridge_cuda
import copy


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['fast_module_reconstruction',]


def fast_module_reconstruction(proc, device, conf, data, coh_dims, image=None, support=None, coherence=None):
    """
    This function calls a bridge method corresponding to the requested processor type. The bridge method is an access
    to the CFM (Calc Fast Module). When reconstruction is completed the function retrieves results from the CFM.
    The data received is max centered and the array is ordered "C". The CFM requires data zero-frequency component at
    the center of the spectrum and "F" array order. Thus the data is modified at the beginning.

    Parameters
    ----------
    proc : str
        a string indicating the processor type

    device : int
        device id assigned to this reconstruction

    conf : dict
        configuration map

    data : array
        a 3D np array containing pre-processed experiment data

    coh_dims : tuple
        shape of coherence array

    image : numpy array
        initial image for reconstruction or None

    support : numpy array
        support corresponding to image or None

    coherence : numpy array
       coherence corresponding to image

    Returns
    -------
    image : numpy array
        reconstructed image

    support : numpy array
        support for reconstructed image

    coherence : numpy array
        coherence for reconstructed image

    er : list
        a vector containing errors for each iteration
    """
    if proc == 'cpu':
        import reccdi.src_py.cyth.bridge_cpu as bridge_cpu
        fast_module = bridge_cpu.PyBridge()
    elif proc == 'opencl':
        import reccdi.src_py.cyth.bridge_opencl as bridge_opencl
        fast_module = bridge_opencl.PyBridge()
    elif proc == 'cuda':
        import reccdi.src_py.cyth.bridge_cuda as bridge_cuda
        fast_module = bridge_cuda.PyBridge()

    # shift data
    data = sf.fftshift(data)
    dims = data.shape[::-1]
    print("data dims", dims)
    data_l = data.flatten().tolist()
    if image is None:
        # print("Running start_calc")
        fast_module.start_calc(device, data_l, dims, conf)
    elif support is None:
        image = image.flatten()
        fast_module.start_calc_with_guess(device, data_l, image.real.tolist(), image.imag.tolist(), dims, conf)
    elif coherence is None:
        image = image.flatten()
        support = support.flatten()
        fast_module.start_calc_with_guess_support(device, data_l, image.real.tolist(), image.imag.tolist(), support.tolist(), dims, conf)
    else:
        image = image.flatten()
        support = support.flatten()
        coh_dims1 = (coh_dims[2], coh_dims[1], coh_dims[0])
        coherence = coherence.flatten()

        fast_module.start_calc_with_guess_support_coh(device, data_l, image.real.tolist(), image.imag.tolist(), support.tolist(), dims, coherence.tolist(), coh_dims, conf)

    er = copy.deepcopy(fast_module.get_errors())
    if len(er) == 1 and er[0] == -1:
        # run into Nan during reconstruction
        fast_module.cleanup()
        return None, None, None, None, None, None, None
    image_r = np.asarray(fast_module.get_image_r())
    image_i = np.asarray(fast_module.get_image_i())
    image = image_r + 1j*image_i  #no need to deepcopy the real and imag parts since this makes a new array

    # normalize image
    mx = np.abs(image).max()
    image = image/mx

    support = copy.deepcopy(np.asarray(fast_module.get_support()))
    coherence = copy.deepcopy(np.asarray(fast_module.get_coherence()))

    image.shape=dims[::-1]
    support = np.reshape(support, dims[::-1])
    if coherence.shape[0] > 1:
        coherence = np.reshape(coherence, coh_dims[::-1])
    else:
        coherence = None

    reciprocal_r = copy.deepcopy(np.asarray(fast_module.get_reciprocal_r()))
    reciprocal_i = copy.deepcopy(np.asarray(fast_module.get_reciprocal_i()))
    reciprocal = reciprocal_r + 1j*reciprocal_i
    reciprocal = np.reshape(reciprocal, dims[::-1])
    reciprocal = sf.ifftshift(reciprocal)

    iter_array = copy.deepcopy(np.asarray(fast_module.get_iter_flow()))
    flow = copy.deepcopy(list(fast_module.get_flow()))
    flow_len = len(flow)
    iter_array = np.reshape(iter_array, (flow_len, int(iter_array.shape[0]/flow_len)))

    fast_module.cleanup()

    return image, support, coherence, er, reciprocal, flow, iter_array

