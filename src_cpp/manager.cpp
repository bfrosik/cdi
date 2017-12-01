/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "stdexcept"
#include "typeinfo"
#include "arrayfire.h"
#include "worker.hpp"
#include "manager.hpp"
#include "util.hpp"
#include "parameters.hpp"
#include "common.h"


using namespace af;

void Manager::StartCalc(std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> dim, const std::string & config)
{
    dim4 af_dims = Utils::Int2Dim4(dim);
    af::array real_d(af_dims, &data_buffer_r[0]);
    //saving abs(data)
    af::array data = abs(real_d);
    Params * params = new Params(config.c_str(), data.dims());
    

    af::array real_g(af_dims, &guess_buffer_r[0]);
    af::array imag_g(af_dims, &guess_buffer_i[0]);
    af::array guess = complex(real_g, imag_g);
       
    af::array null_array = array();
    Reconstruction reconstruction(data, guess, params, null_array, null_array);
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
    af::array data = abs(real_d);
    
    Params * params = new Params(config.c_str(), data.dims());
    
    af::array guess;
    int action = params->GetAction();
    bool cont = false;        
    if(action == ACTION_CONTINUE)
    {
        const char * continue_dir = params->GetContinueDir();
        std::string image_file = Utils::GetFullFilename(continue_dir, "image.af");
        std::string support_file = Utils::GetFullFilename(continue_dir, "support.af");
        std::string coherence_file = Utils::GetFullFilename(continue_dir, "coherence.af");
        try {
            guess = af::readArray(image_file.c_str(), "image");
            cont = true;
        } 
        catch ( const std::exception &ex)
        {
            printf("Error reading image array from %s file, generating new guess\n", image_file.c_str());
            action = ACTION_NEW_GUESS;
        }  
        
        if (cont)
        {
            af::array null_array = array();            
            af::array support_array;
            try {
                support_array = af::readArray(support_file.c_str(), "support");
            } 
            catch ( const std::exception &ex)
            {
                support_array = null_array;
            }
            
            af::array coherence_array;
            try {
                coherence_array = af::readArray(coherence_file.c_str(), "coherence");
            } 
            catch ( const std::exception &ex)
            {
                coherence_array = null_array;
            }

            Reconstruction reconstruction(data, guess, params, support_array, coherence_array);
            rec = &reconstruction;
        }
    }
    if (action == ACTION_NEW_GUESS)
    {
        af::randomEngine r(AF_RANDOM_ENGINE_MERSENNE, (uint)time(0));
        d_type test1 = 0;
        double test2 = 0;
        if (typeid(test1) == typeid(test2))
        {
            guess = randu(data.dims(), c64, r);
        }
        else
        {
            guess = randu(data.dims(), c32, r);
        }
        af::array null_array = array();
        Reconstruction reconstruction(data, guess, params, null_array, null_array);
        rec = &reconstruction;
    }

    rec->Init();
    printf("initialized\n");

    timer::start();
    rec->Iterate();
    printf("iterate function took %g seconds\n", timer::stop());
    
    if (params->IsSaveResults())
    {
        printf("save results\n");
        const char * save_dir = params->GetSaveDir();
        std::string image_file = Utils::GetFullFilename(save_dir, "image.af");
        std::string support_file = Utils::GetFullFilename(save_dir, "support.af");
        std::string coherence_file = Utils::GetFullFilename(save_dir, "coherence.af");
        
        try {
            af::saveArray("image", rec->GetImage(), image_file.c_str());
            af::saveArray("support", rec->GetSupportArray(), support_file.c_str());
            af::array coh = rec->GetCoherenceArray();
            if (!Utils::IsNullArray(coh))
            {
                af::saveArray("coherence", coh, coherence_file.c_str());
            }
        } 
        catch ( const std::exception &ex)
        {
            printf("Error writing image array to %s file\n", image_file.c_str());
        }                
    }	
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


