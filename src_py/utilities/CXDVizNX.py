import pylibconfig2 as cfg
import os
import traits.api as tr
from tvtk.api import tvtk
import numpy as np
import math as m
import utils as ut


class DispalyParams:
    """
    This class encapsulates parameters defining image display. The parameters are read from config file on
    construction
    """

    def __init__(self, config):
        """
        The constructor gets config file and fills out the class members.

        Parameters
        ----------
        conf : str
            configuration file name

        Returns
        -------
        none
        """
        if os.path.isfile(config):
            with open(config, 'r') as f:
                config_map = cfg.Config(f.read())
        deg2rad = np.pi / 180.0
        try:
            self.lamda = config_map.lamda
        except AttributeError:
            print ('lamda not defined')
        try:
            self.delta = config_map.delta * deg2rad
        except AttributeError:
            print ('delta not defined')
        try:
            self.gamma = config_map.gamma * deg2rad
        except AttributeError:
            print ('gamma not defined')
        try:
            self.arm = config_map.arm
        except AttributeError:
            print ('arm not defined')
        try:
            self.dth = config_map.dth
        except AttributeError:
            print ('dth not defined')
        try:
            pixel = config_map.pixel
            self.dpx = pixel[0] / self.arm
            self.dpy = pixel[1] / self.arm
        except AttributeError:
            print ('pixel not defined')
        try:
            self.save_two_files = config_map.save_two_files
        except AttributeError:
            print ('save_two_files not defined')
        try:
            self.crop = config_map.crop
        except AttributeError:
            self.crop = None
            print ('crop not defined')

class CXDViz(tr.HasTraits):
    coords = tr.Array()
    arr = tr.Array()

    cropx = tr.Int()
    cropy = tr.Int()
    cropz = tr.Int()

    def __init__(self):
        self.imd = tvtk.ImageData()
        self.sg = tvtk.StructuredGrid()
        pass

    def set_geometry(self, params, shape):
        lam = params.lamda
        tth = params.delta
        gam = params.gamma
        dpx = params.dpx
        dpy = params.dpy
        dth = params.dth
        dx = 1.0 / shape[0]
        dy = 1.0 / shape[1]
        dz = 1.0 / shape[2]
        dQdpx = np.zeros(3)
        dQdpy = np.zeros(3)
        dQdth = np.zeros(3)
        Astar = np.zeros(3)
        Bstar = np.zeros(3)
        Cstar = np.zeros(3)

        dQdpx[0] = -m.cos(tth) * m.cos(gam)
        dQdpx[1] = 0.0
        dQdpx[2] = +m.sin(tth) * m.cos(gam)

        dQdpy[0] = m.sin(tth) * m.sin(gam)
        dQdpy[1] = -m.cos(gam)
        dQdpy[2] = m.cos(tth) * m.sin(gam)

        dQdth[0] = -m.cos(tth) * m.cos(gam) + 1.0
        dQdth[1] = 0.0
        dQdth[2] = m.sin(tth) * m.cos(gam)

        Astar[0] = 2 * m.pi / lam * dpx * dQdpx[0]
        Astar[1] = 2 * m.pi / lam * dpx * dQdpx[1]
        Astar[2] = 2 * m.pi / lam * dpx * dQdpx[2]

        Bstar[0] = (2 * m.pi / lam) * dpy * dQdpy[0]
        Bstar[1] = (2 * m.pi / lam) * dpy * dQdpy[1]
        Bstar[2] = (2 * m.pi / lam) * dpy * dQdpy[2]

        Cstar[0] = (2 * m.pi / lam) * dth * dQdth[0]
        Cstar[1] = (2 * m.pi / lam) * dth * dQdth[1]
        Cstar[2] = (2 * m.pi / lam) * dth * dQdth[2]

        denom = np.dot(Astar, np.cross(Bstar, Cstar))
        A = 2 * m.pi * np.cross(Bstar, Cstar) / denom
        B = 2 * m.pi * np.cross(Cstar, Astar) / denom
        C = 2 * m.pi * np.cross(Astar, Bstar) / denom

        self.T = np.zeros(9)
        self.T.shape = (3, 3)
        space = 'direct'
        if space == 'recip':
            self.T[:, 0] = Astar
            self.T[:, 1] = Bstar
            self.T[:, 2] = Cstar
            self.dx = 1.0
            self.dy = 1.0
            self.dz = 1.0
        elif space == 'direct':
            self.T = np.array((A, B, C))
            self.dx = dx
            self.dy = dy
            self.dz = dz
        else:
            pass

    def update_coords(self):
        dims = list(self.arr[self.cropobj].shape)

        r = np.mgrid[(dims[0] - 1) * self.dx:-self.dx:-self.dx, \
            0:dims[1] * self.dy:self.dy, 0:dims[2] * self.dz:self.dz]

        r.shape = 3, dims[0] * dims[1] * dims[2]
        r = r.transpose()

        print r.shape
        print self.T.shape

        self.coords = np.dot(r, self.T)

    def set_array(self, array, logentry=None):
        self.arr = array
        if len(self.arr.shape) < 3:
            newdims = list(self.arr.shape)
            for i in range(3 - len(newdims)):
                newdims.append(1)
            self.arr.shape = tuple(newdims)

    def set_crop(self, cropx, cropy, cropz):
        dims = list(self.arr.shape)
        if len(dims) == 2:
            dims.append(1)

        if dims[0] > cropx and cropx > 0:
            self.cropx = cropx
        else:
            self.cropx = dims[0]

        if dims[1] > cropy and cropy > 0:
            self.cropy = cropy
        else:
            self.cropy = dims[1]

        if dims[2] > cropz and cropz > 0:
            self.cropz = cropz
        else:
            self.cropz = dims[2]

        start1 = dims[0] / 2 - self.cropx / 2
        end1 = dims[0] / 2 + self.cropx / 2
        if start1 == end1:
            end1 = end1 + 1
        start2 = dims[1] / 2 - self.cropy / 2
        end2 = dims[1] / 2 + self.cropy / 2
        if start2 == end2:
            end2 = end2 + 1
        start3 = dims[2] / 2 - self.cropz / 2
        end3 = dims[2] / 2 + self.cropz / 2
        if start3 == end3:
            end3 = end3 + 1

        self.cropobj = (slice(start1, end1, None), slice(start2, end2, None),
                        slice(start3, end3, None))

    def get_structured_grid(self, **args):
        self.update_coords()
        dims = list(self.arr[self.cropobj].shape)
        self.sg.points = self.coords
        if args.has_key("mode"):
            if args["mode"] == "Phase":
                arr1 = self.arr[self.cropobj].ravel()
                arr = (np.arctan2(arr1.imag, arr1.real))
            else:
                arr = np.abs(self.arr[self.cropobj].ravel())
        else:
            arr = self.arr[self.cropobj].ravel()
        if (arr.dtype == np.complex128 or arr.dtype == np.complex64):
            self.sg.point_data.scalars = np.abs(arr)
            self.sg.point_data.scalars.name = "Amp"
            ph = tvtk.DoubleArray()
            ph.from_array(np.arctan2(arr.imag, arr.real))
            ph.name = "Phase"
            self.sg.point_data.add_array(ph)
        else:
            self.sg.point_data.scalars = arr
        self.sg.dimensions = (dims[2], dims[1], dims[0])
        self.sg.extent = 0, dims[2] - 1, 0, dims[1] - 1, 0, dims[0] - 1
        return self.sg

    def get_image_data(self, **args):
        self.set_crop(self.cropx, self.cropy, self.cropz)
        dims = list(self.arr[self.cropobj].shape)
        if len(dims) == 2:
            dims.append(1)
        self.imd.dimensions = tuple(dims)
        self.imd.extent = 0, dims[2] - 1, 0, dims[1] - 1, 0, dims[0] - 1
        self.imd.point_data.scalars = self.arr[self.cropobj].ravel()
        return self.imd

    def write_structured_grid(self, filename, **args):
        print 'in WriteStructuredGrid'
        sgwriter = tvtk.StructuredGridWriter()
        sgwriter.file_type = 'binary'
        if filename.endswith(".vtk"):
            sgwriter.file_name = filename
        else:
            sgwriter.file_name = filename + '.vtk'

        sgwriter.set_input_data(self.get_structured_grid())
        print sgwriter.file_name
        sgwriter.write()

