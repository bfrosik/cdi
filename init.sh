#!/bin/sh

currentDir=`pwd`
export LD_LIBRARY_PATH=/usr/local/lib:$currentDir/lib/
python setup.py build_ext --inplace
