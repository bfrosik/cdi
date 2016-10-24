#!/usr/bin/env tcsh

set  called=($_)

if ( "$called" != "") then
    set script_fn='readlink -f $called[2]'
else
    set script_fn=`readlink -f $0`
endif
set currentDir=`dirname $script_fn`
echo $currentDir
set LD_LIBRARY_PATH=/usr/local/lib:$currentDir/lib/
echo $LD_LIBRARY_PATH
###cd build
###make -f Makefile
###cd ..
python setup.py build_ext --build-lib ..

