//
//  support.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#include "stdio.h"
#include "support.hpp"
#include "parameters.hpp"
#include "util.hpp"


Support::Support(const dim4 data_dim, std::vector<int> support_area, float th, bool threshold_adjust, int sgma, std::vector<int> support_triggers, int alg)
{
    threshold = th;
    threshold_adjust = threshold_adjust;
    sigma = sgma;
    triggers = support_triggers;
    algorithm = alg;
    af::array ones = constant(1, Utils::Int2Dim4(support_area), u32);
    support_array = Utils::PadAround(ones, data_dim, 0);
    
    printf("support sum %i\n", sum<int>(support_array));

    if (alg == ALGORITHM_GAUSS)
    {
        int alpha = 1;
        //distribution = InitDistribution(data_dim, sigma, alpha);
        d_type *sigmas = new d_type[nD];
        for (int i=0; i<nD; i++)
        {
            sigmas[i] = data_dim[i]/(2.0*af::Pi*sigma);
            //sigmas[i] = sigma;
        } 
        printf("calculated sigma %f\n", sigmas[0]);
        //distribution = Utils::ReverseGaussDistribution(data_dim, sigmas, alpha);
        distribution = Utils::GaussDistribution(data_dim, sigmas, alpha);
    }
}

void Support::Update(const af::array ds_image_abs)
{
    printf("updating support\n");
    af::array convag = GaussConvFft(ds_image_abs);
    d_type max_convag = af::max<d_type>(convag);
    convag = convag/max_convag;
    printf("convag sum max %f \n", sum<d_type>(convag));
    support_array = (convag >= threshold);
    
// if the support is too small, adjust threshold
//    if (threshold_adjust)
//    {        
//        dim4 dims = ds_image.dims();
//        float min_support_norm = .01 * int(dims[0])*int(dims[1])*int(dims[2]);
//        printf("min support norm %f\n", min_support_norm);
//        float temp_threshold = threshold;
//        while (sum<d_type>(pow(abs(support_array), 2)) < min_support_norm )
//        {
//            temp_threshold = temp_threshold/10;
//            support_array = (convag >= (temp_threshold * max_convag));
//            printf("in while loop support sum %f\n", sum<d_type>(support_array));
//        }
//    }
    printf("support sum %f\n", sum<d_type>(support_array));
}

std::vector<int> Support::GetTriggers()
{
    return triggers;
}

int Support::GetTriggerAlgorithm()
{
    return algorithm;
}

int Support::GetSigma()
{
    return sigma;
}

float Support::GetThreshold()
{
    return threshold;
}

af::array Support::GetSupportArray(bool twin)
{
    if (twin)
    {
        dim4 dims = support_array.dims();
        af::array temp = constant(0, dims, u32);
        temp( af::seq(0, dims[0]/2-1), af::seq(0, dims[1]/2-1), span, span) = 1;
        return support_array * temp;
    }
    else
    {
        return support_array;
    }
}

af::array Support::GaussConvFft(af::array ds_image_abs)
{
    d_type image_sum = sum<d_type>(ds_image_abs);
    af::array shifted = Utils::ifftshift(ds_image_abs);
    af::array rs_amplitudes = Utils::fft(shifted);
    af::array rs_amplitudes_cent = Utils::ifftshift(rs_amplitudes);
    
    af::array amp_dist = rs_amplitudes_cent * distribution;
    shifted = Utils::ifftshift(amp_dist);
    af::array convag_compl = Utils::ifft(shifted);
    af::array convag = (Utils::ifftshift(convag_compl));
    convag = real(convag);
    convag(convag < 0) = 0;
    d_type correction = image_sum/sum<d_type>(convag);
    convag *= correction;
    return convag;
}

//af::array Support::GaussConvFft(af::array ds_image_abs)
//{
// 
//    d_type image_sum = sum<d_type>(ds_image_abs);
//    printf("abs image sum %f\n", image_sum);
//    af::array rs_amplitudes = Utils::fft(ds_image_abs);
//    dim4 dims = rs_amplitudes.dims();
//    af::shift(rs_amplitudes, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
//    af::array amp_distrib = Utils::ifft(rs_amplitudes * distribution);
//    af::shift(amp_distrib, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
//    af::array convag = real(amp_distrib);
//    convag(convag < 0) = 0;
//    d_type correction = image_sum/sum<d_type>(convag);
//    convag *= correction;
//    return convag;
//}


