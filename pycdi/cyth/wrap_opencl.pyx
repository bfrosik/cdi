# distutils: language = c++
# distutils: sources = src/RecWrap.cpp
# distutils: include_dirs = ['include', 'include/af/include',]
# distutils: libraries = ['cdi', 'afopencl',  'config++',]
# distutils: library_dirs = lib

from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr
from libcpp.string cimport string

cdef extern from "../include/RecWrap.hpp":
    cdef cppclass RecWrap:
        RecWrap() except +
        void StartCalc(vector[float], vector[float], vector[float], vector[int], string)
        void StartCalcGenGuess(vector[float], vector[int], string)
        vector[float] GetImageR();
        vector[float] GetImageI();
        vector[float] GetErrors();


cdef class PyRecWrap:
    cdef RecWrap *thisptr
    def __cinit__(self):
        self.thisptr = new RecWrap()
    def __dealloc__(self):
        del self.thisptr
    def start_calc(self, data_r, guess_r, guess_i, dims, config):
        self.thisptr.StartCalc(data_r, guess_r, guess_i, dims, config)
    def start_calc_gen_guess(self, data_r, dims, config):
        self.thisptr.StartCalcGenGuess(data_r, dims, config)
    def get_image_r(self):
        return self.thisptr.GetImageR()
    def get_image_i(self):
        return self.thisptr.GetImageI()
    def get_errors(self):
        return self.thisptr.GetErrors()




