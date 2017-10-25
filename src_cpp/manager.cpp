/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/

#include "typeinfo"
#include "arrayfire.h"
#include "worker.hpp"
#include "manager.hpp"
#include "util.hpp"


using namespace af;

void Manager::StartCalc(std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> dim, const std::string & config)
{
    dim4 af_dims = Utils::Int2Dim4(dim);
    af::array real_d(af_dims, &data_buffer_r[0]);
    //saving abs(data)
    af::array data = abs(real_d);
    

    af::array real_g(af_dims, &guess_buffer_r[0]);
    af::array imag_g(af_dims, &guess_buffer_i[0]);
    af::array guess = complex(real_g, imag_g);
       
    Reconstruction reconstruction(data, guess, config.c_str());
    reconstruction.Init();
    rec = &reconstruction;
    timer::start();

    reconstruction.Iterate();	

    printf("iterate function took %g seconds\n", timer::stop());
}

void Manager::StartCalc(std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config)
{
    StartCalc(data_buffer_r, dim, config, 1);
}

void Manager::StartCalc(std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config, int nu_threads)
{
    af::array real_d(Utils::Int2Dim4(dim), &data_buffer_r[0]);
    //saving abs(data)
    af::array data = abs(real_d);


    af::randomEngine r(AF_RANDOM_ENGINE_MERSENNE, (uint)time(0));
    d_type test1 = 0;
    double test2 = 0;
    af::array guess;
    if (typeid(test1) == typeid(test2))
    {
        guess = randu(data.dims(), c64, r);
    }
    else
    {
        guess = randu(data.dims(), c32, r);
    }
    Reconstruction reconstruction(data, guess, config.c_str());
    reconstruction.Init();
    rec = &reconstruction;

    timer::start();
    reconstruction.Iterate();
    printf("iterate function took %g seconds\n", timer::stop());
	
}

std::vector<d_type> Manager::GetImageR()
{
    af::array image = rec->GetImage();
    
    d_type *image_r = real(image).host<d_type>();
    std::vector<d_type> v(image_r, image_r + image.elements());

    delete [] image_r;
    return v;
}

std::vector<d_type> Manager::GetImageI()
{
    af::array image = rec->GetImage();

    d_type *image_i = imag(image).host<d_type>();
    std::vector<d_type> v(image_i, image_i + image.elements());

    delete [] image_i;
    return v;
}

std::vector<d_type> Manager::GetErrors()
{
    return rec->GetErrors();
}

std::vector<float> Manager::GetSupportV()
{
    return rec->GetSupportVector();
}

std::vector<d_type> Manager::GetCoherenceV()
{
    return rec->GetCoherenceVector();
}


