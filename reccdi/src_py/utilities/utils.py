#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.
This module is a suite of utility mehods.
"""

import tifffile as tf
import pylibconfig2 as cfg
import numpy as np
import scipy.fftpack as sf
import os
import logging
import stat
from functools import reduce
import GPUtil

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_tif',
           'get_opencl_dim',
           'binning',
           'get_centered',
           'adjust_dimensions',
           'crop_center',
           'flip']


def get_logger(name, ldir=''):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    log_file = os.path.join(ldir, 'default.log')
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def read_tif(filename):
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

    ar = tf.imread(filename).transpose()
    #ar = np.swapaxes(ar, 0, 2)
    #ar = np.swapaxes(ar, 0, 1)
    return ar


def save_tif(arr, tif_file):
    # arr = np.swapaxes(arr, 0, 2)
    # arr = np.swapaxes(arr, 1, 2)
    #arr = np.swapaxes(arr, 0, 1)
    #arr = np.swapaxes(arr, 0, 2)
    tf.imsave(tif_file, arr.transpose().astype(np.float32))


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
        print(config)
        with open(config, 'r') as f:
            config_map = cfg.Config(f.read())
            return config_map;
    else:
        return None


def get_good_dim(dim):
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
        if sub % 3 == 0:
            sub = sub / 3
        if sub % 3 == 0:
            sub = sub / 3
        if sub % 5 == 0:
            sub = sub / 5
        while sub % 2 == 0:
            sub = sub / 2
        return sub == 1

    new_dim = dim
    if new_dim % 2 == 1:
        new_dim += 1
    while not is_correct(new_dim):
        new_dim += 2
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
            new_shape.insert(ax, int(array.shape[ax] / binsizes[ax]))
            binned_array = np.reshape(binned_array, tuple(new_shape))
            binned_array = np.sum(binned_array, axis=ax + 1)
            new_shape = list(binned_array.shape)
    return binned_array


# ar = np.asarray([1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9])
# ar.resize((5,9))
# print ('ar', ar)
# b = binning(ar, (2,2))
# print ('b',b)
# c = binning1(ar,(2,2))
# print ('c',c)


def get_centered(arr, center_shift):
    """
    This function finds a greatest value in the array, and puts it in a center of a new array. If center_shift is
    not zeros, the array will be shifted accordingly. The shifted elements are rolled into the other end of array.
    Parameters
    ----------
    arr : array
        the original array to be centered
    center_shift : list
        a list defining shift of the center
    Returns
    -------
    array : array
        the centered array
    """
    max_coordinates = list(np.unravel_index(np.argmax(arr), arr.shape))
    max_coordinates = np.add(max_coordinates, center_shift)
    shape = arr.shape
    centered = arr
    for i in range(len(max_coordinates)):
        centered = np.roll(centered, int(shape[i] / 2) - max_coordinates[i], i)

    return centered


def get_centered_both(arr, support):
    """
    This function finds a greatest value in the array, and puts it in a center of a new array. If center_shift is
    not zeros, the array will be shifted accordingly. The shifted elements are rolled into the other end of array.
    Parameters
    ----------
    arr : array
        the original array to be centered
    support : array
        the associated array shifted the same way centered array is
    Returns
    -------
    centered : array
        the centered array
    """
    max_coordinates = list(np.unravel_index(np.argmax(arr), arr.shape))
    shape = arr.shape
    centered = arr
    centered_supp = support
    for i in range(len(max_coordinates)):
        centered = np.roll(centered, int(shape[i] / 2) - max_coordinates[i], i)
        centered_supp = np.roll(centered_supp, int(shape[i] / 2) - max_coordinates[i], i)

    return centered, centered_supp


def get_zero_padded_centered(arr, new_shape):
    """
    This function pads the array with zeros to the new shape with the array in the center.
    Parameters
    ----------
    arr : array
        the original array to be padded and centered
    new_shape : tuple
        a list of new dimensions
    Returns
    -------
    array : array
        the zero padded centered array
    """
    shape = arr.shape
    pad = []
    c_vals = []
    for i in range(len(new_shape)):
        pad.append((0, new_shape[i] - shape[i]))
        c_vals.append((0.0, 0.0))
    arr = np.lib.pad(arr, (pad), 'constant', constant_values=c_vals)

    centered = arr
    for i in range(len(new_shape)):
        centered = np.roll(centered, int((new_shape[i] - shape[i] + 1) / 2), i)

    return centered


def adjust_dimensions(arr, pads):
    """
    This function adds to or subtracts from each dimension of the array elements defined by pad. If the pad is positive,
    the array is padded in this dimension. If the pad is negative, the array is cropped.
    The dimensions of the new array are supported by the opencl library.
    Parameters
    ----------
    arr : array
        the array to pad/crop
    pad : list
        list of three pad values, for each dimension
    Returns
    -------
    array : array
        the padded/cropped array
    """
    # logger = get_logger('adjust_dimensions')
    old_dims = arr.shape
    start = []
    stop = []
    for i in range(len(old_dims)):
        pad = pads[i]
        first = max(0, -pad[0])
        last = old_dims[i] - max(0, -pad[1])
        if first >= last:
            print ('the crop exceeds size, please change the crop and run again')
            return None
        else:
            start.append(first)
            stop.append(last)

    cropped = arr[ start[0]:stop[0], start[1]:stop[1], start[2]:stop[2] ]
    # logger.info('cutting from to ' + str(crop[0]) + ', ' + str(old_dims[0]-crop[1]) + ', ' + str(crop[2]) + ', ' \
    #             + str(old_dims[1]-crop[3]) + ', ' + str(crop[4]) + ', ' + str(old_dims[2]-crop[5]))
    dims = cropped.shape
    c_vals = []
    new_pad = []
    for i in range(len(dims)):
        pad = pads[i]
        # find a good dimension and find padding
        temp_dim = old_dims[i] + pad[0] + pad[1]
        new_dim = get_good_dim(temp_dim)
        added = new_dim - temp_dim
        # if the pad is positive
        pad_front = max(0, pad[0]) + int(added / 2)
        pad_end = new_dim - dims[i] - pad_front
        new_pad.append((pad_front, pad_end))
        c_vals.append((0.0, 0.0))
    adjusted = np.pad(cropped, new_pad, 'constant', constant_values=c_vals)

    # logger.info('pads ' + str(new_pad[0]) + ', ' + str(new_pad[1]) + ', ' + str(new_pad[2]) + ', ' + str(new_pad[3]) \
    #         + ', ' + str(new_pad[4]) + ', ' + str(new_pad[5]))
    # logger.info('old dim, new dim (' + str(dims[0]) + ',' + str(dims[1]) + ',' + str(dims[2]) + ') (' + str(arr.shape[0]) +\
    #     ',' + str(arr.shape[1]) + ',' + str(arr.shape[1]) + ')')

    return adjusted

# ar = np.zeros((256,256,90))
# pads = (-100,-100,0,0,0,0)
# ar = np.zeros((81,256,256))
# pads = (5,-7,-20,-30,4,-20)
# arr = adjust_dimensions(ar,pads)
# print (arr.shape)

def crop_center(arr, new_size):
    size = arr.shape
    cropped = arr
    for i in range(len(size)):
        crop_front = int((size[i] - new_size[i]) / 2)
        crop_end = crop_front + new_size[i]
        splitted = np.split(cropped, [crop_front, crop_end], axis=i)
        cropped = splitted[1]

    return cropped


# ar = np.zeros((81,256,256))
# new_size = (40, 200,100)
# arr = crop_center(ar,new_size)
# print (arr.shape)

def get_norm(arr):
    return sum(sum(sum(abs(arr) ** 2)))


def flip(m, axis):
    """
    Copied from numpy 1.12.0.
    """
    if not hasattr(m, 'ndim'):
        m = np.asarray(m)
    indexer = [slice(None)] * m.ndim
    try:
        indexer[axis] = slice(None, None, -1)
    except IndexError:
        raise ValueError("axis=%i is invalid for the %i-dimensional input array"
                         % (axis, m.ndim))
    return m[tuple(indexer)]


def gaussian(shape, sigmas, alpha=1):
    grid = np.full(shape, 1.0)
    for i in range(len(shape)):
        # prepare indexes for tile and transpose
        tile_shape = list(shape)
        tile_shape.pop(i)
        tile_shape.append(1)
        trans_shape = list(range(len(shape) - 1))
        trans_shape.insert(i, len(shape) - 1)

        multiplier = - 0.5 * alpha / pow(sigmas[i], 2)
        line = np.linspace(-(shape[i] - 1) / 2.0, (shape[i] - 1) / 2.0, shape[i])
        gi = np.tile(line, tile_shape)
        gi = np.transpose(gi, tuple(trans_shape))
        exponent = np.power(gi, 2) * multiplier
        gi = np.exp(exponent)
        grid = grid * gi

    grid_total = np.sum(grid)
    return grid / grid_total


def gauss_conv_fft(arr, sigmas):
    arr_sum = np.sum(abs(arr))
    arr_f = sf.ifftshift(sf.fftn(sf.ifftshift(arr)))
    shape = list(arr.shape)
    for i in range(len(sigmas)):
        sigmas[i] = shape[i] / 2.0 / np.pi / sigmas[i]
    convag = arr_f * gaussian(shape, sigmas)
    convag = np.fft.ifftshift(sf.ifftn(np.fft.ifftshift(convag)))
    convag = convag.real
    convag = np.clip(convag, 0, None)
    correction = arr_sum / np.sum(convag)
    convag *= correction
    return convag


def shrink_wrap(arr, threshold, sigma, type='gauss'):
    sigmas = [sigma] * len(arr.shape)
    if type == 'gauss':
        convag = gauss_conv_fft(abs(arr), sigmas)
        max_convag = np.amax(convag)
        convag = convag / max_convag
        support = np.where(convag >= threshold, 1, 0)
        return support
    else:
        return None


def read_results(read_dir):
    try:
        imagefile = os.path.join(read_dir, 'image.npy')
        image = np.load(imagefile)

        supportfile = os.path.join(read_dir, 'support.npy')
        support = np.load(supportfile)

        try:
            cohfile = os.path.join(read_dir, 'coherence.npy')
            coh = np.load(cohfile)
        except:
            coh = None
    except:
        pass

    return image, support, coh


def save_metrics(errs, dir, metrics=None):
    metric_file = os.path.join(dir, 'summary')
    if os.path.isfile(metric_file):
        os.remove(metric_file)
    with open(metric_file, 'a') as f:
        if metrics is not None:
            f.write('metric     result\n')
            for key in metrics:
                value = metrics[key]
                f.write(key + ' = ' + str(value) + '\n')
        f.write('\nerrors by iteration\n')
        for er in errs:
            f.write(str(er) + ' ')
    f.close()

def write_plot_errors(save_dir):
    plot_file = os.path.join(save_dir, 'plot_errors.py')
    f = open(plot_file, 'w+')
    f.write("#! /usr/bin/env python\n")
    f.write("import matplotlib.pyplot as plt\n")
    f.write("import numpy as np\n")
    f.write("import sys\n")
    f.write("import os\n")
    f.write("current_dir = sys.path[0]\n")
    f.write("errs = np.load(os.path.join(current_dir, 'errors.npy')).tolist()\n")
    f.write("errs.pop(0)\n")
    f.write("plt.plot(errs)\n")
    f.write("plt.ylabel('errors')\n")
    f.write("plt.show()")
    f.close()
    st = os.stat(plot_file)
    os.chmod(plot_file, st.st_mode | stat.S_IEXEC)


def save_results(image, support, coh, errs, reciprocal, flow, iter_array, save_dir, metrics=None):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    print("image shape", image.shape)

    image_file = os.path.join(save_dir, 'image')
    np.save(image_file, image)
    save_tif(np.abs(image), image_file+".tif")
    support_file = os.path.join(save_dir, 'support')
    np.save(support_file, support)
    save_tif(np.abs(support), support_file+".tif")
    errs_file = os.path.join(save_dir, 'errors')
    np.save(errs_file, errs)
    if not coh is None:
        coh_file = os.path.join(save_dir, 'coherence')
        np.save(coh_file, coh)
    reciprocal_file = os.path.join(save_dir, 'reciprocal')
    np.save(reciprocal_file, reciprocal)
    write_plot_errors(save_dir)

    graph_dir = os.path.join(save_dir, 'graph')
    if not os.path.exists(graph_dir):
        os.makedirs(graph_dir)
    flow_file = os.path.join(graph_dir, 'flow')
    np.save(flow_file, np.asarray(flow))
    iter_array_file = os.path.join(graph_dir, 'iter_array')
    np.save(iter_array_file, iter_array)

    if metrics is not None:
        save_metrics(errs, save_dir, metrics)
    else:
        save_metrics(errs, save_dir)


def save_multiple_results(samples, images, supports, cohs, errs, reciprocals, flows, iter_arrs, save_dir, metrics=None):
    """
    This function saves results of multiple reconstructions to directory tree in save_dir.
    Parameters
    ----------
    samples : int
        number of reconstruction sets results
    images : list
        list of numpy arrays containing reconstructed images
    supports : list
        list of numpy arrays containing support of reconstructed images
    cohs : list
        list of numpy arrays containing coherence of reconstructed images
    save_dir : str
        a directory to save the results
    Returns
    -------
    nothing
    """
    for i in range(samples):
        subdir = os.path.join(save_dir, str(i))
        if metrics is None:
            save_results(images[i], supports[i], cohs[i], np.asarray(errs[i]), reciprocals[i], flows[i], iter_arrs[i], subdir)
        else:
            save_results(images[i], supports[i], cohs[i], np.asarray(errs[i]), reciprocals[i], flows[i], iter_arrs[i], subdir, metrics[i])


def sub_pixel_shift(arr, row_shift, col_shift, z_shift):
    # arr is 3D
    buf2ft = sf.fftn(arr)
    shape = arr.shape
    Nr = np.fft.ifftshift(np.array(list(range(-int(np.floor(shape[0] / 2)), shape[0] - int(np.floor(shape[0] / 2))))))
    Nc = np.fft.ifftshift(np.array(list(range(-int(np.floor(shape[1] / 2)), shape[1] - int(np.floor(shape[1] / 2))))))
    Nz = np.fft.ifftshift(np.array(list(range(-int(np.floor(shape[2] / 2)), shape[2] - int(np.floor(shape[2] / 2))))))
    [Nc, Nr, Nz] = np.meshgrid(Nc, Nr, Nz)
    Greg = buf2ft * np.exp(1j * 2 * np.pi * (-row_shift * Nr / shape[0] - col_shift * Nc / shape[1] - z_shift * Nz / shape[2]))
    return sf.ifftn(Greg)


def arr_property(arr):
    arr1 = abs(arr)
    print ('norm', np.sum(pow(abs(arr),2)))
    max_coordinates = list(np.unravel_index(np.argmax(arr1), arr.shape))
    print ('max coords, value', max_coordinates, arr[max_coordinates[0], max_coordinates[1],max_coordinates[2]])


def get_gpu_load(mem_size, ids):
    gpus = GPUtil.getGPUs()
    total_avail = 0
    available_dir = {}
    for gpu in gpus:
        if gpu.id in ids:
            free_mem = gpu.memoryFree
            avail_runs = int(free_mem / mem_size)
            if avail_runs > 0:
                total_avail += avail_runs
                available_dir[gpu.id] = avail_runs
    available = []
    for id in ids:
        try:
            avail_runs = available_dir[id]
        except:
            avail_runs = 0
        available.append(avail_runs)
    return available


def get_gpu_distribution(runs, available):
    all_avail = reduce((lambda x,y: x+y), available)
    while runs < all_avail:
       # balance distribution
       for i in range(len(available)):
          if available[i] > 0:
             available[i] -= 1
             all_avail -= 1
             if all_avail == runs:
                break
    return available


#https://stackoverflow.com/questions/51503672/decorator-for-timeit-timeit-method/51503837#51503837
from functools import wraps
from time import time
def measure(func):
    @wraps(func)
    def _time_it(*args, **kwargs):
        start = int(round(time() * 1000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1000)) - start
            print(f"Total execution time: {end_ if end_ > 0 else 0} ms")
    return _time_it

