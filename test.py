import src_py.controller.reconstruction as rec
import sys
import os
import argparse
from os.path import expanduser

def main(arg):

    parser = argparse.ArgumentParser()
    parser.add_argument("proc", help="the processor the code will run on, can be 'cpu', 'opencl', or 'cuda'.")
    parser.add_argument("fname", help="data file filename. It is assumed the file is in tif format.")
    parser.add_argument("conf", help="configuration file.")

    args = parser.parse_args()
    proc = args.proc
    fname = args.fname
    conf = args.conf

    rec.reconstruction(proc, fname, conf)


if __name__ == "__main__":
    main(sys.argv[1:])

#python test.py 'opencl' '/home/phoebus/BFROSIK/CDI/S149/Staff14-3_S0149.tif' 'config.test'
        
