# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
import numpy as np
import math as m
import pyevtk.hl as vtk

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'


class CXDViz():

  cropx = 0.5
  cropy = 0.5
  cropz = 0.5
  dir_arrs={}
  recip_arrs={}

  def __init__(self):
    #self.imd = tvtk.ImageData()
    #self.sg = tvtk.StructuredGrid()
    pass


  def set_geometry(self, lam, delta, gamma, dpx, dpy, dth):
    lam = lam
    tth = delta
    gam = gamma
    dpx = dpx
    dpy = dpy
    dth = dth
    dQdpx = np.zeros(3)
    dQdpy = np.zeros(3)
    dQdth = np.zeros(3)
    Astar = np.zeros(3)
    Bstar = np.zeros(3)
    Cstar = np.zeros(3)

    # dQdpx[0] = -m.cos(tth) * m.cos(gam)
    # dQdpx[1] = 0.0
    # dQdpx[2] = +m.sin(tth) * m.cos(gam)
    dQdpx[0] = -m.cos(tth)
    dQdpx[1] = 0.0
    dQdpx[2] = +m.sin(tth)
    print("dqdpx",dQdpx)

    dQdpy[0] = m.sin(tth) * m.sin(gam)
    dQdpy[1] = -m.cos(gam)
    dQdpy[2] = m.cos(tth) * m.sin(gam)
    print("dqdpy",dQdpy)

    dQdth[0] = -m.cos(tth) * m.cos(gam) + 1.0
    dQdth[1] = 0.0
    dQdth[2] = m.sin(tth) * m.cos(gam)
    print("dqdth",dQdth)

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
    self.Tdir = np.array((A, B, C))
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
  
    self.dir_coords = np.dot(self.Tdir, r)

#    self.dir_coords = self.dir_coords.transpose()
    self.dir_coords.shape=origshape
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

  def write_directspace(self, filename, **args):
    print(self.dir_arrs.keys())
    vtk.gridToVTK(filename, self.dir_coords[0,:,:,:].copy(), \
                  self.dir_coords[1,:,:,:].copy(), \
                  self.dir_coords[2,:,:,:].copy(), pointData=self.dir_arrs)
    vtk.imageToVTK(filename, pointData=self.dir_arrs)

  def write_recipspace(self, filename, **args):
    vtk.gridToVTK(filename, self.recip_coords[0,:,:,:].copy(), \
                  self.recip_coords[1,:,:,:].copy(), \
                  self.recip_coords[2,:,:,:].copy(), pointData=self.recip_arrs)
    vtk.imageToVTK(filename, pointData=self.recip_arrs)

