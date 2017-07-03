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
int current_iteration;

af::array ds_image;
af::array prev_ds_image;
//af::array amplitude_condition;
std::vector<d_type> aver_v;
//af::array kernel;


Reconstruction::Reconstruction(af::array image_data, af::array guess, const char* config_file)
{
    data = image_data;
    ds_image = guess;
    params = new Params(config_file, data.dims());
    state = new State(params);
}

void Reconstruction::Init()
{
    // initialize other components
    state->Init();
    support = params->GetSupport();
    partialCoherence = params->GetPartialCoherence();
    //amplitude_condition = data > params->GetAmpThreshold()
    
    // apply twin if set
    if (params->GetTwin() >= 0)
    {
        ds_image(seq(data.dims()[0]/2, data.dims()[0]-1), seq(data.dims()[1]/2, data.dims()[1]-1)) = 0;
    }

    norm_data = GetNorm(data);
    // multiply the rs_amplitudes by max element of data array and the norm
    d_type max_data = af::max<d_type>(data);
    ds_image *= max_data * GetNorm(ds_image);

}


void Reconstruction::Iterate()
{
    while (state->Next())
    {
        if (state->IsUpdateSupport())
        {
            support->Update(ds_image);
        }

        current_iteration = state->GetCurrentIteration();
        Algorithm * alg  = state->GetCurrentAlg();
        alg->RunAlgorithm(this);

       // Average();
    }
/*    if (aver_v.size() > 0)
    {
        printf("averaging\n");
        af::array aver_a(ds_image.dims(0), ds_image.dims(1), ds_image.dims(2), &aver_v[0]);
        //ds_image *= GetRatio(abs(ds_image), abs(aver_a));
        ds_image *= support->GetSupportArray();
    }*/
}

void Reconstruction::ModulusProjection()
{
    printf("------------------current iteration %i -----------------\n", current_iteration);
    prev_ds_image = ds_image;
    af::array rs_amplitudes = ifft3(ds_image);
    state->RecordError( GetNorm(abs(rs_amplitudes)(rs_amplitudes > 0)-abs(data)(rs_amplitudes > 0))/norm_data );
    printf("data norm, ampl norm before ratio %fl %fl\n", GetNorm(data), GetNorm(rs_amplitudes));

    if (partialCoherence != NULL)
    {
        if (current_iteration >= partialCoherence->GetTriggers()[0])
        {
            //rs_amplitudes_abs = partialCoherence->ApplyPartialCoherence(abs(rs_amplitudes), abs(data), current_iteration);
        }
        partialCoherence->SetPrevious(abs(rs_amplitudes));
    }

    af::array temp = af::complex(0, af::arg(rs_amplitudes));
    rs_amplitudes = data * exp(temp);
    printf("ampl norm after ratio %fl\n", GetNorm(rs_amplitudes));
    
    ds_image = fft3(rs_amplitudes);

}

void Reconstruction::ModulusConstrainEr()
{
    printf("er\n");
    printf("image norm before support %fl\n", GetNorm(ds_image));    
    ds_image *= support->GetSupportArray();
    if (state->IsApplyTwin())
    {
        ds_image(seq(data.dims()[0]/2, data.dims()[0]-1), seq(data.dims()[1]/2, data.dims()[1]-1)) = 0;
    }

    printf("image norm after support %fl\n", GetNorm(ds_image));
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
    printf("image norm before support %fl\n",GetNorm(ds_image));
    ds_image(support->GetSupportArray() == 0) = (prev_ds_image - ds_image * params->GetBeta())(support->GetSupportArray() == 0);
    if (state->IsApplyTwin())
    {
        ds_image(seq(data.dims()[0]/2, data.dims()[0]-1), seq(data.dims()[1]/2, data.dims()[1]-1)) = (prev_ds_image - ds_image * params->GetBeta())(seq(data.dims()[0]/2, data.dims()[0]-1), seq(data.dims()[1]/2, data.dims()[1]-1));
    }
    printf("image norm after support %fl\n",GetNorm(ds_image));
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
/*    af::replace(rs_amplitudes, amplitude_condition, data * exp(complex(0, arg(rs_amplitudes))));
    printf("1rs_amplitude norm %fl\n", GetNorm(rs_amplitudes));
    if (params->IsAmpThresholdFillZeros())
    {
        rs_amplitudes *= amplitude_condition;
    }
    printf("2rs_amplitude norm %fl\n", GetNorm(rs_amplitudes));*/
}   

double Reconstruction::GetNorm(af::array arr)
{
    return sum<d_type>(pow(abs(arr), 2));
}

int Reconstruction::GetCurrentIteration()
{
    return state->GetCurrentIteration();
}

af::array Reconstruction::GetImage()
{
    return ds_image;
}

std::vector<d_type> Reconstruction::GetErrors()
{
    return state->GetErrors();
}




