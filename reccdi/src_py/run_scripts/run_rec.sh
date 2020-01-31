#!/bin/sh


export LD_LIBRARY_PATH=/usr/local/lib:/local/libconfig/lib:/local/af/lib

#export LD_LIBRARY_PATH=/home/beams/CXDUSER/CDI/libconfig/lib:/usr/lib64:/home/beams/CXDUSER/CDI/ArrayFire-v3.4.2/lib:/usr/local-linux/cuda-8.0/lib64:/usr/local-linux/cuda-8.0/nvvm/lib64

#newest arrayfire version will work with cuda 9.1
#export LD_LIBRARY_PATH=/home/beams/CXDUSER/CDI/arrayfire/lib:/home/beams/CXDUSER/CDI/libconfig/lib:/local/cuda-9.0/lib64:/local/cuda-9.0/nvvm/lib64

python run_rec.py $1 $2
#python run_rec.py "opencl" <experiment_dir>