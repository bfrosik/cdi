#include "util.hpp"
#include "arrayfire.h"
#include "common.h"
#include <algorithm>
#include "cstdio"

using namespace af;

int Utils::GetDimension(int dim)
{
    int new_dim = dim;
    while (! IsDimCorrect(new_dim))
    {
        new_dim++;
    }
    return new_dim;
}

bool Utils::IsDimCorrect(int dim)
{
    int sub = dim;
    while (sub % 2 == 0)
    {
        sub = sub/2;
    }
    while (sub % 3 == 0)
    {
        sub = sub/3;
    }
    while (sub % 5 == 0)
    {
        sub = sub/5;
    }
    if (sub == 1)
        return true;
    else
        return false;
}

af::array Utils::CropCenter(af::array arr, int * roi)
{
    dim4 dims = arr.dims();
    printf("in CropCenter dims %i %i %i\n", dims[0], dims[1], dims[2]);
    // Find the coordinates sub-array of the given dimentions in the center of array arr
    int x_beginning = int(dims[0]/2 - roi[0]/2);
    int x_ending = x_beginning + roi[0];
    int y_beginning = int(dims[1]/2 - roi[1]/2);
    int y_ending = y_beginning + roi[1];
    int z_beginning = int(dims[2]/2 - roi[2]/2);
    int z_ending = z_beginning + roi[2];;

    // zero out all elements of the array arr except the sub-array
//    arr(seq(0, x_beginning), span) = 0;
//    arr(seq(x_ending, -1), span) = 0;
//    arr(seq(0, -1), seq(0, y_beginning), span) = 0;
//    arr(seq(0, -1), seq(y_ending, -1), span) = 0;
//    arr(seq(0, -1), seq(0, -1), seq(0, z_beginning)) = 0;
//    arr(seq(0, -1), seq(0, -1), seq(z_ending, -1)) = 0;

    // select the subarray
    af::array cropped = arr(seq(x_beginning + 1, x_ending), seq(y_beginning + 1, y_ending), seq(z_beginning + 1, z_ending));
    printf("in CropCenter result dims %i %i %i %i\n", cropped.dims()[0], cropped.dims()[1], cropped.dims()[2], cropped.dims()[0]*cropped.dims()[1]*cropped.dims()[2]);
    return cropped;

}

af::array Utils::CropRoi(af::array arr, int * roi)
{
    // select the subarray
    return arr(seq(0, roi[0]-1), seq(0, roi[1]-1), seq(0, roi[2]-1));
}

af::array Utils::CenterMax(af::array arr, int * kernel)
{
    printf("in CenterMax dims %i %i %i %i\n", arr.dims()[0], arr.dims()[1], arr.dims()[2], arr.dims()[0]*arr.dims()[1]*arr.dims()[2]);
    //find indexes of max
    d_type *arr_values = arr.host<d_type>();
    std::vector<d_type> v(arr_values, arr_values + arr.elements());
    std::vector<d_type>::iterator result = std::max_element(v.begin(), v.end());
    int max_offset = result - v.begin();
    printf("maximum value, %i %f\n", max_offset, v[max_offset]);
    delete [] arr_values;
    int x_max = max_offset % arr.dims()[0];
    int y_max = max_offset / arr.dims()[0] % arr.dims()[1];
    int z_max = max_offset/ (arr.dims()[0] * arr.dims()[1]);
    printf("max indexes %i %i %i\n", x_max, y_max, z_max);
    printf("in CenterMax5\n");

    // TODO ask Ross if the abs should be applied before figuring out maximum

    af::array shifted = af::shift(arr, arr.dims()[0]/2-x_max, arr.dims()[1]/2-y_max, arr.dims()[2]/2-z_max );
    printf("in CenterMax6\n");
    return shifted;

}

af::array Utils::ShiftMax(af::array arr, int * kernel)
{
    printf("in ShiftMax dims %i %i %i %i\n", arr.dims()[0], arr.dims()[1], arr.dims()[2], arr.dims()[0]*arr.dims()[1]*arr.dims()[2]);
    //find indexes of max
    d_type *arr_values = arr.host<d_type>();
    std::vector<d_type> v(arr_values, arr_values + arr.elements());
    std::vector<d_type>::iterator result = std::max_element(v.begin(), v.end());
    int max_offset = result - v.begin();
    printf("maximum value, %i %f\n", max_offset, v[max_offset]);
    delete [] arr_values;
    int x_max = max_offset % arr.dims()[0];
    int y_max = max_offset / arr.dims()[0] % arr.dims()[1];
    int z_max = max_offset/ (arr.dims()[0] * arr.dims()[1]);
    printf("ShiftMax max indexes %i %i %i\n", x_max, y_max, z_max);

    // TODO ask Ross if the abs should be applied before figuring out maximum

    af::array shifted = af::shift(arr, -x_max, -y_max, -z_max );
    return shifted;

}