def shift(arr, s0, s1, s2):
    shifted = np.roll(arr, s0, 0)
    shifted = np.roll(shifted, s1, 1)
    return np.roll(shifted, s2, 2)


def sub_pixel_shift(arr, shift_ind):
    buf = np.fft.fftn(arr)
    dims = buf.shape
    x = np.fft.ifftshift(np.arange(-(dims[0] / 2), dims[0] / 2))
    y = np.fft.ifftshift(np.arange(-(dims[1] / 2), dims[1] / 2))
    z = np.fft.ifftshift(np.arange(-(dims[2] / 2), dims[2] / 2))
    gx, gy, gz = np.meshgrid(x, y, z)

    grid_shift = - gx * shift_ind[0] / dims[0] - gy * shift_ind[1] / dims[1] - gy * shift_ind[2] / dims[2]
    g = buf * np.exp(1j * 2 * np.pi * grid_shift)
    return np.fft.ifftn(g)


def center_of_mass(arr):
    tot = np.sum(arr)
    dims = arr.shape
    xyz = []
    griddims = []
    for d in dims:
        griddims.append(slice(0, d))
    grid = np.ogrid[griddims]
    for g in grid:
        xyz.append(np.sum(arr * g) / tot)
    com = np.asarray(xyz)
    com = np.ma.round(com).astype(np.int)
    return list(com)


def remove_ramp(arr):
    # pad zeros around arr, to the size of 3 times (ups = 3) of arr size
    padded = ut.zero_pad(arr, arr.shape)
    data = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(padded)))
    com = center_of_mass(np.power(np.absolute(data), 2)) - .5
    sub_pixel_shifted = sub_pixel_shift(data, (com[1], com[0], com[2]))
    ramp_removed_padded = np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(sub_pixel_shifted)))
    ramp_removed = ut.crop_center(ramp_removed_padded, arr.shape)

    return ramp_removed


def center(image, support):
    dims = image.shape
    com = center_of_mass(np.absolute(image) * support)
    # place center of mass image*support in the center
    image = shift(image, dims[0] / 2 - com[0], dims[1] / 2 - com[1], dims[2] / 2 - com[2])
    support = shift(support, dims[0] / 2 - com[0], dims[1] / 2 - com[1], dims[2] / 2 - com[2])

    # set com phase to zero, use as a reference
    phi0 = m.atan2(image.imag[dims[0]/2, dims[1]/2, dims[2]/2], image.real[dims[0]/2, dims[1]/2, dims[2]/2])
    print 'phi0', phi0
    image = image * np.exp(-1j * phi0)
    return image, support


def save_CX(conf, image, support, filename):
    image, support = center(image, support)
    #    image = remove_ramp(image)
    params = DispalyParams(conf)
    viz = CXDViz()
    viz.set_array(image)
    viz.set_geometry(params, image.shape)
    if params.crop is None:
        crop = image.shape
    else:
        crop = params.crop
    viz.set_crop(crop[0], crop[1], crop[2])  # save image
    viz.write_structured_grid(filename + '_img')
    viz.set_array(support)
    viz.write_structured_grid(filename + '_support')

