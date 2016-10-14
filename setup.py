from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(ext_modules = cythonize(
           ["pycdi/cyth/wrap_cpu.pyx", "pycdi/cyth/wrap_opencl.pyx", "pycdi/cyth/wrap_cuda.pyx",],
           language="c++",)
)



