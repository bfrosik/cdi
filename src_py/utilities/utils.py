import tifffile as tf

def get_array_from_tif(filename):
    return tf.imread(filename)