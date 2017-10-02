#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
This module is a suite of utility mehods.
"""

import pylibconfig2 as cfg
import os
from tvtk.api import tvtk
import numpy as np
import math as m
#import src_py.utilities.utils as ut
import utils as ut
import scipy
import scipy.io as sio
import scipy.interpolate as ipl
from mayavi import mlab


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
        deg2rad=np.pi/180.0
        try:
            self.lamda = config_map.lamda
        except AttributeError:
            print ('lamda not defined')
        try:
            self.delta = config_map.delta*deg2rad
        except AttributeError:
            print ('delta not defined')
        try:
            self.gamma = config_map.gamma*deg2rad
        except AttributeError:
            print ('gamma not defined')
        try:
            self.arm = config_map.arm
        except AttributeError:
            print ('arm not defined')
        try:
            self.dth = config_map.dth*deg2rad
        except AttributeError:
            print ('dth not defined')
        try:
            self.coordinates = config_map.coordinates
        except AttributeError:
            print ('coordinates not defined')
        try:
            pixel = config_map.pixel
            self.dpx = pixel[0]/self.arm
            self.dpy = pixel[1]/self.arm
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


    def get_geometry(self):
        """
        The class method calculates geometry of display based on the configuration parameters.
        It returns calculated geometry as array.

        Parameters
        ----------
        none

        Returns
        -------
        numpy.array
            an array defining geometry
        """
        dQdpx=np.zeros(3)
        dQdpy=np.zeros(3)
        dQdth=np.zeros(3)
        Astar=np.zeros(3)
        Bstar=np.zeros(3)
        Cstar=np.zeros(3)

        dQdpx[0] = -m.cos(self.delta)*m.cos(self.gamma)
        dQdpx[1] = 0.0
        dQdpx[2] = +m.sin(self.delta)*m.cos(self.gamma)

        dQdpy[0] = m.sin(self.delta)*m.sin(self.gamma)
        dQdpy[1] = -m.cos(self.gamma)
        dQdpy[2] = m.cos(self.delta)*m.sin(self.gamma)

        dQdth[0] = -m.cos(self.delta)*m.cos(self.gamma)+1.0
        dQdth[1] = 0.0
        dQdth[2] = m.sin(self.delta)*m.cos(self.gamma)

        Astar[0] = 2*m.pi/self.lamda*self.dpx*dQdpx[0]
        Astar[1] = 2*m.pi/self.lamda*self.dpx*dQdpx[1]
        Astar[2] = 2*m.pi/self.lamda*self.dpx*dQdpx[2]

        Bstar[0] = (2*m.pi/self.lamda)*self.dpy*dQdpy[0]
        Bstar[1] = (2*m.pi/self.lamda)*self.dpy*dQdpy[1]
        Bstar[2] = (2*m.pi/self.lamda)*self.dpy*dQdpy[2]

        Cstar[0] = (2*m.pi/self.lamda)*self.dth*dQdth[0]
        Cstar[1] = (2*m.pi/self.lamda)*self.dth*dQdth[1]
        Cstar[2] = (2*m.pi/self.lamda)*self.dth*dQdth[2]


        denom=np.dot( Astar, np.cross(Bstar,Cstar) )
        A=2*m.pi*np.cross(Bstar,Cstar)/denom
        B=2*m.pi*np.cross(Cstar,Astar)/denom
        C=2*m.pi*np.cross(Astar,Bstar)/denom

        return np.array( (A,B,C) )


def crop_array_center(ar, crop):
    """
    This method returns cropped array from the given array ar. The crop is taken from the center of the array
    and the size is defined by crop. If any of the crop value is either equal zero or less, or is greater than
    the corresponding array dimension, the crop value defaults to that dimension.

    Parameters
    ----------
    ar : numpy.array
        array to be cropped

    crop : tuple
        the dimension of new cropped array

    Returns
    -------
    cropped array
    """

    dims = list(ar.shape)
    if len(dims)==2:
        dims.append(1)
    cropx = crop[0]
    cropy = crop[1]
    cropz = crop[2]
    if dims[0] > cropx and cropx > 0:
        x = cropx
    else:
        x = dims[0]
    startx = dims[0]/2 - x/2
    endx = dims[0]/2 + x/2
    if startx == endx:
        endx += 1

    if dims[1] > cropy and cropy > 0:
        y = cropy
    else:
        y = dims[1]
    starty = dims[1]/2 - y/2
    endy = dims[1]/2 + y/2
    if starty == endy:
        endy += 1

    if dims[2] > cropz and cropz > 0:
        z = cropz
    else:
        z = dims[2]
    startz = dims[2]/2 - z/2
    endz = dims[2]/2 + z/2
    if startz == endz:
        endz += 1

    return ar[startx:endx, starty:endy, startz:endz]


def get_coords(dims, dx, dy, dz, geometry):
    """
    This method calculates grid based on array dimension, configuration parameters coordinates, and
    geometry.

    Parameters
    ----------
    dims : tuple
        displayed array dimension

    dx : int
        the configured x coordinate

    dy : int
        the configured y coordinate

    dz : int
        the configured z coordinate

    geometry : array
        an array defining geometry, calculated from configuration parameters

    Returns
    -------
    grid
    """

    r = np.mgrid[ (dims[0]-1)*dx:-dx:-dx,0:dims[1]*dy:dy, 0:dims[2]*dz:dz]
    r.shape = 3,dims[0]*dims[1]*dims[2]
    r = r.transpose()
    return np.dot(r, geometry)


def write_array(sg, filename):
    """
    This method writes initialized StructuredGrid object into given file.

    Parameters
    ----------
    sg : StructuredGrid
        an instance of vtkt.StructuredGrid initialized with data

    filename : str
        name of the file the image will be written to

    Returns
    -------
    none
    """

    writer = tvtk.StructuredGridWriter()
    writer.file_type = 'binary'
    writer.file_name = filename
    writer.set_input_data(sg)
    writer.write()


def write_to_vtk(conf, ar, filename):
    """
    This function writes a numpy array into vtk format file.
    It reads configuration into DispalyParams object.
    The given array is cropped to the configured size if the crop parameter is defined in configuration file.
    Based on configuration parameters the grid needed for the tvtk StructuredGrid is calculated.
    Other StructuredGrid attributes are set.
    The initialized StructuredGrid object is then written into vtk type file. If configuration parameter
    save_two_files is set to True, one file will be saved for amplitudes with "_Amp.vtk" ending, and one for
    phases with "_Phase.vtk" ending. Otherwise, a single file will be saved that contains double array
    with amplitudes a nd phases.

    Parameters
    ----------
    conf : str
        configuration file name
        
    ar : numpy array
        a complex array thatwill be saved

    filename : str
        a prefix to an output filename

    Returns
    -------
    none
    """

    params = DispalyParams(conf)

    if params.crop is None:
        dims = ar.shape
        arr_cropped = ar.ravel()
    else:
        dims = params.crop
        arr_cropped = crop_array_center(ar, params.crop).ravel()

    amps = np.abs(arr_cropped)
    phases = np.arctan2(arr_cropped.imag, arr_cropped.real)

    geometry = params.get_geometry()
    coordinates = get_coords(dims, params.coordinates[0], params.coordinates[1], params.coordinates[2], geometry)

    sg = tvtk.StructuredGrid()
    sg.points = coordinates
    sg.dimensions=(dims[2], dims[1], dims[0])
    sg.extent=0, dims[2]-1, 0, dims[1]-1, 0, dims[0]-1
    if params.save_two_files:
        sg.point_data.scalars = amps
        sg.point_data.scalars.name = "Amp"
        write_array(sg, filename + "_Amp.vtk")

        sg.point_data.scalars = phases
        sg.point_data.scalars.name = "Phase"
        write_array(sg, filename + "_Phase.vtk")
    else:
        sg.point_data.scalars=amps
        sg.point_data.scalars.name="Amp"
        ph=tvtk.FloatArray()
        ph.from_array(phases)
        ph.name="Phase"
        sg.point_data.add_array(ph)
        write_array(sg, filename + ".vtk")


def shift(arr, s0, s1, s2):
    shifted0 = np.roll(arr, s0, 0)
    shifted1 = np.roll(shifted0, s1, 1)
    return np.roll(shifted1, s2, 2)

def sub_pixel_shift(arr, shift_ind):
    buf = np.fft.fftn(arr)
    dims = buf.shape
    #x = np.fft.ifftshift( np.arange(-((dims[0]-1)/2), dims[0]/2) )
    #y = np.fft.ifftshift( np.arange(-((dims[1]-1)/2), dims[1]/2) )
    #z = np.fft.ifftshift( np.arange(-((dims[2]-1)/2), dims[2]/2) )
    x = np.fft.ifftshift( np.arange(-(dims[0]/2), dims[0]/2) )
    y = np.fft.ifftshift( np.arange(-(dims[1]/2), dims[1]/2) )
    z = np.fft.ifftshift( np.arange(-(dims[2]/2), dims[2]/2) )
    gx, gy, gz = np.meshgrid(x,y,z)

    grid_shift = - gx * shift_ind[0]/dims[0] - gy * shift_ind[1]/dims[1] - gy * shift_ind[2]/dims[2]
    g = buf * np.exp(1j*2*np.pi*grid_shift)
    return np.fft.ifftn(g)
    

def center_array(arr):
    dims = arr.shape
    max_coordinates = list(np.unravel_index(np.argmax(np.absolute(arr)), dims))
    print 'max_coordinates', max_coordinates
    centered = shift(arr, dims[1]/2-max_coordinates[1], dims[0]/2-max_coordinates[0],dims[2]/2-max_coordinates[2])
    return cented, max_coordinates

def center_of_mass(array):
    array.astype(float)
    tot = sum(sum(sum(array)))
    print 'total', tot

    dims = array.shape
    x = np.arange(-(dims[1]-1)/2.0, (dims[1])/2.0)
    y = np.arange(-(dims[0]-1)/2.0, (dims[0])/2.0)
    z = np.arange(-(dims[2]-1)/2.0, (dims[2])/2.0)
    gx, gy, gz = np.meshgrid(x,y,z)

    sx = sum(sum(sum(array * gx)))/tot
    sy = sum(sum(sum(array * gy)))/tot
    sz = sum(sum(sum(array * gz)))/tot
    
    t = (sx, sy, sz)
    return np.asarray(t)-1

def remove_ramp(arr):
    # pad zeros around arr, to the size of 3 times (ups = 3) of arr size
    padded = ut.zero_pad(arr, arr.shape)
    data = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(padded)))
    com = center_of_mass(np.power(np.absolute(data),2))-.5
    print 'com', com
    sub_pixel_shifted = sub_pixel_shift(data, (com[1], com[0], com[2]))
    ramp_removed_padded = np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(sub_pixel_shifted)))
    ramp_removed = ut.crop_center(ramp_removed_padded, arr.shape)
    
    return ramp_removed, com[1]/3, com[0]/3

def ross_tform(shape, lamda, delta, gamma, pixelx, pixely, dth, arm ):
    dpx = pixelx/arm
    dpy = pixely/arm

    dQdpx=np.zeros(3)
    dQdpy=np.zeros(3)
    dQdth=np.zeros(3)
    Astar=np.zeros(3)
    Bstar=np.zeros(3)
    Cstar=np.zeros(3)

    dQdpx[0] = -m.cos(delta)*m.cos(gamma)
    dQdpx[1] = 0.0
    dQdpx[2] = +m.sin(delta)*m.cos(gamma)

    dQdpy[0] = m.sin(delta)*m.sin(gamma)
    dQdpy[1] = -m.cos(gamma)
    dQdpy[2] = m.cos(delta)*m.sin(gamma)

    dQdth[0] = -m.cos(delta)*m.cos(gamma)+1.0
    dQdth[1] = 0.0
    dQdth[2] = m.sin(delta)*m.cos(gamma)

    Astar[0] = 2*m.pi/lamda*dpx*dQdpx[0]
    Astar[1] = 2*m.pi/lamda*dpx*dQdpx[1]
    Astar[2] = 2*m.pi/lamda*dpx*dQdpx[2]
    print 'Astar', Astar

    Bstar[0] = (2*m.pi/lamda)*dpy*dQdpy[0]
    Bstar[1] = (2*m.pi/lamda)*dpy*dQdpy[1]
    Bstar[2] = (2*m.pi/lamda)*dpy*dQdpy[2]

    Cstar[0] = (2*m.pi/lamda)*dth*dQdth[0]
    Cstar[1] = (2*m.pi/lamda)*dth*dQdth[1]
    Cstar[2] = (2*m.pi/lamda)*dth*dQdth[2]

    denom=np.dot( Astar, np.cross(Bstar,Cstar) )
    Adenom = np.cross(Bstar,Cstar)
    Bdenom = np.cross(Cstar,Astar)
    Cdenom = np.cross(Astar,Bstar)

    A = 2*np.pi*Adenom/denom
    B = 2*np.pi*Bdenom/denom
    C = 2*np.pi*Cdenom/denom

    l0 = [A[0], B[0], C[0]]
    l1 = [A[1], B[1], C[1]]
    l2 = [A[2], B[2], C[2]]
    #T = np.asarray([l0, l1, l2])
    T = np.asarray((A,B,C))
    print 'T', T
    return T

def UpdateCoordSystem(shape):
    dx = 1.0/shape[1]
    dy = 1.0/shape[0]
    dz = 1.0/shape[2]
    #r = np.mgrid[(shape[0]-1)*dx:-dx:-dx,0:shape[1]*dy:dy, 0:shape[2]*dz:dz]
    r = np.mgrid[ dx:(shape[0]+1)*dx:dx,dy:(shape[1]+1)*dy:dy, dz:(shape[2]+1)*dz:dz]
    r.shape = 3,shape[0]*shape[1]*shape[2]
    x = r[0]
    print 'x shape', x.shape
    #r = r.transpose()
    return r


def det2lab(arr):
    deg2rad = np.pi/180.0000 
    # Detector and scan variables 
    det_px=   0.000055000000000
    binx=1.00
    biny=1.00
    delta_deg=30.100
    gam_deg=14.000
    pixelx=binx*det_px 
    pixely=biny*det_px 
    arm=   0.635000000000000
    lam=   0.139330000000000
    delta=delta_deg*deg2rad 
    gam=gam_deg*deg2rad 
    dth=   0.000174532925199
    dtilt=   0.000000000000000

    sx=lam*arm/pixelx
    sy=lam*arm/pixely
    sz=abs(lam/(dth*np.pi/180)/arr.shape[2])
    print 'sz', sz
    sample_pixel = min((sx,sy,sz))
    print 'sample pixel', sample_pixel
    T = ross_tform(arr.shape, lam, delta, gam, pixelx, pixely, dth, arm )
    r = UpdateCoordSystem(arr.shape)
    print 'r, shape,', r.shape
    #print r[0,0:50]
    #print r[0,2097100:2097152]
    #print r[1,0:50]
    #print r[1,2097100:2097152]
    #print r[2,0:50]
    #print r[2,2097100:2097152]
    print r[:,0]

    r1 = np.array((r[0],r[2],r[1]))
    r1 = r1.transpose()

    r = UpdateCoordSystem(arr.shape)
    print 'T, r shape', T.shape, r.shape
    coords = np.dot(r.transpose(),T)
    print coords[0]

    print 'coords', coords.shape
    #np.reshape(coords, (3, arr.shape[1], arr.shape[0], arr.shape[2]))
    print 'coords shape', coords.shape


    X = coords.transpose()[0]

    #x = np.linspace(1.0/arr.shape[0], 1.0/arr.shape[0], 1)
    #X = np.dot(x, T[0])
    #y = np.linspace(1.0/arr.shape[1], 1.0/arr.shape[1], 1)
    #Y = np.dot(y, T[:,1])
    #z = np.linspace(1.0/arr.shape[2], 1.0/arr.shape[2], 1)
    #Z = np.dot(z, T[2])
    print 'X, min ', X[0:50], X[2097100:2097152], min(X)
    X = X - min(X)
    X = X - max(X)/2
    Y = coords.transpose()[1]
    print 'Y, min ', Y[0:50], Y[2097100:2097152], min(Y)
    Y = Y - min(Y)
    Y = Y - max(Y)/2
    Z = coords.transpose()[2]
    print 'Z, min ', Z[0:50], Z[2097100:2097152], min(Z)
    Z = Z - min(Z)
    Z = Z - max(Z)/2
    print 'X type, shape', type(X), X.shape
    coords1 = np.array((X,Y,Z)).transpose()
    print 'coords1 shape', coords1.shape
    #X = np.sort(X)
    #Y = np.sort(Y)
    #Z - np.sort(Z)
    #np.reshape(X, arr.shape)
    #np.reshape(Y, arr.shape)
    #np.reshape(Z, arr.shape)
    XX = r[:,0] * sample_pixel * arr.shape[1]
    XX = XX - max(XX)/2
    YY = r[:,1] * sample_pixel * arr.shape[0]
    YY = YY - max(YY)/2
    ZZ = r[:,2] * sample_pixel * arr.shape[2]
    ZZ = ZZ - max(ZZ)/2
    #ut.flip(arr, 2)

    #coords2 = ipl.RegularGridInterpolator((X,Y,Z), arr)
    #coords3 = coords2((XX,YY,ZZ))

    coords2 = ipl.griddata((X,Y,Z), arr.ravel(), (XX,YY,ZZ), fill_value=0.0)

    #return coords1.transpose() * sample_pixel
    return coords2
    

def coordinate_transform_bac(image, support):
    mx = max(np.absolute(image).ravel().tolist())
    image = image/mx
    dims = image.shape
    phases = np.arctan2(image.imag, image.real).ravel()
    amps = np.absolute(image).ravel()
    
    coordinates = det2lab(image)

    sg = tvtk.StructuredGrid()
    sg.points = coordinates
    sg.dimensions=(dims[2], dims[1], dims[0])
    sg.extent=0, dims[2]-1, 0, dims[1]-1, 0, dims[0]-1
    sg.point_data.scalars=amps
    sg.point_data.scalars.name="Amp"
    ph=tvtk.FloatArray()
    ph.from_array(phases)
    ph.name="Phase"
    sg.point_data.add_array(ph)
    write_array(sg, "fromML.vtk")
    

def coordinate_transform(image, support):
    mx = max(np.absolute(image).ravel().tolist())
    image = image/mx
    dims = image.shape
    phases = np.arctan2(image.imag, image.real).ravel()
    amps = np.absolute(image).ravel()
    
    coordinates = det2lab(image)

    sg = tvtk.StructuredGrid()
    sg.points = coordinates
    sg.dimensions=(dims[2], dims[1], dims[0])
    sg.extent=0, dims[2]-1, 0, dims[1]-1, 0, dims[0]-1
    sg.point_data.scalars=amps
    sg.point_data.scalars.name="Amp"
    ph=tvtk.FloatArray()
    ph.from_array(phases)
    ph.name="Phase"
    sg.point_data.add_array(ph)
    write_array(sg, "fromML.vtk")
    

def save_to_file(arr, file_name):
    from tvtk.api import tvtk, write_data
    id=tvtk.ImageData()
    id.point_data.scalars=abs(arr.ravel(order='F'))
    id.dimensions=arr.shape
    write_data(id, file_name)


def prepare_disp(image, support):
    dims = np.asarray(image.shape)
    max_coordinates = np.asarray(list(np.unravel_index(np.argmax(np.absolute(image)), dims)))
    print 'max_coordinates', max_coordinates
    shifts = (dims+1)/2-(max_coordinates+1)
    shifts = list(shifts)
    print 'shifts', shifts

    image = shift(image, shifts[0], shifts[1], shifts[2])
    support = shift(support, shifts[0], shifts[1], shifts[2])

    com = center_of_mass(np.absolute(image) * support)
    print 'com', com
    com = -1 * np.ma.round(com).astype(np.int)
    print 'after round', com
    shift_ind = list(com)
    shift_ind[0], shift_ind[1] = shift_ind[1], shift_ind[0]

    image = shift(image, shift_ind[0], shift_ind[1], shift_ind[2])
    support = shift(support, shift_ind[0], shift_ind[1], shift_ind[2])
    
    # set COM phase to zero, use as a reference
    phi0 = m.atan2(image.imag[dims[0]/2, dims[1]/2, dims[2]/2], image.real[dims[0]/2, dims[1]/2, dims[2]/2])
    print 'phi0', phi0
    image = image * np.exp(-1j*phi0)

    #if recenter_rec:
    image, com1, com0 = remove_ramp(image)
    flip = 1 #this can be configured
    #if flip == 1:
    #    ut.flip(image,1)
    #    ut.flip(support,1)
    #save not yet
    #save_to_file(image, 'image.vtk')
    #save_to_file(support, 'support_mass_centered.vtk')

    coordinate_transform(image, support)    

    

# arr=np.zeros(256*256*1)
# arr.shape=(256,256,1)
# arr[64:196,64:196]=1.0
# write_to_vtk('/local/bfrosik/cdi/config.test', arr, '/local/bfrosik/cdi/test')


#read the image and support from mat files
im_dict = sio.loadmat('/local/bfrosik/CDI/pnm.mat')
image = im_dict['pnm']
sup_dict = sio.loadmat('/local/bfrosik/CDI/support.mat')
support = sup_dict['support']
prepare_disp(image, support)

