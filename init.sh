#!/bin/sh


echo -n "enter ArrayFire installation directory > "
read af_dir
#af_dir='/local/af'
export LD_LIBRARY_PATH=/usr/local/lib:$af_dir/lib/

AF='AF_DIR'
sed -i 's?'$AF'?'$af_dir'?g' src_py/cyth/*.pyx

echo -n "enter LibConfig installation directory > "
read lc_dir
#lc_dir=/local/bfrosik/libconfig-1.5

LC_DIR=LC_DIR
sed -i 's?'$LC_DIR'?'$lc_dir'?g' src_py/cyth/*.pyx
python setup.py build_ext --inplace
