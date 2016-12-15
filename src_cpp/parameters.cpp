//
//  parameters.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#include "map"
#include "algorithm"
#include "parameters.hpp"
#include "support.hpp"
#include "common.h"
#include "iostream"
#include "libconfig.h++"

using namespace libconfig;
Config cfg;

// maps algorithm name to algorithm number
std::map<std::string, int> algorithm_id_map;
// vector holding algorithm run sequence, where algorithm run is a pair of algorithm and number of iterations
std::vector<alg_switch> alg_switches;

// amplitude threshold
d_type amp_threshold;
bool amp_threshold_fill_zeros;

d_type phase_min = 120;
d_type phase_max = 10;
float beta = .9;

// support
Support *support_attr;
PartialCoherence *partial_coherence;

bool d_type_precision;

// when to start averaging iterates
int avg_iterations;
int aver_method;
// number of iterates to average

// calculated number of iterations
int number_iterations;


Params::Params(const char* config_file, const dim4 data_dim)
{
    BuildAlgorithmMap();
    
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
        
        int switch_iter = 0;
        int iter = 0;
        for (int i = 0; i < count; ++i)
        {   
            int repeat = tmp[i][0];
            for (int k = 0; k < repeat; k++)
            { 
                for (int j = 1; j < tmp[i].getLength(); ++j)
                {
                    iter = tmp[i][j][1];
                    switch_iter = switch_iter + iter;
                    alg_switches.push_back(Alg_switch(algorithm_id_map[tmp[i][j][0]], switch_iter));
                }
            }
        }
        number_iterations = alg_switches[alg_switches.size()-1].iterations;
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'algorithm_sequence' parameter in configuration file.");
    }

    int * support_area = new int[3];
    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["support_area"];
        for (int i = 0; i < tmp.getLength(); ++i)
        {
            try {
                support_area[i] = Utils::GetDimension(tmp[i]);
            }
            catch ( const SettingTypeException &nfex)
            {
                float ftmp = tmp[i];
                support_area[i] = Utils::GetDimension(int(ftmp * data_dim[i]));
            }
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_area' parameter in configuration file.");
    }
    float support_threshold = 0;
    try {
        support_threshold = cfg.lookup("support_threshold");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_threshold' parameter in configuration file.");
    }
    int support_sigma = 0;
    try {
        support_sigma = cfg.lookup("support_sigma");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_sigma' parameter in configuration file.");
    }
    Trigger *support_trigger = ParseTrigger("support");
    support_attr = new Support(data_dim, support_area, support_threshold, support_sigma, support_trigger);

    int * roi = new int[3];
    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["partial_coherence_roi"];
        for (int i = 0; i < tmp.getLength(); ++i)
        {
            try {
                roi[i] = Utils::GetDimension(tmp[i]);
            }
            catch ( const SettingTypeException &nfex)
            {
                float ftmp = tmp[i];
                roi[i] = Utils::GetDimension(int(ftmp * data_dim[i]));
            }
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'partial_coherence_roi' parameter in configuration file.");
    }
    int * kernel = new int[3];
    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["partial_coherence_kernel"];
        for (int i = 0; i < tmp.getLength(); ++i)
        {
            try {
                kernel[i] = Utils::GetDimension(tmp[i]);
            }
            catch ( const SettingTypeException &nfex)
            {
                float ftmp = tmp[i];
                kernel[i] = Utils::GetDimension(int(ftmp * data_dim[i]));
            }
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'partial_coherence_kernel' parameter in configuration file.");
    }

    Trigger *partial_coherence_trigger = ParseTrigger("partial_coherence");
    partial_coherence = new PartialCoherence(roi, kernel, partial_coherence_trigger);

    try
    {
        amp_threshold = cfg.lookup("amp_threshold");
    }
    catch(const SettingNotFoundException &nfex)
    {
        printf("No 'amp_threshold' parameter in configuration file.");
    }

    try {
        amp_threshold_fill_zeros = cfg.lookup("amp_threshold_fill_zeros");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'amp_threshold_fill_zeros' parameter in configuration file.");
    }
    
    try {
        phase_min = cfg.lookup("phase_min");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'phase_min' parameter in configuration file.");
    }

    try {
        phase_max = cfg.lookup("phase_max");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'phase_max' parameter in configuration file.");
    }

    try
    {
        beta = cfg.lookup("beta");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'beta' parameter in configuration file.");
    }

    try
    {
        avg_iterations = cfg.lookup("avg_iterations");
    } catch (const SettingNotFoundException &nfex) {
        printf("No 'avg_iterations' parameter in configuration file.");
    }
        
    try
    {
        aver_method = cfg.lookup("aver_method");
    } catch (const SettingNotFoundException &nfex) {
        printf("No 'aver_method' parameter in configuration file.");
    }

}

