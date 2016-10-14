//
//  Parameters.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#include "Parameters.hpp"
#include "iostream"
#include "libconfig.h++"

// an array holding numbers of algoritms iterations, starting with ER algorithm.
std::vector<int> algorithm_sequence;
std::vector<int> roi;

// amplitude threshold
// for HIO: if data > threshold: replace guess by data * guess/abs(guess),
// for ER: 1.if data > threshold: replace guess by data * guess/abs(guess), 2. replace as 1., and set the rest to 0
d_type amp_threshold;
bool amp_threshold_fill_zeros;

d_type phase_min = 120;
d_type phase_max = 10;
float beta = .9;

// support
int support_update_step = 5;
float support_threshold;
int support_type;
bool d_type_precision;

using namespace libconfig;

Params::Params(const char* config_file)
{
    Config cfg;
    
    // Read the file. If there is an error, report.
    try
    {
        cfg.readFile(config_file);
    }
    catch(const FileIOException &fioex)
    {
        printf("file I/O exception");
    }
    catch(const ParseException &pex)
    {
        printf("parsing exception");
    }
    
    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["algorithm_sequence"];
        int count = tmp.getLength();
        
        for (int i = 0; i < count; ++i)
        {
            algorithm_sequence.push_back(tmp[i]);
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'algorithm_sequence' setting in configuration file.");
    }
    
    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["roi"];
        int count = tmp.getLength();
        
        for (int i = 0; i < count; ++i)
        {
            roi.push_back(tmp[i]);
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'roi' setting in configuration file.");
    }
    
    try
    {
        amp_threshold = cfg.lookup("amp_threshold");
    }
    catch(const SettingNotFoundException &nfex)
    {
        printf("No 'amp_threshold' setting in configuration file.");
    }

    try {
        amp_threshold_fill_zeros = cfg.lookup("amp_threshold_fill_zeros");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'amp_threshold_fill_zeros' setting in configuration file.");
    }
    
    try {
        phase_min = cfg.lookup("phase_min");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'phase_min' setting in configuration file.");
    }

    try {
        phase_max = cfg.lookup("phase_max");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'phase_max' setting in configuration file.");
    }

    try
    {
        beta = cfg.lookup("beta");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'beta' setting in configuration file.");
    }

    try
    {
        support_update_step = cfg.lookup("support_update_step");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'support_update_step' setting in configuration file.");
    }

    try
    {
        support_threshold = cfg.lookup("support_threshold");
    } catch (const SettingNotFoundException &nfex)
    {
        printf("No 'support_threshold' setting in configuration file.");
    }

    try
    {
        support_type = cfg.lookup("support_type");
    } catch (const SettingNotFoundException &nfex) {
        printf("No 'support_type' setting in configuration file.");
    }
    
}

int Params::GetIterationsNumber()
{
    int sum = 0;
    for (int i = 0; i < algorithm_sequence.size(); i++)
    {
        sum += algorithm_sequence[i];
    }
    return sum;
}

std::vector<int> Params::GetAlgorithmSequence()
{
    return algorithm_sequence;
}

int Params::GetSuportUpdateStep()
{
    return support_update_step;
}

d_type Params::GetAmpThreshold()
{
    return amp_threshold;
}

bool Params::IsAmpThresholdFillZeros()
{
    return amp_threshold_fill_zeros;
}

d_type Params::GetPhaseMin()
{
    return phase_min;
}

d_type Params::GetPhaseMax()
{
    return phase_max;
}

float Params::GetBeta()
{
    return beta;
}

std::vector<int> Params::GetRoi()
{
    return roi;
}


