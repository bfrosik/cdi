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
    This function finds a greatest value in the array, and puts it in a center of a new array. The dimentions of the new array are
    supported by the opencl library. The extra elements in the new array are set to 0.

    Parameters
    ----------
    array : array
        the original array to be centerred
        
    center_shift : list
        a list defining shift of the center

    Returns
    -------
    array : array
        the centerred array
    """
    max_coordinates = list(np.unravel_index(np.argmax(array), array.shape))
    max_coordinates = np.add(max_coordinates, center_shift)
    shape = array.shape
    new_shape = []
    shift = []
    # find new shape that can fit the array with max_coordinate in center and 
    # which has dimensions supported by opencl
    for ax in range(len(shape)):
        if max_coordinates[ax] <= shape[ax]/2:
            new_shape.append(get_opencl_dim(2*(shape[ax] - max_coordinates[ax]), 2))
        else:
            new_shape.append(get_opencl_dim(2*max_coordinates[ax], 2))        
        shift.append(new_shape[ax]/2 - max_coordinates[ax])
        
    centered = np.zeros(tuple(new_shape))

    # this supports 3D arrays
    centered[shift[0]:shift[0]+shape[0], shift[1]:shift[1]+shape[1], shift[2]:shift[2]+shape[2]] = array

    return centered    


