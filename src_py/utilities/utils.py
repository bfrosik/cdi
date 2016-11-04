import tifffile as tf
import numpy as np

def get_array_from_tif(filename):
    return tf.imread(filename)


def get_opencl_dim(dim, step):
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


