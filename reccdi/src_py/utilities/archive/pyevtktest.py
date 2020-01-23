#! /usr/bin/env python

# **************************************************************
# * Example of how to use the high level gridToVTK function.   *
# * This example shows how to export a structured grid.        *
# **************************************************************

from pyevtk.hl import gridToVTK
import numpy as np
import random as rnd

# Dimensions
nx, ny, nz = 10, 5, 2
lx, ly, lz = 10.0, 5.0, 1.0
dx, dy, dz = lx/nx, ly/ny, lz/nz

ncells = nx * ny * nz
npoints = (nx + 1) * (ny + 1) * (nz + 1)

# Coordinates
X = np.arange(0, lx + 0.1*dx, dx, dtype='float64')
Y = np.arange(0, ly + 0.1*dy, dy, dtype='float64')
Z = np.arange(0, lz + 0.1*dz, dz, dtype='float64')

x = np.zeros((nx + 1, ny + 1, nz + 1))
y = np.zeros((nx + 1, ny + 1, nz + 1))
z = np.zeros((nx + 1, ny + 1, nz + 1))

# We add some random fluctuation to make the grid
# more interesting
for k in range(nz + 1):
    for j in range(ny + 1):
        for i in range(nx + 1):
            x[i,j,k] = X[i]  
            y[i,j,k] = Y[j] 
            z[i,j,k] = Z[k] 

# Variables
#pressure = np.random.rand(ncells).reshape( (nx, ny, nz))
#temp = np.random.rand(npoints).reshape( (nx + 1, ny + 1, nz + 1))

#gridToVTK("./structured", x, y, z, cellData = {"pressure" : pressure}, pointData = {"temp" : temp})
