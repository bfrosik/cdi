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

void Bridge::StartCalcWithGuess(std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> dim, const std::string & config)
{
    mgr.StartCalc(data_buffer_r, guess_buffer_r, guess_buffer_i, dim, config);
}

void Bridge::StartCalc(std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config)
{
    mgr.StartCalc(data_buffer_r, dim, config);
}

void Bridge::StartCalcMultiple(std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config, int nu_threads)
{
    mgr.StartCalc(data_buffer_r, dim, config, nu_threads);
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
    return mgr.GetErrors();;
}





