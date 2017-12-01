/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "arrayfire.h"
#include <string.h>
#include "iostream"
#include "libconfig.h++"
#include "map"
#include "algorithm"
#include "parameters.hpp"
#include "common.h"
#include "util.hpp"

using namespace af;
using namespace libconfig;
Config cfg;

// maps action name to action number
std::map<std::string, int> action_id_map;

// maps algorithm name to algorithm number
std::map<std::string, int> algorithm_id_map;
// vector holding algorithm run sequence, where algorithm run is a pair of algorithm and number of iterations
std::vector<alg_switch> alg_switches;

std::string data_type;

d_type amp_threshold;
bool amp_threshold_fill_zeros;

d_type phase_min = 120;
d_type phase_max = 10;
float beta = .9;

// support
std::vector<int> support_area;
float support_threshold;
int support_sigma;
std::vector<int> support_triggers;
int support_alg;

//partial coherence
//PartialCoherence *partial_coherence = NULL;
int pcdi_alg = 0;
std::vector<int>  pcdi_roi;
std::vector<int> pcdi_triggers;
bool pcdi_normalize;
int pcdi_iter;

bool d_type_precision;

// number of iterates to average
int avg_iterations;

// calculated number of iterations
int number_iterations;

int twin;

int regularized_amp = REGULARIZED_AMPLITUDE_NONE;

const char * save_dir;

const char * continue_dir;

int action;

bool save_results;

int gc = -1;



Params::Params(const char* config_file, dim4 data_dim)
{
    BuildAlgorithmMap();
    BuildActionMap();
    
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
    
    try
    {
        save_dir = cfg.lookup("save_dir");
        // else it is initialized
    }
    catch (const SettingNotFoundException &nfex)
    {
        save_dir = "my_dir";
        printf("No 'save_dir' parameter in configuration file, saving in 'my_dir'.");
    }

    try {
        action = action_id_map[cfg.lookup("action")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        action = action_id_map["new_guess"];
        printf((std::string("No 'action' parameter in configuration file. running new guess")).c_str());
    }

    if (action == ACTION_CONTINUE)
    {
        try
        {
            continue_dir = cfg.lookup("continue_dir");
            // else it is initialized
        }
        catch (const SettingNotFoundException &nfex)
        {
            continue_dir = "my_dir";
            printf("No 'continue_dir' parameter in configuration file, saving in 'my_dir'.");
        }
    }
    save_results = true;
    try {
        save_results = cfg.lookup("save_results");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("No 'save_results' parameter in configuration file.")).c_str());
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

    try {
        gc = cfg.lookup("gc");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'gcd' parameter in configuration file.");
    }

    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["support_area"];
        for (int i = 0; i < tmp.getLength(); ++i)
        {
            try {
                support_area.push_back(tmp[i]);
            }
            catch ( const SettingTypeException &nfex)
            {
                float ftmp = tmp[i];
                support_area.push_back(int(ftmp * data_dim[i]));
            }
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_area' parameter in configuration file.");
    }
    support_threshold = 0;
    try {
        support_threshold = cfg.lookup("support_threshold");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_threshold' parameter in configuration file.");
    }
    support_sigma = 0;
    try {
        support_sigma = cfg.lookup("support_sigma");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_sigma' parameter in configuration file.");
    }
    support_triggers = ParseTriggers("support");
    support_alg = -1;
    try {
        support_alg = algorithm_id_map[cfg.lookup("support_type")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("'No support_type' parameter in configuration file.")).c_str());
    }

    pcdi_alg = 0;
    try {
        pcdi_alg = algorithm_id_map[cfg.lookup("partial_coherence_type")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("No 'partial_coherence_type' parameter in configuration file.")).c_str());
    }

    if (pcdi_alg > 0)
    {
        try {
            const Setting& root = cfg.getRoot();
            const Setting &tmp = root["partial_coherence_roi"];
            for (int i = 0; i < tmp.getLength(); ++i)
            {
                try {
                    pcdi_roi.push_back(Utils::GetDimension(tmp[i]));
                }
                catch ( const SettingTypeException &nfex)
                {
                    float ftmp = tmp[i];
                    pcdi_roi.push_back(Utils::GetDimension(int(ftmp * data_dim[i])));
                }
            }
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf("No 'partial_coherence_roi' parameter in configuration file.");
        }

        pcdi_triggers = ParseTriggers("partial_coherence");
        pcdi_normalize = false;
        try {
            pcdi_normalize = cfg.lookup("partial_coherence_normalize");
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf((std::string("No 'partial_coherence_normalize' parameter in configuration file.")).c_str());
        }
        pcdi_iter = 1;
        try {
            pcdi_iter = cfg.lookup("partial_coherence_iteration_num");
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf((std::string("'No partial_coherence_iteration_num' parameter in configuration file.")).c_str());
        }
    }

    try
    {
        avg_iterations = cfg.lookup("avg_iterations");
    }
    catch(const SettingNotFoundException &nfex)
    {
        printf("No 'avg_iterations' parameter in configuration file.");
    }

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
        const char *reg_amp = cfg.lookup("regularized_amp");
        if (strcmp (reg_amp, "GAUSS") == 0)
        {
            regularized_amp = REGULARIZED_AMPLITUDE_GAUSS;
        }
        else if (strcmp (reg_amp, "POISSON") == 0)
        {
            regularized_amp = REGULARIZED_AMPLITUDE_POISSON;
        }
        else if (strcmp (reg_amp, "UNIFORM") == 0)
        {
            regularized_amp = REGULARIZED_AMPLITUDE_UNIFORM;
        }
        // else it is initialized
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'regularized_amp' parameter in configuration file.");
    }
    twin = -1;
    try {
        twin = cfg.lookup("twin");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'twin' parameter in configuration file.");
    }

}

