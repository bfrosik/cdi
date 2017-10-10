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

af::array data;   // this is abs
int num_points;
d_type norm_data;
int current_iteration;
af::array ds_image;
af::array aver;
int aver_iter;
std::vector<d_type> aver_v;
std::vector<float> support_vector;
std::vector<d_type> coherence_vector;


Reconstruction::Reconstruction(af::array image_data, af::array guess, const char* config_file)
{
    af::dim4 dims = image_data.dims();
    data = Utils::fftshift(image_data);
    //data = image_data;
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
    aver_iter = params->GetAvgIterations();
    if (aver_iter > 0)
    {
        aver = af::constant(0, data.dims(), (af_dtype) dtype_traits<d_type>::ctype);
    }
    if (partialCoherence != NULL)
    {
        partialCoherence->Init(data);
    }
    norm_data = GetNorm(data);
    num_points = data.elements();
    // multiply the rs_amplitudes by max element of data array and the norm
    d_type max_data = af::max<d_type>(data);
    ds_image *= max_data * GetNorm(ds_image);
    
    //af::array ones = constant(1, dim4(32,64,32), u32);
    //af::array temp = Utils::PadAround(ones, data.dims(), 0);
    af::array temp = support->GetSupportArray();
    ds_image  = complex(temp.as((af_dtype) dtype_traits<d_type>::ctype), 0.0).as(c64);
    printf("initial image norm %f\n", GetNorm(ds_image));

}


void Reconstruction::Iterate()
{
    while (state->Next())
    {
        if (state->IsUpdateSupport())
        {
            support->Update(abs(ds_image).copy());
        }

        current_iteration = state->GetCurrentIteration();
        Algorithm * alg  = state->GetCurrentAlg();
        alg->RunAlgorithm(this);

        Average();
    }
    printf("final image\n");

    if (aver_iter > 0)
    {
        printf("final averaging\n");
        af::array ratio = Utils::GetRatio(aver, abs(ds_image));
        ds_image *= ratio/aver_iter;                    
    }
    if (aver_v.size() > 0)
    {
        printf("final averaging\n");
        //af::array aver_a(ds_image.dims(0), ds_image.dims(1), ds_image.dims(2), &aver_v[0]);
        af::array aver_a(ds_image.dims(), &aver_v[0]);
        af::array ratio = Utils::GetRatio(aver_a, abs(ds_image));
        ds_image *= ratio/aver_iter;                    
    }
    ds_image *= support->GetSupportArray();
    VectorizeSupport(); 
    if (partialCoherence != NULL)
    {
        VectorizeCoherence();
    }
}

af::array Reconstruction::ModulusProjection()
{
    printf("------------------current iteration %i -----------------\n", current_iteration);
    af::array rs_amplitudes;
    dim4 dims = data.dims();
    if (params->IsMatlabOrder())
    {
        af::array shifted = shift(ds_image, dims[0]/2, dims[1]/2, dims[2]/2);
        rs_amplitudes = Utils::ifftshift(Utils::fft(Utils::ifftshift(ds_image)));
    }
    else
    {
        rs_amplitudes = Utils::ifft(ds_image)*num_points;
    }

    
    printf("data norm, ampl norm before ratio %fl %fl\n", GetNorm(data), GetNorm(rs_amplitudes));
    //state->RecordError( GetNorm(abs(rs_amplitudes)(rs_amplitudes > 0)-data(rs_amplitudes > 0))/norm_data );
    
    if ((partialCoherence == NULL) || (partialCoherence->GetTriggers().size() == 0))
    {
        printf("applying ratio\n");
        //rs_amplitudes = data * exp(af::complex(0, af::arg(rs_amplitudes)));
        af::array ratio = Utils::GetRatio(data, abs(rs_amplitudes));        
        rs_amplitudes *= ratio;
    }  
    else
    {
        if (current_iteration >= partialCoherence->GetTriggers()[0])
        {
            printf("coherence using lucy\n");            
            af::array abs_amplitudes = abs(rs_amplitudes).copy();
            af::array converged = partialCoherence->ApplyPartialCoherence(abs_amplitudes, current_iteration);
            af::array ratio = Utils::GetRatio(data, abs(converged));
            printf("ratio norm %f\n", GetNorm(ratio));

            rs_amplitudes *= ratio;            
        }
        else
        {
            printf("applying ratio\n");
            //rs_amplitudes = data * exp(af::complex(0, af::arg(rs_amplitudes)));
            af::array ratio = Utils::GetRatio(data, abs(rs_amplitudes));
            rs_amplitudes *= ratio;
        }
        printf("setting previous\n");
        partialCoherence->SetPrevious(abs(rs_amplitudes));
    }
    printf("ampl norm after ratio %fl\n", GetNorm(rs_amplitudes));
    
    if (params->IsMatlabOrder())
    {
        af::array temp = Utils::ifftshift((Utils::ifft(Utils::ifftshift(rs_amplitudes))));
        //return Utils::ifft(rs_amplitudes);
        return temp;
    }
    else
    {
        return Utils::fft(rs_amplitudes)/num_points;
     }

}