void Params::BuildAlgorithmMap()
{
    // hardcoded
    algorithm_id_map.insert(std::pair<char*,int>("ER", ALGORITHM_ER));
    algorithm_id_map.insert(std::pair<char*,int>("HIO", ALGORITHM_HIO));
}

Trigger * Params::ParseTrigger(std::string trigger_name)
{
    const Setting& root = cfg.getRoot();
    std::vector<trigger_setting> triggers;
    int alg = -1;
    try {
        alg = algorithm_id_map[cfg.lookup(trigger_name + "_type")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("No ") + trigger_name.c_str() + std::string("_type' parameter in configuration file.")).c_str());
    }

    try {
        const Setting &tmp = root[(trigger_name + std::basic_string<char>("_triggers")).c_str()];
        for (int i =0; i < tmp.getLength(); i++)
        {
            int start = tmp[i][0];
            int step = tmp[i][1];
            if (tmp[i].getLength() > 2)
            {
                end = tmp[i][2];
                end = std::min(end, number_iterations);
            }
            else
            {
                end = number_iterations;
            }
            triggers.push_back(Trigger_setting(start, step, end));
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("No ") + trigger_name + std::string("_triggers' parameter in configuration file.")).c_str());
    }
    return (new Trigger(triggers, alg));
}

int Params::GetNumberIterations()
{
    return number_iterations;
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

int Params::GetAvgIterations()
{
    return avg_iterations;
}

int Params::GetAvrgMethod()
{
    return aver_method;
}

Support * Params::GetSupport()
{
    return support_attr;
}

PartialCoherence * Params::GetPartialCoherence()
{
    return partial_coherence;
}

std::vector<alg_switch> Params::GetAlgSwitches()
{
    return alg_switches;
}

//-----------------------------------------------------------------
// Trigger class
Trigger::Trigger(std::vector<trigger_setting> triggers, int alg)
{
    trig_algorithm = alg;
    for (int i = 0; i < triggers.size(); i++)
    {
        for (int j = triggers[i].start_iteration; j <= triggers[i].end_iteration; j += triggers[i].step_iteration)
        {
            trigger_iterations.push_back(j);
        }
    }
    if (triggers.size() > 1)
    {
        std::sort(trigger_iterations.begin(), trigger_iterations.end());
        trigger_iterations.erase( unique(trigger_iterations.begin(), trigger_iterations.end()), trigger_iterations.end());
    }
}

std::vector<int> Trigger::GetTriggers()
{
    return trigger_iterations;
}

int Trigger::GetTriggerAlgorithm()
{
    return trig_algorithm;
}


//---------------------------------------------------------------------
// PartialCoherence class
PartialCoherence::PartialCoherence(int * roi_area, int * kernel_area, Trigger * partial_coherence_trig)
{
    partial_coherence_trigger = partial_coherence_trig;
    roi= roi_area;
    kernel = kernel_area;
}

std::vector<int> PartialCoherence::GetTriggers()
{
    return partial_coherence_trigger->GetTriggers();
}

int PartialCoherence::GetTriggerAlgorithm()
{
    return partial_coherence_trigger->GetTriggerAlgorithm();
}

int * PartialCoherence::GetRoi()
{
    return roi;
}

int * PartialCoherence::GetKernel()
{
    return kernel;
}

//------------------------------------------------------------------------
// class Utils
int Utils::GetDimension(int dim)
{
    int new_dim = dim;
    while (! IsCorrect(new_dim))
    {
        new_dim++;
    }
    return new_dim;
}

bool Utils::IsCorrect(int dim)
{
    int sub = dim;
    while (sub % 2 == 0)
    {
        sub = sub/2;
    }
    while (sub % 3 == 0)
    {
        sub = sub/3;
    }
    while (sub % 5 == 0)
    {
        sub = sub/5;
    }
    if (sub == 1)
        return true;
    else
        return false;
}

