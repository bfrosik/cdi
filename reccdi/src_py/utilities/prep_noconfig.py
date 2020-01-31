import numpy as np
import copy
import scipy.fftpack as sf
import os
import glob
import tifffile as tif
#import reccdi.src_py.utilities.spec as spec
#import reccdi.src_py.utilities.utils as ut


def get_dir_list(scans, map):
    """
    Returns list of sub-directories in data_dir with names matching range of scans
    It will exclude scans within exclude_scans list if provided, and directories with fewer files than
    min_files, if provided
    :param scans:
    :param map:
    :return:
    """
    try:
        min_files = map.min_files
    except:
        min_files = 0
    try:
        exclude_scans = map.exclude_scans
    except:
        exclude_scans = []
    try:
        data_dir = map.data_dir
    except:
        print ('please provide data_dir')

    dirs = []
    for name in os.listdir(data_dir):
        subdir = os.path.join(data_dir, name)
        if os.path.isdir(subdir):
            # exclude directories with fewer tif files than min_files
            if len(glob.glob1(subdir, "*.tif")) < min_files and len(glob.glob1(subdir, "*.tiff")) < min_files:
                continue
            try:
                index = int(name[-4:])
                if index >= scans[0] and index <= scans[1] and not index in exclude_scans:
                    dirs.append(subdir)
            except:
                continue
    return dirs


def get_dark_white(darkfile, whitefile, det_area1, det_area2):
    if darkfile is not None:
        # find the darkfield array
        dark_full = tif.imread(darkfile).astype(float)
        # crop the corresponding quad or use the whole array, depending on what info was parsed from spec file
        dark = dark_full[slice(det_area1[0], det_area1[1]), slice(det_area2[0], det_area2[1])]
    else:
        dark = None

    if whitefile is not None:
        # find the whitefield array
        white_full = tif.imread(whitefile).astype(float)
        # crop the corresponding quad or use the whole array, depending on what info was parsed from spec file
        white = white_full[slice(det_area1[0], det_area1[1]), slice(det_area2[0], det_area2[1])]
        # set the bad pixels to some large value
        white = np.where(white<5000, 1e20, white) #Some large value
    else:
        white = None

    return dark, white


def get_normalized_slice(file, dark, white):
    # file is a tuple of slice and either background slice or None
    slice = tif.TiffFile(file[0]).asarray()
    if file[1] is not None:
        slice = slice - tif.TiffFile(file[1]).asarray()
    if dark is not None:
        slice = np.where(dark > 5, 0, slice) #Ignore cosmic rays
    # here would be code for correction for dead time
    if white is not None:
        slice = slice/white
        slice *= 1e5 #Some medium value
    slice = np.where(np.isnan(slice), 0, slice)
    return slice


def read_scan(dir, dark, white):
    files = []
    files_dir = {}
    for file in os.listdir(dir):
        if file.endswith('tif') or file.endswith('tiff'):
            temp = file.split('.')
            #it's assumed that the files end with four digits and 'tif' or 'tiff' extension
            key = temp[0][-4:]
            files_dir[key] = file

    ordered_keys = sorted(list(files_dir.keys()))

    for key in ordered_keys:
        file = files_dir[key]
        file = os.path.join(dir, file)
        bg_file = file.replace('.tif', '_bg.tif')
        if not os.path.isfile(bg_file):
            bg_file = None

        files.append((file, bg_file))

    # look at slice0 to find out shape
    n = 0
    slice0 = get_normalized_slice(files[n], dark, white).transpose()
    shape = (slice0.shape[0], slice0.shape[1], len(files))
    arr = np.zeros(shape, dtype=slice0.dtype)
    arr[:,:,0] = slice0
    print("slice shape",slice0.shape)

    #for i in range (1, len(files)):
    for file in files[1:]:
        n = n + 1
        slice = get_normalized_slice(file, dark, white).transpose()
        arr[:,:,n] = slice
    return arr


def shift(arr, shifty):
    # pass the FT of the fftshifted array you want to shift
    # you get back the actual array, not the FT.
    dims = arr.shape
    # scipy does normalize ffts!
    ftarr = sf.fftn(arr)
    r=[]
    for d in dims:
        r.append(slice(int(np.ceil(-d/2.)), int(np.ceil(d/2.)), None))
    idxgrid = np.mgrid[r]
    for d in range(len(dims)):
        ftarr *= np.exp(-1j*2*np.pi*shifty[d]*sf.fftshift(idxgrid[d])/float(dims[d]))

    shiftedarr = sf.ifftn(ftarr)
    return shiftedarr


def combine_part(part_f, slice_sum, refpart, part):
    # get cross correlation and pixel shift
    cross_correlation = sf.ifftn(refpart*np.conj(part_f))
    corelated = np.array(cross_correlation.shape)
    amp = np.abs(cross_correlation)
    intshift = np.unravel_index(amp.argmax(), corelated)
    shifted = np.array(intshift)
    pixelshift = np.where(shifted>=corelated/2, shifted-corelated, shifted)
    return slice_sum + shift(part, pixelshift)


def fit(arr, det_area1, det_area2):
    # if the full sensor was used for the image (i.e. the data size is 512x512)
    # the quadrants need to be shifted
    if det_area1[0] == 0 and det_area1[1] == 512 and det_area1[0] == 0 and det_area2[1] == 512:
        b = np.zeros((arr.shape[0],517,516),float)
        b[:,:256,:256] = arr[:,:256,:256] #Quad top left unchanged
        b[:,:256,260:] = arr[:,:256,256:] #Quad top right moved 4 right
        b[:,261:,:256] = arr[:,256:,:256] #Quad bot left moved 6 down
        b[:,261:,260:] = arr[:,256:,256:] #Quad bot right
    else:
        b = arr
    return b


def prep_data(experiment_dir, scans, map, det_area1, det_area2, *args):
    if scans is None:
        print ('scan info not provided')
        return

    # build sub-directories map
    if len(scans) == 1:
        scans.append(scans[0])
    dirs = get_dir_list(scans, map)

    try:
        whitefile = map.whitefile
    except:
        whitefile = None

    try:
        darkfile = map.darkfile
    except:
        darkfile = None

    dark, white = get_dark_white(darkfile, whitefile, det_area1, det_area2)

    if len(dirs) == 0:
        print ('there are no data directories for given scans')
        return

    if len(dirs) == 1:
        arr = read_scan(dirs[0], dark, white)
    else:
        # make the first part a reference
        part = read_scan(dirs[0], dark, white)
        slice_sum = np.abs(copy.deepcopy(part))
        refpart = sf.fftn(part)
        for i in range (1, len(dirs)):
            #this will load scans from each directory into an array part
            part = read_scan(dirs[i], dark, white)
            # add the arrays together
            part_f = sf.fftn(part)
            slice_sum = combine_part(part_f, slice_sum, refpart, part)
        arr = np.abs(slice_sum).astype(np.int32)

    arr = fit(arr, det_area1, det_area2)

    #create directory to save prepared data ,<experiment_dir>/prep
    prep_data_dir = os.path.join(experiment_dir, 'prep')
    if not os.path.exists(prep_data_dir):
        os.makedirs(prep_data_dir)
    data_file = os.path.join(prep_data_dir, 'prep_data.tif')

    ut.save_tif(arr, data_file)
    print ('done with prep, shape:', arr.shape)

