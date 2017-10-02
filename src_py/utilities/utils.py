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
This module is a suite of utility mehods.
"""

import tifffile as tf
import numpy as np


def get_array_from_tif(filename):
    """
    This method reads tif type file containing experiment data and returns the data as array.

    Parameters
    ----------
    filename : str
        a filename containing the experiment data

    Returns
    -------
    data : array
        an array containing the experiment data
    """
    
    return tf.imread(filename)


def get_opencl_dim(dim, step):
    """
    This function calculates the dimension supported by opencl library (i.e. is multiplier of 2,3, or 5) and is closest to the 
    given starting dimension, and spaced by the given step.
    If the dimension is not supported the function adds step value and verifies the new dimension. It iterates until it finds
    supported value.

    Parameters
    ----------
    dim : int
        a dimension that needs to be tranformed to one that is supported by the opencl library, if it is not already
        
    step : int
        a delta to increase the dimension

    Returns
    -------
    dim : int
        a dimension that is supported by the opencl library, and closest to the original dimension by n*step
    """

    def is_correct(x):
        sub = x
        while sub%2 == 0:
            sub = sub/2
        while sub%3 == 0:
            sub = sub/3
        while sub%5 == 0:
            sub = sub/5
        return sub == 1

    new_dim = dim
    while not is_correct(new_dim):
        new_dim += step
    return new_dim
    

def binning(array, binsizes):
    """
    This function does the binning of the array. The array is binned in each dimension by the corresponding binsizes elements.
    If binsizes list is shorter than the array dimensions, the remaining dimensions are not binned. The elements in
    a bucket are summed.

    Parameters
    ----------
    array : array
        the original array to be binned
        
    binsizes : list
        a list defining binning buckets for corresponding dimensions

    Returns
    -------
    array : array
        the binned array
    """

    data_dims = array.shape
    # trim array 
    for ax in range(len(binsizes)):
        cut_slices = range(data_dims[ax] - data_dims[ax] % binsizes[ax], data_dims[ax])
        array = np.delete(array, cut_slices, ax)

    binned_array = array
    new_shape = list(array.shape)

    for ax in range(len(binsizes)):
        if binsizes[ax] > 1:
            new_shape[ax] = binsizes[ax]
            new_shape.insert(ax, array.shape[ax] / binsizes[ax])
            binned_array = np.reshape(binned_array, tuple(new_shape))
            binned_array = np.sum(binned_array, axis=ax+1)
            new_shape = list(binned_array.shape)
    return binned_array
   

def get_centered(array, center_shift):
    """
    This function finds a greatest value in the array, and puts it in a center of a new array. The extra elements in the new 
    array are set to 0.

    Parameters
    ----------
    array : array
        the original array to be centered
        
    center_shift : list
        a list defining shift of the center

    Returns
    -------
    array : array
        the centered array
    """
    max_coordinates = list(np.unravel_index(np.argmax(array), array.shape))
    max_coordinates = np.add(max_coordinates, center_shift)
    shape = array.shape
    new_shape = []
    shift = []
    # find new shape that can fit the array with max_coordinate in center
    for ax in range(len(shape)):
        if max_coordinates[ax] <= int(shape[ax]/2):
            new_shape.append(2*(shape[ax] - max_coordinates[ax]))
        else:
            new_shape.append(2*max_coordinates[ax])       
        shift.append(int(new_shape[ax]/2) - max_coordinates[ax])

    centered = np.zeros(tuple(new_shape), dtype=array.dtype)

    # this supports 3D arrays
    centered[shift[0]:shift[0]+shape[0], shift[1]:shift[1]+shape[1], shift[2]:shift[2]+shape[2]] = array

    return centered    

def zero_pad(array, pad):
    """
    This function adds to each dimension of the array elements defined by pad. The elements are added to the 
    beginning of array and end by the same number, so the original array is centered. The dimensions of the new array are
    supported by the opencl library. 
    

    Parameters
    ----------
    array : array
        the array to pad

    pad : list
        list of three pad values, for each dimension
        
    Returns
    -------
    array : array
        the padded array
    """
    # calculate the opencl dimensions
    dims = array.shape
    x_dim = get_opencl_dim(dims[0] + 2*pad[0], 2)
    x_pad = (x_dim - dims[0])/2
    y_dim = get_opencl_dim(dims[1] + 2*pad[1], 2)
    y_pad = (y_dim - dims[1])/2
    z_dim = get_opencl_dim(dims[2] + 2*pad[2], 2)
    z_pad = (z_dim - dims[2])/2
    return np.lib.pad(array, ((x_pad, x_pad),(y_pad, y_pad), (z_pad, z_pad)), 'constant', constant_values=((0.0,0.0),(0.0,0.0),(0.0,0.0))).copy()

def crop_center(arr, new_size):
    size = arr.shape
    return arr[ (size[0]-new_size[0])/2 : (size[0]-new_size[0])/2 + new_size[0], (size[1]-new_size[1])/2 : (size[1]-new_size[1])/2 + new_size[1], (size[2]-new_size[2])/2 : (size[2]-new_size[2])/2 + new_size[2]]

def flip(m, axis):
    """
    Copied from numpy 1.12.0.

    """
    #if not hasattr(m, 'ndim'):
    #    m = asarray(m)
    indexer = [slice(None)] * m.ndim
    try:
        indexer[axis] = slice(None, None, -1)
    except IndexError:
        raise ValueError("axis=%i is invalid for the %i-dimensional input array"
                         % (axis, m.ndim))
    return m[tuple(indexer)]





