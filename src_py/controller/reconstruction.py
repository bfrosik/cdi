import numpy as np
import src_py.utilities.utils as ut

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
    
def get_dim(dim):
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
        new_dim -= 1
    return new_dim
    
def reconstruction(proc, filename, conf):
    img = ut.get_array_from_tif(filename)

    data = img[::-1,:,:]

    dim0 = get_dim(data.shape[0])
    dim1 = get_dim(data.shape[1])
    dim2 = get_dim(data.shape[2])
    data_corrected = data[0:dim0, 0:dim1, 0:dim2]

    return do_reconstruction(proc, data_corrected, conf)
    

