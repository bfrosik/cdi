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
import reccdi.src_py.beamlines.aps_34id.spec as sput
import reccdi.src_py.beamlines.aps_34id.detectors as det

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'

class DispalyParams:
    """
    This class encapsulates parameters defining image display. The parameters are
read from config file on construction or whereever they may exist.  This class is
basically an information agglomerator for the viz generation.
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
            #get stuff from the spec file.
            delta, gamma, theta, phi, chi, scanmot, scanmot_del, detdist, detector, energy = sput.parse_spec(specfile, last_scan)
            self.delta = delta 
            self.gamma = gamma 
            self.theta = theta 
            self.phi = phi 
            self.chi = chi 
            self.detdist = detdist
            self.energy = energy
            self.scanmot=scanmot
            self.scanmot_del=scanmot_del
            self.detector=detector

        except Exception as e:
            pass
        # override the parsed parameters with entries in config file
        try:
            self.energy = config['energy']
        except KeyError:
            print("energy from specfile")
            pass
        try:
            self.delta = config['delta'] 
        except KeyError:
            pass
        try:
            self.gamma = config['gamma']
        except KeyError:
            pass
        try:
            self.theta = config['theta'] 
        except KeyError:
            pass
        try:
            self.phi = config['phi'] 
        except KeyError:
            pass
        try:
            self.chi = config['chi'] 
        except KeyError:
            pass
        try:
            self.scanmot = config['scanmot']
        except KeyError:
            pass
        try:
            self.scanmot_del = config['scanmot_del']
        except KeyError:
            pass
        try:
            self.detdist = config['arm']
        except KeyError:
            pass
        try:
            self.detector = config['detector']
        except KeyError:
            pass
        try:
            self.detector_obj=det.getdetclass(self.detector)
        except:
            self.detector_obj = None

        try:
            pixel = self.detector_obj.get_pixel()
            pixelorientation=self.detector_obj.get_pixelorientation()
        except:
            pass
        try:
            pixel = config['pixel']
        except KeyError:
            pass
        try:
            pixelorientation = config['pixelorientation']
        except KeyError:
            pass

        pixel = pixel[1:-1]
        self.pixel = pixel.split(',')
        self.pixel[0], self.pixel[1] = float(self.pixel[0]), float(self.pixel[1]) 
        self.pixelorientation=pixelorientation[1:-1].split(',')

        try:
            self.binning = []
            binning = config['binning']
            for i in range(len(binning)):
                self.binning.append(binning[i])
            for _ in range(3 - len(self.binning)):
                self.binning.append(1)
        except KeyError:
            self.binning = [1,1,1]
        try:
            self.crop = []
            crop = config['crop']
            for i in range(len(crop)):
                self.crop.append(crop[i])
            for _ in range(3 - len(self.crop)):
                self.crop.append(1.0)
            crop[0], crop[1] = crop[1], crop[0]
        except KeyError:
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
  def set_geometry(self, p, shape):
    self.params = p
    px = p.pixel[0]*p.binning[0]
    py = p.pixel[1]*p.binning[1]
    detdist=p.detdist/1000.0  #convert to meters
    energy=p.energy*1000  #x-ray energy in eV
   
    print("running the xrayutilities version and tvtk")
    self.qc=xuexp.QConversion(['y+','z-','x-'], ['y+','x-'],(0,0,1),en=energy) 
    #compute for 4pixel (2x2) detector
    self.qc.init_area(p.pixelorientation[0],p.pixelorientation[1], shape[0],shape[1], 2,2, distance=detdist, pwidth1=px, pwidth2=py)

    #vtrans=np.vectorize(self.qc.transformSample2Lab)
#
    q1=np.array(self.qc.area(p.theta,p.chi,p.phi,p.delta,p.gamma,deg=True))
    #qshape=q1.shape
    #q1=np.array(vtrans([q1[0,:,:].ravel(),q1[1,:,:].ravel(),q1[2,:,:].ravel()],p.theta,p.chi,p.phi)).reshape(qshape)
    if p.scanmot.strip()=='th':
      q2=np.array(self.qc.area(p.theta+p.scanmot_del,p.chi,p.phi,p.delta,p.gamma,deg=True))
    #  q2=np.array(self.qc.transformSample2Lab([q2[0,:,:],q1[1,:,:],q1[2,:,:]],p.theta+p.scanmot_del,p.chi,p.phi))
    elif p.scanmot.strip()=='chi':
      q2=np.array(self.qc.area(p.theta,p.chi+p.scanmot_del,p.phi,p.delta,p.gamma,deg=True))
    #  q2=np.array(self.qc.transformSample2Lab([q2[0,:,:],q1[1,:,:],q1[2,:,:]],p.theta,p.chi+p.scanmot_del,p.phi))
    elif p.scanmot.strip()=='phi':
      q2=np.array(self.qc.area(p.theta,p.chi,p.phi+p.scanmot_del,p.delta,p.gamma,deg=True))
    #  q2=np.array(self.qc.transformSample2Lab([q2[0,:,:],q1[1,:,:],q1[2,:,:]],p.theta,p.chi,p.phi+p.scanmot_del))
    #Astar=q1[:,1,0]-q1[:,0,0]
    #Bstar=q1[:,0,1]-q1[:,0,0]
    #Cstar=(q2-q1)[:,0,0]
    Astar=q1[:,1,0]-q1[:,0,0]
    Bstar=q1[:,0,1]-q1[:,0,0]
    Cstar=(q2-q1)[:,0,0]
    print("Recip")
    print(Astar, Bstar, Cstar)
    Astar=self.qc.transformSample2Lab(Astar, p.theta,p.chi,p.phi)
    Bstar=self.qc.transformSample2Lab(Bstar, p.theta,p.chi,p.phi)
    Cstar=self.qc.transformSample2Lab(Cstar, p.theta,p.chi,p.phi)



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
    print(self.Trecip)

    self.Tdir = np.zeros(9)
    self.Tdir.shape = (3, 3)
    self.Tdir = np.array((A, B, C)).transpose()
    print("Direct")
    print(A,B,C)
    print(self.Tdir)

    self.dirspace_uptodate=0
    self.recipspace_uptodate=0

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
