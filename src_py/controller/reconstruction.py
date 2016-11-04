import numpy as np
import src_py.utilities.utils as ut
import pylibconfig2 as cfg
import os
import scipy.fftpack as sf

def read_config(config):
    if os.path.isfile(config):
        with open(config, 'r') as f:
            config_map = cfg.Config(f.read())
            return config_map;
    else:
        return None

def prepare_data(config_map, data):
    # zero out the noise
    data = np.where(data < config_map.amp_threshold, 0, data)

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

    # shift data
    data=sf.fftshift(data)

    return data
    

def do_reconstruction(proc, data, conf):
    if proc == 'cpu':
        from src_py.cyth.bridge_cpu import *
    elif proc == 'opencl':
        from src_py.cyth.bridge_opencl import *
    elif proc == 'cuda':
        from src_py.cyth.bridge_cuda import *
    else:
        print 'unrecognized processor, only "cpu", "opencl", and "cuda" are valid'
        return None, None
    
    dims = data.shape
    fast_module = PyBridge()
    data_l = data.flatten().tolist()
    fast_module.start_calc(data_l, dims, conf)
    er = fast_module.get_errors()
    image_r = np.asarray(fast_module.get_image_r())
    image_i = np.asarray(fast_module.get_image_i())
    image = image_r + 1j*image_i
    np.reshape(image, dims)
    return image, er
    
def reconstruction(proc, filename, conf):
    data = ut.get_array_from_tif(filename)
    if len(data.shape) > 3:
        print "this program supports 3d images only"
        return None, None

    config_map = read_config(conf)
    if config_map is None:
        print "can't read configuration file"
        return None, None

    data = prepare_data(config_map, data)

    return do_reconstruction(proc, data, conf)
    

