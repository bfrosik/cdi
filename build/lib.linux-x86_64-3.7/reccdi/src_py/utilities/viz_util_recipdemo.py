import numpy as np
import math as m
import tifffile as tif
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.beamlines.aps_34id.diffractometer as dif
import sys
import os

conf_dir='/home/beams7/CXDUSER/34idc-work/2019/NX2019/SandboxTest/NX2019a-3_483/conf'
data_dir='/home/beams7/CXDUSER/34idc-work/2019/NX2019/SandboxTest/NX2019a-3_483/data'
conf = os.path.join(conf_dir, 'config_disp')
main_conf = os.path.join(conf_dir, 'config')

    # parse the conf once here and save it in dictionary, it will apply to all images in the directory tree
conf_dict = {}
try:
    conf_map = ut.read_config(conf)
    items = conf_map.items()
    for item in items:
        conf_dict[item[0]] = item[1]
except:
    print('cannot parse configuration file ' + conf)

if os.path.isfile(main_conf):
    try:
        config_map = ut.read_config(main_conf)
        scan = config_map.scan
        last_scan = scan.split('-')[-1]
        conf_dict['last_scan'] = int(last_scan)
    except:
        print ("info: scan not determined, can't read " + conf + " configuration file")

# get binning from the config_data file and add it to conf_dict
binning = None
data_conf = os.path.join(conf_dir, 'config_data')
if os.path.isfile(data_conf):
    try:
        conf_map = ut.read_config(data_conf)
        conf_dict['binning'] = conf_map.binning
    except:
        pass

print(conf_dict)

arr=ut.read_tif(os.path.join(data_dir,'data.tif'))

params=dif.DispalyParams(conf_dict)
viz=dif.CXDViz()
viz.set_geometry(params, arr.shape)
viz.add_array(arr, "dp", space='recip')

viz.write_recipspace("test") 
sys.exit()
'''
#binning of the data, this is not actually done, it's to account for previous binning in the saved data.
dbin1=1
dbin2=1
a=t.read_tif("cropped.tif").copy() #copy ensures array is contiguous which pyevtk needs
b=prep.read_scan("/Users/rharder/Desktop/cropped", None, None)

tif.imsave("RawDiffraction.tif", b)
print("raw data",b.shape)
print("imagejsave",a.shape)

#scan info.  
lam=.137  #wavelength
delta=33.0*m.pi/180   #detector angle 1
gamma=11.0*m.pi/180   #detector angle 2
dpx=55e-6/0.5   #pixel size divided by detector dist
dpy=55e-6/0.5
dth=0.01*m.pi/180   #rocking curve scan step.  Everything in radians

vr=vu.CXDViz()
vr.set_geometry(lam, delta, gamma, dbin1*dpx, dbin2*dpy, dth)

q=vr.recip_coords
qmag=np.sqrt(q[0,:,:,:]**2 + q[1,:,:,:]**2 + q[2,:,:,:]**2)
vr.add_array(qmag, "qmag", space='recip')  #add a second property that can be used for color in viz.
vr.write_recipspace("RawDiffraction") 
'''
