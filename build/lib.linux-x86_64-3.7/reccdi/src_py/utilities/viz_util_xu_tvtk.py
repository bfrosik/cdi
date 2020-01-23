# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
import numpy as np
import scipy.ndimage as ndi
import math as m
import pyevtk.hl as vtk
from tvtk.api import tvtk
import xrayutilities.experiment as xuexp
import reccdi.src_py.utilities.utils as ut
from reccdi.src_py.utilities.utils import measure
import reccdi.src_py.utilities.spec as sput

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'

class DispalyParams:
    """
    This class encapsulates parameters defining image display. The parameters are
read from config file on
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
        deg2rad = np.pi / 180.0
        try:
            specfile = config['specfile']
            last_scan = config['last_scan']
            self.lam, delta, gamma, dth, arm, pixel,energy = sput.parse_spec(specfile,
last_scan)
            self.delta = delta * deg2rad
            self.gamma = gamma * deg2rad
            self.dth = dth * deg2rad
            self.arm = arm / 1000
            self.energy = energy
            pixel = pixel[1:-1]
            pixel = pixel.split(',')
            pixel[0], pixel[1] = float(pixel[0]), float(pixel[1])
        except Exception as e:
            pass
        # override the parsed parameters with entries in config file
        try:
            self.energy = config['energy']
            self.lam = 12.398 / energy / 10
        except AttributeError:
            pass
        try:
            self.delta = config['delta'] * deg2rad
        except AttributeError:
            pass
        try:
            self.gamma = config['gamma'] * deg2rad
        except AttributeError:
            pass
        try:
            self.dth = config['dth'] * deg2rad
        except AttributeError:
            pass
        try:
            self.arm = config['arm'] / 1000
        except AttributeError:
            pass
        try:
            pixel = config['pixel']
        except AttributeError:
            pass

        try:
            self.binning = []
            binning = config['binning']
            for i in range(len(binning)):
                self.binning.append(binning[i])
            for _ in range(3 - len(self.binning)):
                self.binning.append(1)
        except AttributeError:
            self.binning = [1,1,1]
        self.px = pixel[0] * self.binning[0]
        self.py = pixel[1] * self.binning[1]
        self.dpx = pixel[0] * self.binning[0] / self.arm / self.binning[2]
        self.dpy = pixel[1] * self.binning[1] / self.arm / self.binning[2]
        try:
            self.crop = []
            crop = config['crop']
            for i in range(len(crop)):
                self.crop.append(crop[i])
            for _ in range(3 - len(self.crop)):
                self.crop.append(1.0)
            crop[0], crop[1] = crop[1], crop[0]
        except AttributeError:
            self.crop = None






class CXDViz():

  cropx = 0.5
  cropy = 0.5
  cropz = 0.5
  dir_arrs={}
  recip_arrs={}
 
  def __init__(self):
    self.imd = tvtk.ImageData()
    self.sg = tvtk.StructuredGrid()
    pass


  #def set_geometry(self, lam, delta, gamma, dpx, dpy, dth):
  @measure
  def set_geometry(self, params, shape):
    self.params = params
    lam = params.lam
    tth = params.delta
    gam = params.gamma
    px = params.px
    py = params.py
    dpx = params.dpx
    dpy = params.dpy
    dth = params.dth
    energy = params.energy
    dQdpx = np.zeros(3)
    dQdpy = np.zeros(3)
    dQdth = np.zeros(3)
    Astar = np.zeros(3)
    Bstar = np.zeros(3)
    Cstar = np.zeros(3)
   
    print("running the xrayutilities version and tvtk")
    self.qc=xuexp.QConversion(['y+','z-','x-'], ['y+','x-'],(0,0,1),en=energy*1000) 
    self.qc.init_area('x+','y-', shape[0],shape[1], 2,2, distance=params.arm, pwidth1=px, pwidth2=py)                                              

    q1=np.array(self.qc.area(0.0,0,0,tth,gam,deg=False))
    q2=np.array(self.qc.area(dth,0,0,tth,gam,deg=False))
    Astar=q1[:,1,0]-q1[:,0,0]
    Bstar=q1[:,0,1]-q1[:,0,0]
    Cstar=(q2-q1)[:,0,0]

    denom = np.dot(Astar, np.cross(Bstar, Cstar))
    A = 2 * m.pi * np.cross(Bstar, Cstar) / denom
    B = 2 * m.pi * np.cross(Cstar, Astar) / denom
    C = 2 * m.pi * np.cross(Astar, Bstar) / denom

    self.Trecip = np.zeros(9)
    self.Trecip.shape = (3, 3)
    self.Trecip[:, 0] = Astar
    self.Trecip[:, 1] = Bstar
    self.Trecip[:, 2] = Cstar
#    self.Trecip[:, 0] = [2,0,1]
#    self.Trecip[:, 1] = [0,1,0]
#    self.Trecip[:, 2] = [0,0,1]
    print("Recip")
    print(Astar,Bstar,Cstar)
    print(self.Trecip)

    self.Tdir = np.zeros(9)
    self.Tdir.shape = (3, 3)
    self.Tdir = np.array((A, B, C)).transpose()
    print("Direct")
    print(A,B,C)
    print(self.Tdir)

    self.dirspace_uptodate=0
    self.recipspace_uptodate=0
    return dQdpx, dQdpy, dQdth

  def update_dirspace(self, shape):
    print("Updating dirspace coords")
    dims = list(shape)
    self.dxdir = 1.0 / shape[0]
    self.dydir = 1.0 / shape[1]
    self.dzdir = 1.0 / shape[2]

    r = np.mgrid[
        0:dims[0] * self.dxdir:self.dxdir, \
        0:dims[1] * self.dydir:self.dydir,\
        0:dims[2] * self.dzdir:self.dzdir]
#    r = np.mgrid[
#        0:dims[0]*self.dxdir:self.dxdir, \
#        (dims[1]-1)*self.dydir:-self.dydir:-self.dydir,\
#        0:dims[2]*self.dzdir:self.dzdir]

    origshape=r.shape
    r.shape = 3, dims[0] * dims[1] * dims[2]
    #r = r.transpose()
  
    self.dir_coords = np.dot(self.Tdir, r).transpose()
 
#    self.dir_coords = self.dir_coords.transpose()
#    self.dir_coords.shape=origshape
    print("dir shape", self.dir_coords.shape)
    self.dirspace_uptodate=1

  def update_recipspace(self, shape): 
    dims = list(shape)
    q = np.mgrid[ 0:dims[0], 0:dims[1], 0:dims[2]]

    origshape=q.shape
    q.shape = 3, dims[0] * dims[1] * dims[2]

    self.recip_coords = np.dot(self.Trecip, q)
    self.recip_coords.shape=origshape
    self.recipspace_uptodate=1   

  def clear_direct_arrays(self):
    self.dir_arrs.clear()
  def clear_recip_arrays(self):
    self.recip_arrs.clear()

  @measure
  def add_array(self, array, name, space='direct', logentry=None):

    #Need to add something to ensure arrays are all the same dimension.
    #Need to add crop of viz output arrays
    if len(array.shape) < 3:
        newdims = list(array.shape)
        for i in range(3 - len(newdims)):
            newdims.append(1)
        array.shape = tuple(newdims)
    print("adding array of shape ", array.shape)
    if space=='direct':
      self.dir_arrs[name]=array
      if (not self.dirspace_uptodate):
        self.update_dirspace(array.shape)
    elif space=='recip':
      self.recip_arrs[name]=array
      if (not self.recipspace_uptodate):
        self.update_recipspace(array.shape)
    else:
      return

  def get_ds_structured_grid(self, **args):
    arr0=self.dir_arrs[list(self.dir_arrs.keys())[0]]
    dims = list(arr0.shape)
    self.sg.points = self.dir_coords
    for a in self.dir_arrs.keys():
      arr=tvtk.DoubleArray()
      arr.from_array(self.dir_arrs[a].ravel())
      arr.name=a
      self.sg.point_data.add_array(arr)
      
    self.sg.dimensions = (dims[2], dims[1], dims[0])
    self.sg.extent = 0, dims[2] - 1, 0, dims[1] - 1, 0, dims[0] - 1
    return self.sg

  def write_directspace(self, filename, **args):
    sgwriter = tvtk.XMLStructuredGridWriter()
    #sgwriter.file_type = 'binary'
    if filename.endswith(".vtk"):
        sgwriter.file_name = filename
    else:
        sgwriter.file_name = filename + '.vts'
    sgwriter.set_input_data(self.get_ds_structured_grid())
    sgwriter.write()
    print ('saved file', filename)

  @measure
  def write_directspace_pyevtk(self, filename, **args):
    print(self.dir_arrs.keys())
    vtk.gridToVTK(filename, self.dir_coords[0,:,:,:].copy(), \
                  self.dir_coords[1,:,:,:].copy(), \
                  self.dir_coords[2,:,:,:].copy(), pointData=self.dir_arrs)
    vtk.imageToVTK(filename, pointData=self.dir_arrs)

  def write_recipspace_pyevtk(self, filename, **args):
    vtk.gridToVTK(filename, self.recip_coords[0,:,:,:].copy(), \
                  self.recip_coords[1,:,:,:].copy(), \
                  self.recip_coords[2,:,:,:].copy(), pointData=self.recip_arrs)
    vtk.imageToVTK(filename, pointData=self.recip_arrs)

def shift(arr, s0, s1, s2):
    shifted = np.roll(arr, s0, axis=0)
    shifted = np.roll(shifted, s1, axis=1)
    return np.roll(shifted, s2, axis=2)


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

@measure
def remove_ramp(arr, ups=1):
    new_shape = list(arr.shape)
    # pad zeros around arr, to the size of 3 times (ups = 3) of arr size
    for i in range(len(new_shape)):
        new_shape[i] = ups * new_shape[i]
    padded = ut.get_zero_padded_centered(arr, new_shape)
    padded_f = np.fft.fftshift(np.fft.fftn(np.fft.ifftshift(padded)))
    com = ndi.center_of_mass(np.power(np.abs(padded_f), 2))
    sub_pixel_shifted = ut.sub_pixel_shift(padded_f, new_shape[0]/2.0-com[0], new_shape[1]/2.0-com[1],
new_shape[2]/2.0-com[2])
    ramp_removed_padded = np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(sub_pixel_shifted)))
    ramp_removed = ut.crop_center(ramp_removed_padded, arr.shape)

    return ramp_removed


@measure
def center(image, support):
    dims = image.shape
    image, support = ut.get_centered_both(image, support)

    # place center of mass image*support in the center
    for ax in range(len(dims)):
        com = ndi.center_of_mass(np.absolute(image) * support)
        image = shift(image, int(dims[0]/2 - com[0]), int(dims[1]/2 - com[1]), int(dims[2]/2 - com[2]))
        support = shift(support, int(dims[0]/2 - com[0]), int(dims[1]/2 - com[1]), int(dims[2]/2 - com[2]))

    # set center phase to zero, use as a reference
    phi0 = m.atan2(image.imag[int(dims[0]/2), int(dims[1]/2), int(dims[2]/2)], image.real[int(dims[0]/2), int(dims[1]/2),
int(dims[2]/2)])
    image = image * np.exp(-1j * phi0)

    return image, support


def get_crop(params, shape):
    crop = []
    for i in range(len(shape)):
        if params.crop is None:
            crop.append(shape[i])
        else:
            crop.append(params.crop[i])
            if isinstance(crop[i], float):
                crop[i] = int(crop[i]*shape[i])
    return crop