void Params::BuildAlgorithmMap()
{
    // hardcoded
    algorithm_id_map.insert(std::pair<char*,int>("ER", ALGORITHM_ER));
    algorithm_id_map.insert(std::pair<char*,int>("HIO", ALGORITHM_HIO));
    algorithm_id_map.insert(std::pair<char*,int>("LUCY", ALGORITHM_LUCY));
    algorithm_id_map.insert(std::pair<char*,int>("LUCY_PREV", ALGORITHM_LUCY_PREV));
    algorithm_id_map.insert(std::pair<char*,int>("GAUSS", ALGORITHM_GAUSS));
}

void Params::BuildActionMap()
{
    // hardcoded
    action_id_map.insert(std::pair<char*,int>("prep_only", ACTION_PREP_ONLY));
    action_id_map.insert(std::pair<char*,int>("new_guess", ACTION_NEW_GUESS));
    action_id_map.insert(std::pair<char*,int>("continue", ACTION_CONTINUE));
}

std::vector<int> Params::ParseTriggers(std::string trigger_name)
{
    std::vector<int> trigger_iterations;
    const Setting& root = cfg.getRoot();
    std::vector<trigger_setting> triggers;

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

    return trigger_iterations;
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

int Params::GetRegularizedAmp()
{
    return regularized_amp;
}

int Params::GetTwin()
{
    return twin;
}

std::vector<int> Params::GetSupportArea()
{
    return support_area;
}

float Params::GetSupportThreshold()
{
    return support_threshold;
}

int Params::GetSupportSigma()
{
    return support_sigma;
}

std::vector<int> Params::GetSupportTriggers()
{
    return support_triggers;
}

int Params::GetSupportAlg()
{
    return support_alg;
}

//PartialCoherence * Params::GetPartialCoherence()
//{
//    return partial_coherence;
//}
int Params::GetPcdiAlgorithm()
{
    return pcdi_alg;
}

std::vector<int>  Params::GetPcdiRoi()
{
    return pcdi_roi;
}

std::vector<int> Params::GetPcdiTriggers()
{
    return pcdi_triggers;
}

bool Params::GetPcdiNormalize()
{
    return pcdi_normalize;
}

int Params::GetPcdiIterations()
{
    return pcdi_iter;
}

std::vector<alg_switch> Params::GetAlgSwitches()
{
    return alg_switches;
}

const char * Params::GetSaveDir()
{
    return save_dir;
}

const char * Params::GetContinueDir()
{
    return continue_dir;
}

int Params::GetAction()
{
    return action;
}

bool Params::IsSaveResults()
{
    return save_results;
}

int Params::GetGC()
{
    return gc;
}


