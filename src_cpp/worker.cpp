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
    //amplitude_condition = operator>(params->GetAmpThreshold(), data);
    amplitude_condition = data > params->GetAmpThreshold();
    data_size = data.elements();
    
    // multiply the rs_amplitudes by first element of data array and the norm

    af::array first_array = data(0);
    d_type *host_first_data = real(first_array).host<d_type>();
    d_type first = host_first_data[0];
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

//void Reconstruction::InitKernel()
//{
//    // TODO the kernel size will be read from configuration file, (is it roi?)
//    kernel = data(seq(0, 32), seq(0, 32), seq(0,32));
//    kernel = pow(abs(kernel), 2);
//}

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
}

void Reconstruction::ModulusProjection()
{
    prev_ds_image = ds_image;
    //af_print(ds_image(seq(0,5), seq(0,5), seq(0,5)));
    rs_amplitudes = ifft3(ds_image)*data_size;
    //af_print(rs_amplitudes(seq(0,5), seq(0,5), seq(0,5)));

    if (partialCoherence != NULL)
    {
        if (current_iteration >= partialCoherence->GetTriggers()[0])
        {
            af::array rs_amplitudes_adjust = partialCoherence->ApplyPartialCoherence(abs(rs_amplitudes), abs(data), this);

            rs_amplitudes_adjust(rs_amplitudes_adjust == 0) = 1.0;
            replace(rs_amplitudes_adjust, rs_amplitudes != 0, abs(data)/rs_amplitudes_adjust);
            rs_amplitudes *= rs_amplitudes_adjust;
        }
        else if (current_iteration == (partialCoherence->GetTriggers()[0]-1))
        {
            partialCoherence->Init(abs(rs_amplitudes));
        }
    }


    state->RecordError(sum<d_type>(pow( (abs(rs_amplitudes)-abs(data)) ,2))/norm_data);
    // need to check timing of the expressions below.
    // notice that the top one does not work for c64
    af::replace(rs_amplitudes, amplitude_condition, data * exp(complex(0, arg(rs_amplitudes))));
//    af::replace(rs_amplitudes, amplitude_condition, data * rs_amplitudes / (abs(rs_amplitudes) + .0001));

    if (params->IsAmpThresholdFillZeros())
    {
        replace(rs_amplitudes, ! amplitude_condition, 0);
    }
    ds_image = fft3(rs_amplitudes)/data_size;
    //af_print(ds_image(seq(0,5), seq(0,5), seq(0,5)));

}

void Reconstruction::ModulusConstrainEr()
{
    printf("er\n");
    d_type norm_ds_image = GetNorm(ds_image);
    ds_image *= support->GetSupportArray();

    d_type norm_ds_image_with_support = GetNorm(ds_image);

    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    ds_image *= ratio;
}

void Reconstruction::ModulusConstrainHio()
{
    printf("hio\n");
    // find phase
    //af_print(ds_image(seq(0,5), seq(0,5), seq(0,5)));
    d_type norm_ds_image = GetNorm(ds_image);
    printf("norm_ds_image %fl\n", norm_ds_image);

    //calculate phase
    af::array phase = atan2(imag(ds_image), real(ds_image));
    // set to true (1) elements that are greater than phase min and less than phase max, and support is 1
    af::array phase_condition = (phase > params->GetPhaseMin()) && (phase < params->GetPhaseMax()) && (support->GetSupportArray() == 1);
    // replace the elements that above condition is 1 with prev_ds_image - ds_image * params->GetBeta()
    replace(ds_image, phase_condition, (prev_ds_image - ds_image * params->GetBeta()));

    d_type norm_ds_image_with_support = GetNorm(ds_image);
    //printf("norm_ds_image_with_support %fl\n", norm_ds_image_with_support);

    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    ds_image *= ratio;
}

void Reconstruction::Average()
{
    int averaging_iter = state->GetAveragingIteration();
    if (averaging_iter < 0)
    {
        return;
    }

    printf("average\n");
    d_type *amplitudes = abs(ds_image).host<d_type>();
    std::vector<d_type> v(amplitudes, amplitudes + ds_image.elements());
    if (averaging_iter > 0)
    {
        for (int i = 0; i < aver_v.size(); i++)
        {
            aver_v[i] = aver_v[i] + v[i];
        }
    }
    else if (averaging_iter == 0)
    {
        aver_v = v;
    }

    delete [] amplitudes;
}

d_type Reconstruction::GetNorm(af::array arr)
{
    return sum<d_type>(pow(abs(arr), 2));
}

af::array Reconstruction::CalculateRatio(af::array arr1, af::array arr2)
{
    printf("calculate ratio\n");
    af::array ratio = af::constant(1.0, arr1.dims());
    printf("created array\n");
    //replace(ratio, amplitude_condition, ds_image);
    return ratio;
}

int Reconstruction::GetCurrentIteration()
{
    return state->GetCurrentIteration();
}

af::array Reconstruction::GetImage()
{
    if (aver_v.size() > 0)
    {
        af::array aver_a(ds_image.dims(0), ds_image.dims(1), ds_image.dims(2), &aver_v[0]);
        af::array ratio = (aver_a/params->GetAvgIterations())/ abs(ds_image);
        ds_image *= ratio;
    }
    return ds_image;
}

std::vector<d_type> Reconstruction::GetErrors()
{
    return state->GetErrors();
}



