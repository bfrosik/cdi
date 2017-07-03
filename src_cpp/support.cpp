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


Support::Support(const dim4 data_dim, int * support_area, float th, bool threshold_adjust, int sgma, std::vector<int> support_triggers, int alg)
{
    threshold = th;
    threshold_adjust = threshold_adjust;
    sigma = sgma;
    triggers = support_triggers;
    algorithm = alg;
    support_array = constant(0, data_dim, u32);
    
    // center support
    int x1 = (data_dim[0] - support_area[0])/2;
    int x2 = (data_dim[0] + support_area[0])/2;
    int y1 = (data_dim[1] - support_area[1])/2;
    int y2 = (data_dim[1] + support_area[1])/2;
    int z1 = (data_dim[2] - support_area[2])/2;
    int z2 = (data_dim[2] + support_area[2])/2;
    support_array( seq(x1, x2), seq(y1, y2), seq(z1, z2) ) = 1;
    printf("support bounds %i %i %i %i %i %i\n", x1, x2, y1, y2, z1, z2);

    if (alg == ALGORITHM_GAUSS)
    {
        int alpha = 1;
        distribution = InitDistribution(data_dim, sigma, alpha);
        printf("distribution norm %f\n", sum<d_type>(pow(abs(distribution), 2)));
    }
}

void Support::Update(const af::array ds_image)
{
    af::array convag = GaussConvFft(abs(ds_image));
    d_type max_convag = af::max<d_type>(convag);
    convag = convag/max_convag;
    support_array = convag >= (threshold * max_convag);
    // if the support is too small, adjust threshold
    if (threshold_adjust)
    {
        dim4 dims = ds_image.dims();
        int min_support_norm = .01 * int(dims[0])*int(dims[1])*int(dims[2]);
        while (sum<d_type>(pow(abs(support_array), 2)) < min_support_norm )
        {
            threshold = threshold/10;
            support_array = convag >= (threshold * max_convag);
        }
    }
    printf("support norm %f\n", sum<d_type>(pow(abs(support_array), 2)));
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

af::array Support::GetSupportArray()
{
    return support_array;
}

/*
af::array Support::InitDistribution(const dim4 data_dim, int sgma, int alpha)
{
    // calculate multiplier
    double x_mult = -2 * alpha * pow(af::Pi*sgma/data_dim[0],2);
    double y_mult = -2 * alpha * pow(af::Pi*sgma/data_dim[1],2);
    double z_mult = -2 * alpha * pow(af::Pi*sgma/data_dim[2],2);

    af::array x = exp((pow(range(data_dim, 0)-data_dim[0]/2+1, 2) * x_mult));
    af::array y = exp((pow(range(data_dim, 1)-data_dim[1]/2+1, 2) * y_mult));
    af::array z = exp((pow(range(data_dim, 2)-data_dim[2]/2+1, 2) * z_mult));
    return x * y * z;
}

af::array Support::GaussConvFft(af::array ds_image)
{
    d_type image_sum = sum<d_type>(abs(ds_image));
    af::array ds_amplitudes = fft3(ds_image);
    af::dim4 dims = ds_amplitudes.dims();
    af::array ds_amplitudes_centered = Utils::CenterMax(ds_amplitudes);
    af::array convag = real(ifft3(ds_amplitudes_centered * distribution));
    //af::array convag = abs(ifft3(ds_amplitudes_centered * distribution));
    convag(convag < 0) = 0;
    convag *= image_sum/sum<d_type>(convag);
    return convag;

}
*/

af::array Support::InitDistribution(const dim4 data_dim, int sgma, int alpha)
{
    // calculate multiplier
    double x_mult = -2 * alpha * pow(af::Pi*sgma/data_dim[0],2);
    double y_mult = -2 * alpha * pow(af::Pi*sgma/data_dim[1],2);
    double z_mult = -2 * alpha * pow(af::Pi*sgma/data_dim[2],2);

    af::array x = exp(pow(data_dim[0]/2 - abs(range(data_dim, 0)-(data_dim[0]+1)/2), 2) * x_mult);
    af::array y = exp(pow(data_dim[1]/2 - abs(range(data_dim, 1)-(data_dim[1]+1)/2), 2) * y_mult);
    af::array z = exp(pow(data_dim[1]/2 - abs(range(data_dim, 2)-(data_dim[2]+1)/2), 2) * z_mult);
    return x * y * z;
}

af::array Support::GaussConvFft(af::array ds_image)
{
    d_type image_sum = sum<d_type>(abs(ds_image));
    af::array ds_amplitudes = fft3(ds_image);
    af::array convag = real(ifft3(ds_amplitudes * distribution));
    convag(convag < 0) = 0;
    convag *= image_sum/sum<d_type>(convag);
    return convag;
}


