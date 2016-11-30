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
#include "map"
#include "parameters.hpp"
#include "state.hpp"
#include "common.h"


af::array data;
d_type norm_data;
long size;

af::array ds_image;
af::array rs_amplitudes;
af::array amplitude_condition;
af::array averages;
af::array kernel;

//typedef void (Reconstruction::*func)(void);
//std::map<int, func> func_map;

std::vector<int> algorithm_sequance;
std::vector<func> func_sequance;

Reconstruction::Reconstruction(af::array image_data, af::array guess, const char* config_file)
{
    params = new Params(config_file);
    state = new State(params);
    data = image_data;
    ds_image = guess;
}

void Reconstruction::Init()
{
    norm_data = GetNorm(data);
    amplitude_condition = operator>(params->GetAmpThreshold(), data);
    size = data.elements();
    
    // multiply the rs_amplitudes by first element of data array and the norm

    af::array first_array = data(0);
    d_type *host_first_data = real(first_array).host<d_type>();
    d_type first = host_first_data[0];
    delete [] host_first_data;
    if (first != 0)
    {
        ds_image *= first * GetNorm(ds_image);
    }

    averages = constant(0.0, data.dims());
    InitKernel();
    InitFunctionMap();    

    algorithm_sequance = params->GetAlgorithmSequence();
    for (int i = 0; i < algorithm_sequance.size(); i++)
    {
        func_sequance.push_back(func_map[algorithm_sequance[i]]);
    }

    // initialize other components
    state->Init(data.dims());
}

void Reconstruction::InitKernel()
{
    // TODO the kernel size will be read from configuration file, (is it roi?)
    kernel = data(seq(0, 32), seq(0, 32), seq(0,32));
    kernel = pow(abs(kernel), 2);
}

void Reconstruction::InitFunctionMap()
{
    // create map mapping algorithm name to function pointer
    func_map.insert(std::pair<int,func>(0, &Reconstruction::Er));
    func_map.insert(std::pair<int,func>(1, &Reconstruction::Hio));    
}

void Reconstruction::Iterate()
{
    while (state->Next())
    {
        int current_iteration = state->GetCurrentIteration();
        printf("current iter %i", current_iteration);
        (*this.*func_sequance[current_iteration])();
        printf("did iter %i", current_iteration);
    }
}
/*
bool Reconstruction::Next()
{   
    if (state->Next())
    {
        int current_iteration = state->GetCurrentIteration();
        printf("current iter %i", current_iteration);
        (*this.*func_sequance[current_iteration])();
        printf("did iter %i", current_iteration);
        return true;
    }

    return false;
}
*/
void Reconstruction::Er()
{
    printf("er\n");
    ModulusProjection();
    d_type norm_ds_image = GetNorm(ds_image);
    ds_image *= state->GetSupport();
    
    d_type norm_ds_image_with_support = GetNorm(ds_image);
    
    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    ds_image *= ratio;
    
}

void Reconstruction::Hio()
{
    printf("hio\n");
    af::array prev_ds_image = ds_image;
    ModulusProjection();
    
    // find phase
    d_type norm_ds_image = GetNorm(ds_image);
    
    //calculate phase
    af::array phase = atan2(imag(ds_image), real(ds_image));
    af::array phase_condition = operator>(params->GetPhaseMin(), phase) && operator<(params->GetPhaseMax(), phase) && (state->GetSupport() == 1);
    replace(ds_image, phase_condition, (prev_ds_image - ds_image * params->GetBeta()));
    
    d_type norm_ds_image_with_support = GetNorm(ds_image);
    
    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    ds_image *= ratio;
    printf("did hio\n");
}

void Reconstruction::ModulusProjection()
{
    rs_amplitudes = ifft3(ds_image)*size;
    
    if (state->IsConvolve())
    {
        ds_image = Convolve();
    }

    state->RecordError(sum<d_type>(pow( (abs(rs_amplitudes)-abs(data)) ,2))/norm_data);
    af::array good = data * rs_amplitudes / abs(rs_amplitudes);
    // need to check timing of the expressions below.
    // notice that the top one does not work for c64
    //af::replace(rs_amplitudes, amplitude_condition, data * exp(complex(0, arg(rs_amplitudes))));
    af::replace(rs_amplitudes, amplitude_condition, data * rs_amplitudes / (abs(rs_amplitudes) + .0001));

    if (params->IsAmpThresholdFillZeros())
    {
        replace(rs_amplitudes, ! amplitude_condition, 0);
    }
    ds_image = fft3(rs_amplitudes)/size;

    Average();
}

af::array Reconstruction::Convolve()
{
    return af::convolve(ds_image, kernel);
}

void Reconstruction::Average()
{
    int averaging_iter = state->GetAveragingIteration();
    if (averaging_iter > 0)
    {
        averages = averages * (averaging_iter - 1)/averaging_iter + abs(ds_image)/averaging_iter;
        ds_image = ds_image * averages;
    }
    else if (averaging_iter == 0)
    { 
        averages = abs(ds_image);
    }


/*    if (averaging_iter < 0)
    {
        return;
    }

    d_type *amplitudes = abs(ds_image).host<d_type>();
    std::vector<d_type> v(amplitudes, amplitudes + ds_image.elements());
    if (averaging_iter > 0)
    {
        for (int i = 0; i < aver_v.size(); i++)
        {
            aver_v[i] = aver_v[i] * (averaging_iter - 1)/averaging_iter + v[i]/averaging_iter;
        }
        af::array aver_a(ds_image.dims(0), ds_image.dims(1), ds_image.dims(2), &aver_v[0]);
        ds_image = ds_image *aver_a;

    }
    else if (averaging_iter == 0)
    {
        aver_v = v;
    }

    delete [] amplitudes;
*/
    
}

d_type Reconstruction::GetNorm(af::array arr)
{
    return sum<d_type>(pow(abs(arr), 2));
}

af::array Reconstruction::GetImage()
{
    return ds_image;
}

std::vector<d_type> Reconstruction::GetErrors()
{
    return state->GetErrors();
}



