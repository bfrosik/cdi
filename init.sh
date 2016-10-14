#!/bin/sh

currentDir=`pwd`
export LD_LIBRARY_PATH=/usr/local/lib:$currentDir/lib/
echo $
cd build
make -f Makefile
cd ..
python setup.py build_ext --inplace
