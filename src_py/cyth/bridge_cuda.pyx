# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

# distutils: language = c++
# distutils: include_dirs = ['include', 'AF_DIR/include', 'LC_DIR/lib',]
# distutils: sources = ['src_cpp/algorithm.cpp', 'src_cpp/bridge.cpp', 'src_cpp/manager.cpp', 'src_cpp/parameters.cpp', 'src_cpp/pcdi.cpp', 'src_cpp/state.cpp', 'src_cpp/support.cpp', 'src_cpp/util.cpp', 'src_cpp/worker.cpp']
# distutils: libraries = ['afcuda',  'config++',]
# distutils: library_dirs = ['AF_DIR/lib', 'LC_DIR/lib/.libs', ]

from libcpp.vector cimport vector
from libcpp.string cimport string

cdef extern from "../include/bridge.hpp":
    cdef cppclass Bridge:
        Bridge() except +
        void StartCalcWithGuess(vector[float], vector[float], vector[float], vector[int], string)
        void StartCalc(vector[float], vector[int], string)
        void StartCalcMultiple(vector[float], vector[int], string, int)
        vector[def_type] GetImageR()
        vector[def_type] GetImageI()
        vector[def_type] GetErrors()
        vector[float] GetSupportV()
        vector[def_type] GetCoherenceV()


cdef class PyBridge:
    cdef Bridge *thisptr
    def __cinit__(self):
        self.thisptr = new Bridge()
    def __dealloc__(self):
        del self.thisptr
    def start_calc_with_guess(self, data_r, guess_r, guess_i, dims, config):
        self.thisptr.StartCalcWithGuess(data_r, guess_r, guess_i, dims, config.encode())
    def start_calc(self, data_r, dims, config):
        self.thisptr.StartCalc(data_r, dims, config.encode())
    def start_calc_multiple(self, data_r, dims, config, no_threads):
        self.thisptr.StartCalcMultiple(data_r, dims, config, no_threads)
    def get_image_r(self):
        return self.thisptr.GetImageR()
    def get_image_i(self):
        return self.thisptr.GetImageI()
    def get_errors(self):
        return self.thisptr.GetErrors()
    def get_support(self):
        return self.thisptr.GetSupportV()
    def get_coherence(self):
        return self.thisptr.GetCoherenceV()

