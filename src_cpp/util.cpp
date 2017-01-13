#include "util.hpp"
#include "arrayfire.h"

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

af::array Utils::CropCenter(af::array arr, int roix, int roiy, int roiz)
{
    dim4 dims = arr.dims();
    // Find the coordinates sub-array of the given dimentions in the center of array arr
    int x_beginning = int((dims[0] - roix)/2);
    int x_ending = int(dims[0]-x_beginning);
    int y_beginning = int((dims[1] - roiy)/2);
    int y_ending = int(dims[1]-y_beginning);
    int z_beginning = int((dims[2] - roiz)/2);
    int z_ending = int(dims[2]-z_beginning);

    // zero out all elements of the array arr except the sub-array
    arr(seq(0, x_beginning), span) = 0;
    arr(seq(x_ending, -1), span) = 0;
    arr(seq(0, -1), seq(0, y_beginning), span) = 0;
    arr(seq(0, -1), seq(y_ending, -1), span) = 0;
    arr(seq(0, -1), seq(0, -1), seq(0, z_beginning)) = 0;
    arr(seq(0, -1), seq(0, -1), seq(z_ending, -1)) = 0;

    return arr;
}

af::array Utils::CenterMax(af::array arr)
{
    //find max

    return arr;

}
