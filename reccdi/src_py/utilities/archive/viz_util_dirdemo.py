if __name__ =="__main__":
  import numpy as np
  import math as m
  import tifffile as tif
  import tools as t
  import viz_util_xu as vu
  import prep_noconfig as prep
  import os

  #binning of the data, this is not actually done, it's to account for previous binning in the saved data.
  dbin1=2
  dbin2=2
  dir="/Users/rharder/Box/cdi-master/reccdi/src_py/utilities/NX2019a-3_483/results"
  fname=os.path.join(dir,"image.npy")
  #a=t.read_tif("cropped.tif").copy() #copy ensures array is contiguous which pyevtk needs
  #b=prep.read_scan("/Users/rharder/Desktop/cropped", None, None)
  a=np.load(fname)[:-28,:,:]

#  tif.imsave("RawDiffraction.tif", b)
#  print("raw data",b.shape)
#  print("imagejsave",a.shape)

  #scan info.  
  lam=1.37  #wavelength
  delta=33.0*m.pi/180   #detector angle 1
  gamma=11.0*m.pi/180   #detector angle 2
  dpx=55e-6/0.500   #pixel size divided by detector dist
  dpy=55e-6/0.500
  dth=0.01*m.pi/180   #rocking curve scan step.  Everything in radians

  vr=vu.CXDViz()
  vr.set_geometry(lam, delta, gamma, dbin1*dpx, dbin2*dpy, dth)
  vr.add_array(abs(a), "imamp", space='direct')
  #vr.add_array(np.angle(a), "imph", space='direct')
  vr.write_directspace("dirtest.vtk")

  

#  q=vr.recip_coords
#  qmag=np.sqrt(q[0,:,:,:]**2 + q[1,:,:,:]**2 + q[2,:,:,:]**2)
#  vr.add_array(qmag, "qmag", space='recip')  #add a second property that can be used for color in viz.
#  vr.write_recipspace("RawDiffraction") 
