//
//  worker.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/12/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#include "fstream"
#include "worker.hpp"
#include "cstdio"
#include "cstdlib"
#include "math.h"
#include "vector"
#include "parameters.hpp"
#include "state.hpp"
#include "common.h"


af::array data;
d_type norm_data;
long size;

af::array r_image;
af::array image;
af::array amplitude_condition;


Reconstruction::Reconstruction(af::array image_data, af::array guess, const char* config_file)
{
    params = new Params(config_file);
    state = new State(params);
    data = image_data;
    r_image = guess;
    Init();
}

void Reconstruction::Init()
{
    norm_data = GetNorm(data);
    amplitude_condition = operator>(params->GetAmpThreshold(), data);
    size = data.elements();
    
    // multiply the image by first element of data array and the norm

    af::array first_array = data(0);
    if (data.type() == c32)
    {
        float *host_first_data = real(first_array).host<float>();
        float first = host_first_data[0];
        delete [] host_first_data;
        if (first != 0)
        {
            r_image *= first * GetNorm(r_image);
        }
    }
    else // type is c64
    {
        d_type *host_first_data = real(first_array).host<d_type>();
        d_type first = host_first_data[0];
        delete [] host_first_data;
        if (first != 0)
        {
            r_image *= first * GetNorm(r_image);
        }
    }

    // initialize other components
    state->Init(data.dims());
}

void Reconstruction::Iterate()
{
    while (Next())
    {
        continue;
    }
}

bool Reconstruction::Next()
{
    bool ret = state->Next(data);

    if (ret)
    {
        if (state->GetCurrentAlg() == ALGORITHM_ER)
        {
            Er();
        }
        else
        {
            Hio();
        }
    }
    
    return ret;
}

void Reconstruction::Er()
{
    CommonErHio();
    d_type norm_r_image = GetNorm(r_image);
    r_image *= state->GetSupport();
    
    d_type norm_r_image_with_support = GetNorm(r_image);
    
    d_type ratio = sqrt(norm_r_image/norm_r_image_with_support);
    r_image *= ratio;
    
}

void Reconstruction::Hio()
{
    af::array prev_r_image = r_image;
    CommonErHio();
    
    // find phase
    d_type norm_r_image = GetNorm(r_image);
    
    //calculate phase
    af::array phase = atan2(imag(r_image), real(r_image));
    af::array phase_condition = operator>(params->GetPhaseMin(), phase) && operator<(params->GetPhaseMax(), phase) && (state->GetSupport() == 1);
    replace(r_image, phase_condition, (prev_r_image - r_image * params->GetBeta()));
    
    d_type norm_r_image_with_support = GetNorm(r_image);
    
    d_type ratio = sqrt(norm_r_image/norm_r_image_with_support);
    r_image *= ratio;
}

void Reconstruction::CommonErHio()
{
    image = ifft3(r_image)*size;
    
    if (state->IsConvolve())
    {
        d_type ratio = Convolve();
        replace(image, amplitude_condition, image * ratio);
    }
    else
    {
        state->RecordError(sum<d_type>(pow( (abs(image)-abs(data)) ,2))/norm_data);
        af::array good = data * image / abs(image);
        // need to check timing of the expressions below.
        // notice that the top one does not work for c64
        //af::replace(image, amplitude_condition, data * exp(complex(0, arg(image))));
        af::replace(image, amplitude_condition, data * image / (abs(image) + .0001));
    }
    if (params->IsAmpThresholdFillZeros())
    {
        replace(image, ! amplitude_condition, 0);
    }
    r_image = fft3(image)/size;

}

d_type Reconstruction::Convolve()
{
    //get a 3D subarray from image
    // sets error at the end
    // returns ratio
    return 0.0;
}

d_type Reconstruction::GetNorm(af::array arr)
{
    return sum<d_type>(pow(abs(arr), 2));
}

af::array Reconstruction::GetImage()
{
    return image;
}

std::vector<d_type> Reconstruction::GetErrors()
{
    return state->GetErrors();
}



