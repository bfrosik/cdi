from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(ext_modules = cythonize(
           ["src_py/cyth/bridge_cpu.pyx", "src_py/cyth/bridge_opencl.pyx",],
           language="c++",)
)



