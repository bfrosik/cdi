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
#include "support.hpp"
#include "pcdi.hpp"
#include "state.hpp"
#include "common.h"
#include "algorithm.hpp"
#include "util.hpp"

af::array data;
d_type norm_data;
long data_size;
int current_iteration;

af::array ds_image;
af::array prev_ds_image;
af::array rs_amplitudes;
af::array amplitude_condition;
std::vector<d_type> aver_v;
af::array kernel;


Reconstruction::Reconstruction(af::array image_data, af::array guess, const char* config_file)
{
    data = image_data;
    ds_image = guess;
    params = new Params(config_file, data.dims());
    state = new State(params);
}

void Reconstruction::Init()
{
    //af_print(data(seq(0,5), seq(0,5), seq(0,5)));
    norm_data = GetNorm(data);
    printf("norm_data %fl\n", norm_data);
    amplitude_condition = data > params->GetAmpThreshold();
    data_size = data.elements();
    
    // multiply the rs_amplitudes by first element of data array and the norm

    af::array first_array = data(0);
    d_type *host_first_data = real(first_array).host<d_type>();
    d_type first = host_first_data[0];
    printf("first %fl\n", first);
    delete [] host_first_data;
    if (first != 0)
    {
        ds_image *= first * GetNorm(ds_image);
    }

    //printf("gues norm %lf\n", GetNorm(ds_image));
    //af_print(ds_image(seq(0,5), seq(0,5), seq(0,5)));

    // initialize other components
    state->Init();
    support = params->GetSupport();
    partialCoherence = params->GetPartialCoherence();
}


void Reconstruction::Iterate()
{
    while (state->Next())
    {
        current_iteration = state->GetCurrentIteration();
        Algorithm * alg  = state->GetCurrentAlg();
        alg->RunAlgorithm(this);

        if (state->IsUpdateSupport())
        {
            support->Update();
        }

        Average();
    }
    if (aver_v.size() > 0)
    {
        printf("averaging\n");
        af::array aver_a(ds_image.dims(0), ds_image.dims(1), ds_image.dims(2), &aver_v[0]);
        ds_image *= GetRatio(abs(ds_image), abs(aver_a));
        ds_image *= support->GetSupportArray();
    }

    af_print(ds_image(seq(0,5), seq(0,5), seq(0,5)));
}

void Reconstruction::ModulusProjection()
{
    printf("mod proj\n");
    prev_ds_image = ds_image;
    //af_print(ds_image(seq(0,5), seq(0,5), seq(0,5)));
    rs_amplitudes = ifft3(ds_image)*data_size;
    //af_print(rs_amplitudes(seq(0,5), seq(0,5), seq(0,5)));
    af::array rs_amplitudes_abs = abs(rs_amplitudes);
    if (partialCoherence != NULL)
    {
        if (current_iteration >= partialCoherence->GetTriggers()[0])
        {
            rs_amplitudes_abs = partialCoherence->ApplyPartialCoherence(abs(rs_amplitudes), abs(data), current_iteration);
        }
        partialCoherence->SetPrevious(abs(rs_amplitudes));
    }

    AmplitudeThreshold();
    
    // The rs_amplitudes_abs is impacted by pcdi, if configured
    rs_amplitudes *= GetRatio(abs(data), rs_amplitudes_abs);
    printf("3rs_amplitude norm %fl\n", GetNorm(rs_amplitudes));

    state->RecordError(GetNorm(abs(rs_amplitudes)-abs(data))/norm_data);

    ds_image = fft3(rs_amplitudes)/data_size;

    
    printf("ds_image norm %fl\n", GetNorm(ds_image));

}

void Reconstruction::ModulusConstrainEr()
{
    printf("er\n");
    ds_image *= support->GetSupportArray();
}

void Reconstruction::ModulusConstrainErNorm()
{
    printf("er_norm\n");
    d_type norm_ds_image = GetNorm(ds_image);
    ds_image *= support->GetSupportArray();

    d_type norm_ds_image_with_support = GetNorm(ds_image);

    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    printf("ratio %fl\n", ratio);
    ds_image *= ratio;
}

void Reconstruction::ModulusConstrainHio()
{
    printf("hio\n");
    printf("ds_image norm %fl\n",GetNorm(ds_image));
    ds_image = ds_image*support->GetSupportArray() + (1 - support->GetSupportArray())*(prev_ds_image - ds_image * params->GetBeta());
    printf("ds_image norm %fl\n",GetNorm(ds_image));
}

void Reconstruction::ModulusConstrainHioNorm()
{
    printf("hio_norm\n");
    // find phase
    //af_print(ds_image(seq(0,5), seq(0,5), seq(0,5)));
    d_type norm_ds_image = GetNorm(ds_image);
    printf("norm_ds_image %fl\n", norm_ds_image);

    //calculate phase
    af::array phase = atan2(imag(ds_image), real(ds_image));
    // set to true (1) elements that are greater than phase min and less than phase max, and support is 1
    af::array phase_condition = (phase < params->GetPhaseMin()) || (phase > params->GetPhaseMax()) || (support->GetSupportArray() == 0);
    // replace the elements that above condition is 1 with prev_ds_image - ds_image * params->GetBeta()
    replace(ds_image, phase_condition, (prev_ds_image - ds_image * params->GetBeta()));

    d_type norm_ds_image_with_support = GetNorm(ds_image);
    printf("norm_ds_image_with_support %fl\n", norm_ds_image_with_support);

    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    printf("ratio %fl\n", ratio);
    ds_image *= ratio;

}


void Reconstruction::Average()
{
    if (state->GetAveragingIteration() == 0)
    {
        printf("average\n");
        int aver_num = params->GetAvgIterations();
        d_type *amplitudes = abs(ds_image).host<d_type>();
        std::vector<d_type> v(amplitudes, amplitudes + ds_image.elements());
        for (int i = 0; i < aver_v.size(); i++)
        {
            aver_v[i] = aver_v[i] + v[i]/aver_num;
        }

        delete [] amplitudes;
    }
}

void Reconstruction::AmplitudeThreshold()
{
    af::replace(rs_amplitudes, amplitude_condition, data * exp(complex(0, arg(rs_amplitudes))));
    printf("1rs_amplitude norm %fl\n", GetNorm(rs_amplitudes));
    if (params->IsAmpThresholdFillZeros())
    {
        rs_amplitudes *= amplitude_condition;
    }
    printf("2rs_amplitude norm %fl\n", GetNorm(rs_amplitudes));
}   

af::array Reconstruction::GetRatio(af::array ar, af::array correction)
{
    // ar(ar == 0.0) = 1.0;
    // return correction/ar;
    correction(correction == 0.0) = ar(correction == 0.0);
    correction(ar == 0.0) = 1.0;
    return ar/correction;
}

d_type Reconstruction::GetNorm(af::array arr)
{
    return sum<d_type>(pow(abs(arr), 2));
}

int Reconstruction::GetCurrentIteration()
{
    return state->GetCurrentIteration();
}

af::array Reconstruction::GetImage()
{
    return ds_image.T();
}

std::vector<d_type> Reconstruction::GetErrors()
{
    return state->GetErrors();
}



