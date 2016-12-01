//
//  state.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#include "state.hpp"
#include "parameters.hpp"
#include "vector"

// a reference to params object
Params *params;

// The variables
std::vector<d_type>  errors;
af::array support;

bool run_convolution = false;
int averaging_iter = 0;

int current_iter = -1;
int current_alg = -1;
int switch_num = 0;
int total_iter_num = 0;

State::State(Params* parameters)
{
    params = parameters;
}

void State::Init(const dim4 data_dim)
{
    current_alg = params->GetAlgSwitches()[0].algorithm;
    total_iter_num = params->GetIterationsNumber();

    // create initial support
    support = constant(0, data_dim, u32);
    std::vector<int> roi = params->GetRoi();
    support( seq(0, roi[0]-1), seq(0, roi[1]-1), seq(0, roi[2]-1) ) = 1;
}

State::~State()
{
}

int State::GetCurrentAlg()
{
    return current_alg;
}

void State::RecordError(d_type error)
{
    errors.push_back(error);
}

int State::GetCurrentIteration()
{
    return current_iter;
}

bool State::IsConvolve()
{
    return run_convolution;
}

int State::GetAveragingIteration()
{
    return (current_iter - params->GetIterateAvgStart() );
}

int State::Next()
{
    if (current_iter++ == total_iter_num - 1)
    {
        return false;
    }

    // figure out current alg
    if (params->GetAlgSwitches()[switch_num].iterations == current_iter)
    // switch to the next algorithm
    // set to do convolution on switch
    {
        switch_num++;
        current_alg = params->GetAlgSwitches()[switch_num].algorithm;
        run_convolution = true;
    }
    else
    {
        run_convolution = false;
    }
    
    // figure out support update
    if (current_iter % params->GetSuportUpdateStep() == 0 && current_iter != 0)
    {
        //UpdateSupport();
    }
    
    return true;
}

void State::UpdateSupport()
{
    
}

af::array State::GetSupport()
{
    return support;
}

std::vector<d_type>  State::GetErrors()
{
    return errors;
}


