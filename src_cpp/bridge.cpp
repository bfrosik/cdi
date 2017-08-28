//
//  Reconstruction.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/12/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//


#include "sstream"
#include "bridge.hpp"
#include "manager.hpp"

Manager mgr;

void Bridge::StartCalcWithGuess(std::vector<float> data_buffer_r, std::vector<float> guess_buffer_r, std::vector<float> guess_buffer_i, std::vector<int> dim, const std::string & config)
{
    std::vector<d_type> data_r(data_buffer_r.begin(), data_buffer_r.end());
    std::vector<d_type> guess_i(guess_buffer_i.begin(), guess_buffer_i.end());
    std::vector<d_type> guess_r(guess_buffer_r.begin(), guess_buffer_r.end());
    mgr.StartCalc(data_r, guess_r, guess_i, dim, config);
    //mgr.StartCalc(data_buffer_r, guess_buffer_r, guess_buffer_i, dim, config);
}

void Bridge::StartCalc(std::vector<float> data_buffer_r, std::vector<int> dim, std::string const & config)
{
    std::vector<d_type> data_r(data_buffer_r.begin(), data_buffer_r.end());
    mgr.StartCalc(data_r, dim, config);
//    mgr.StartCalc(data_buffer_r, dim, config);
}

void Bridge::StartCalcMultiple(std::vector<float> data_buffer_r, std::vector<int> dim, std::string const & config, int nu_threads)
{
    std::vector<d_type> data_r(data_buffer_r.begin(), data_buffer_r.end());
    mgr.StartCalc(data_r, dim, config, nu_threads);
//    mgr.StartCalc(data_buffer_r, dim, config, nu_threads);
}

std::vector<d_type> Bridge::GetImageR()
{
    return mgr.GetImageR();
}

std::vector<d_type> Bridge::GetImageI()
{
    return mgr.GetImageI();
}

std::vector<d_type> Bridge::GetErrors()
{
    return mgr.GetErrors();
}

std::vector<float> Bridge::GetSupportV()
{
    return mgr.GetSupportV();
}

std::vector<d_type> Bridge::GetCoherenceV()
{
    return mgr.GetCoherenceV();
}