void Reconstruction::ModulusConstrainEr(af::array ds_image_raw)
{
    printf("er\n");
    printf("image norm before support %fl\n", GetNorm(ds_image_raw));  
    //ds_image = ds_image_raw * support->GetSupportArray(state->IsApplyTwin());
    af::array support_array = support->GetSupportArray(state->IsApplyTwin());
    ds_image = ds_image_raw * support_array;

    printf("image norm after support %fl\n", GetNorm(ds_image));
}

void Reconstruction::ModulusConstrainErNorm(af::array ds_image_raw)
{
    printf("er_norm\n");
    d_type norm_ds_image = GetNorm(ds_image_raw);
    ds_image = ds_image_raw * support->GetSupportArray();

    d_type norm_ds_image_with_support = GetNorm(ds_image);

    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    printf("ratio %fl\n", ratio);
    ds_image *= ratio;
}

void Reconstruction::ModulusConstrainHio(af::array ds_image_raw)
{
    
    printf("hio\n");
    printf("image norm before support %fl\n",GetNorm(ds_image_raw));
    //ds_image(support->GetSupportArray(state->IsApplyTwin()) == 0) = (ds_image - ds_image_raw * params->GetBeta())(support->GetSupportArray(state->IsApplyTwin()) == 0);
    af::array support_array = support->GetSupportArray(state->IsApplyTwin());
    af::array adjusted_calc_image = ds_image_raw * params->GetBeta();
    af::array combined_image = ds_image - adjusted_calc_image;
    ds_image = ds_image_raw;
    ds_image(support_array == 0) = combined_image(support_array == 0);
    printf("image norm after support %fl\n",GetNorm(ds_image));
}

void Reconstruction::ModulusConstrainHioNorm(af::array ds_image_raw)
{
    printf("hio_norm\n");
    d_type norm_ds_image = GetNorm(ds_image);
    printf("norm_ds_image %fl\n", norm_ds_image);

    //calculate phase
    af::array phase = atan2(imag(ds_image), real(ds_image));
    // set to true (1) elements that are greater than phase min and less than phase max, and support is 1
    af::array phase_condition = (phase < params->GetPhaseMin()) || (phase > params->GetPhaseMax()) || (support->GetSupportArray() == 0);
    // replace the elements that above condition is 1 with prev_ds_image - ds_image * params->GetBeta()
    //replace(ds_image, phase_condition, (prev_ds_image - ds_image * params->GetBeta()));

    d_type norm_ds_image_with_support = GetNorm(ds_image);
    printf("norm_ds_image_with_support %fl\n", norm_ds_image_with_support);

    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    printf("ratio %fl\n", ratio);
    ds_image *= ratio;

}


void Reconstruction::Average()
{
    if (state->IsAveragingIteration())
    {
        printf("average\n");
        int aver_num = params->GetAvgIterations();
        af::array abs_image = abs(ds_image).copy();
        d_type *image_v = abs_image.host<d_type>();
        std::vector<d_type> v(image_v, image_v + ds_image.elements());
        if (aver_v.size() == 0)
        {
            for (int i = 0; i < v.size(); i++)
            {
                aver_v.push_back(v[i]);
            }            
        }
        else
        {
            for (int i = 0; i < v.size(); i++)
            {
                aver_v[i] += v[i];
            }            
        }

        delete [] image_v;
    }
}

//void Reconstruction::Average()
//{
//    if (state->IsAveragingIteration())
//    {
//        printf("average, aver iter %i\n", aver_iter);
//        aver += abs(ds_image);
//    }
//}

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

void Reconstruction::VectorizeSupport()
{
    af::array a = support->GetSupportArray().as(f32);
    float *support_v = a.host<float>();
    std::vector<float> v(support_v, support_v + a.elements());
    support_vector = v;
    delete [] support_v;
 }

void Reconstruction::VectorizeCoherence()
{
    // get the partial coherence as double, so it will work for float and double data types
    af::array a = partialCoherence->GetKernelArray();
    d_type *coherence_v = a.host<d_type>();
    std::vector<d_type> v(coherence_v, coherence_v + a.elements());
    coherence_vector = v;
    delete [] coherence_v;
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

std::vector<float> Reconstruction::GetSupportVector()
{
    return support_vector;
}

std::vector<d_type> Reconstruction::GetCoherenceVector()
{
    return coherence_vector;
}

std::vector<d_type> Reconstruction::GetCoherenceVectorR()
{
    return coherence_vector;
}

std::vector<d_type> Reconstruction::GetCoherenceVectorI()
{
    return coherence_vector;
}

