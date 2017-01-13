#ifndef util_hpp
#define util_hpp

namespace af {
    class array;
}

class Utils
{
public:
    // This method takes in an array dimension and returns a new number (i.e. dimension) that is not
    // smaller than the given value, and is supported by opencl library (i.e. divisible by powers of 2, 3, and 5 only)
    static int GetDimension(int dim);

    // This is a helper method. Returns true if the given dimension is supported by opencl library, and false otherwise.
    static bool IsDimCorrect(int dim);

    // This method takes a 3D array, and dimensions of sub-array. It is assumed that the dimensions do not extend array's
    // dimensions.
    // The method returns the array with the sub-array centered and preserved values. All other elements of the array
    // that are beyound the sub-array are zeroed out.
    static af::array CropCenter(af::array arr, int roix, int roiy, int roiz);

    // This method finds the maximum value in the given array arr, places it in the center, shifting circular the content,
    // in all dimensions.
    static af::array CenterMax(af::array arr);
};

#endif /* util_hpp */
