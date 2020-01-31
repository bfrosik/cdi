import pylibconfig2 as cfg
import numpy as np
import copy
import scipy.fftpack as sf
import os
import glob
import tifffile as tif
import reccdi.src_py.beamlines.aps_34id.spec as spec
import reccdi.src_py.utilities.utils as ut


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
        data_dir = map.data_dir.strip()
    except:
        print ('please provide data_dir')
        return

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
        dark = dark_full[slice(det_area1[0], det_area1[0] + det_area1[1]), slice(det_area2[0], det_area2[0] + det_area2[1])]
    else:
        dark = None

    if whitefile is not None:
        # find the whitefield array
        white_full = tif.imread(whitefile).astype(float)
        # crop the corresponding quad or use the whole array, depending on what info was parsed from spec file
        white = white_full[slice(det_area1[0], det_area1[0] + det_area1[1]), slice(det_area2[0], det_area2[0] + det_area2[1])]
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
    slice0 = get_normalized_slice(files[n], dark, white)
    shape = (slice0.shape[0], slice0.shape[1], len(files))
    arr = np.zeros(shape, dtype=slice0.dtype)
    arr[:,:,0] = slice0

    #for i in range (1, len(files)):
    for file in files[1:]:
        n = n + 1
        slice = get_normalized_slice(file, dark, white)
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

    shifted_arr = sf.ifftn(ftarr)
    return shifted_arr


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
    # The det_area parameters hold the [beginning of image, size] in both dimensions.
    # the beginning of image is relative to the full sensor image 512 x 512.
    # if the full sensor was used for the image (i.e. the data size is 512x512)
    # or if the image overleaps multiple quads,
    # the quadrants need to be shifted
    # check whether the image was taken with a single quad, then no shift is needed
    if (det_area1[0] + det_area1[1] <= 256) and (det_area2[0] + det_area2[1] <= 256):
       return arr
    else:
        b = np.zeros((517,516,arr.shape[2]),float)
        tmp = np.zeros((512,512,arr.shape[2]),float)
        tmp[det_area1[0]:det_area1[0]+det_area1[1],det_area2[0]:det_area2[0]+det_area2[1],:] = arr
        b[:256,:256,:] = tmp[:256,:256,:] #Quad top left unchanged
        b[:256,260:,:] = tmp[:256,256:,:] #Quad top right moved 4 right
        b[261:,:256,:] = tmp[256:,:256,:] #Quad bot left moved 6 down
        b[261:,260:,:] = tmp[256:,256:,:] #Quad bot right

        return b[det_area1[0]:det_area1[0]+det_area1[1],det_area2[0]:det_area2[0]+det_area2[1],:]


def prep_data(experiment_dir, scans, map, det_area1, det_area2, *args):
    if scans is None:
        print ('scan info not provided')
        return

    # build sub-directories map
    if len(scans) == 1:
        scans.append(scans[0])
    dirs = get_dir_list(scans, map)
    if len(dirs) == 0:
        print ('no data directories found')
        return
    else:
        if not os.path.exists(experiment_dir):
            os.makedirs(experiment_dir)

    try:
        whitefile = (map.whitefile).strip()
    except:
        whitefile = None

    try:
        darkfile = (map.darkfile).strip()
    except:
        darkfile = None

    dark, white = get_dark_white(darkfile, whitefile, det_area1, det_area2)

    if len(dirs) == 0:
        print ('there are no data directories for given scans')
        return

    if len(dirs) == 1:
        arr = read_scan(dirs[0], dark, white)
        arr = fit(arr, det_area1, det_area2)
    else:
        # make the first part a reference
        part = read_scan(dirs[0], dark, white)
        part = fit(part, det_area1, det_area2)
        slice_sum = np.abs(copy.deepcopy(part))
        refpart = sf.fftn(part)
        for i in range (1, len(dirs)):
            #this will load scans from each directory into an array part
            part = read_scan(dirs[i], dark, white)
            part = fit(part, det_area1, det_area2)
            # add the arrays together
            part_f = sf.fftn(part)
            slice_sum = combine_part(part_f, slice_sum, refpart, part)
        arr = np.abs(slice_sum).astype(np.int32)

    #arr = fit(arr, det_area1, det_area2)

    #create directory to save prepared data ,<experiment_dir>/prep
    prep_data_dir = os.path.join(experiment_dir, 'prep')
    if not os.path.exists(prep_data_dir):
        os.makedirs(prep_data_dir)
    data_file = os.path.join(prep_data_dir, 'prep_data.tif')

    ut.save_tif(arr, data_file)
    print ('done with prep, shape:', arr.shape)


def prepare(experiment_dir, scans, conf_file, *args):
    try:
        with open(conf_file, 'r') as f:
            config_map = cfg.Config(f.read())
    except Exception as e:
        print('Please check the configuration file ' + conf_file + '. Cannot parse ' + str(e))
        return

    scan_end = scans[len(scans)-1]
    try:
        specfile = config_map.specfile.strip()
        # parse det1 and det2 parameters from spec
        det_area1, det_area2 = spec.get_det_from_spec(specfile, scan_end)
    except:
        try:
            det_quad = config_map.det_quad
            if det_quad == 0:
                det_area1 = (0, 512)
                det_area2 = (0, 512)
            elif det_quad == 1:
                det_area1 = (0, 256)
                det_area2 = (0, 256)
            elif det_quad == 2:
                det_area1 = (0, 256)
                det_area2 = (256, 512)
            elif det_quad == 3:
                det_area1 = (256, 512)
                det_area2 = (0, 256)
            elif det_quad == 4:
                det_area1 = (256, 512)
                det_area2 = (256, 512)
            else:
                print('the detector quad can be configured as digt from 0 to 4')
                return
        except Exception as e:
            print('spec file or scan is not configured, and detector quad is not configured')
            return

    try:
        separate_scans = config_map.separate_scans
    except:
        separate_scans = False

    # data prep
    # if separate scans, prepare data in each scan separately in subdirectory
    if separate_scans and len(scans) > 1:
        for scan in range (scans[0], scans[1]+1):
            single_scan = [scan]
            scan_exp_dir = os.path.join(experiment_dir, 'scan_' + str(scan))
            prep_data(scan_exp_dir, single_scan, config_map, det_area1, det_area2, args)
    else:
        prep_data(experiment_dir, scans, config_map, det_area1, det_area2, args)


