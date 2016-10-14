//
//  Reconstruction.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/12/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//


#include "sstream"
#include "arrayfire.h"
#include "RecWrap.hpp"
#include "Reconstruction.hpp"


using namespace af;

void RecWrap::StartCalc(std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> dim, const std::string & config)
{
    af::array real_d(dim[0], dim[1], dim[2], &data_buffer_r[0]);
    af::array data = complex(real_d, 0.0);

    af::array real_g(dim[0], dim[1], dim[2], &guess_buffer_r[0]);
    af::array imag_g(dim[0], dim[1], dim[2], &guess_buffer_i[0]);
    af::array guess = complex(real_g, imag_g);
       
    Reconstruction reconstruction(data, guess, config.c_str());
    rec = &reconstruction;

    timer::start();
    reconstruction.Iterate();
    printf("iterate function took %g seconds\n", timer::stop());
	
}

void RecWrap::StartCalcGenGuess(std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config)
{
    af::array real_d(dim[0], dim[1], dim[2], &data_buffer_r[0]);
    af::array data = complex(real_d, 0.0);

    af::randomEngine r(AF_RANDOM_ENGINE_MERSENNE, (uint)time(0));
    af::array guess = randu(data.dims(), c32, r);
     
    Reconstruction reconstruction(data, guess, config.c_str());
    rec = &reconstruction;

    timer::start();
    reconstruction.Iterate();
    printf("iterate function took %g seconds\n", timer::stop());
	
}

std::vector<d_type> RecWrap::GetImageR()
{
    af::array image = rec->GetImage();

    d_type *image_r = real(image).host<d_type>();
    std::vector<d_type> v(image_r, image_r + image.elements());

    delete [] image_r;
    return v;
}

std::vector<d_type> RecWrap::GetImageI()
{
    af::array image = rec->GetImage();

    d_type *image_i = imag(image).host<d_type>();
    std::vector<d_type> v(image_i, image_i + image.elements());

    delete [] image_i;
    return v;
}

std::vector<d_type> RecWrap::GetErrors()
{
    return rec->GetErrors();;
}





