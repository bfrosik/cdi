//
//  parameters.cpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#include "arrayfire.h"
#include <string.h>
#include "iostream"
#include "libconfig.h++"
#include "map"
#include "algorithm"
#include "parameters.hpp"
#include "support.hpp"
#include "pcdi.hpp"
#include "common.h"
#include "util.hpp"

using namespace af;
using namespace libconfig;
Config cfg;

// maps algorithm name to algorithm number
std::map<std::string, int> algorithm_id_map;
// vector holding algorithm run sequence, where algorithm run is a pair of algorithm and number of iterations
std::vector<alg_switch> alg_switches;

std::string data_type;

//use the matlab order (fft/ifft in modulus projector)
bool matlab_order = true;

// amplitude threshold
d_type amp_threshold;
bool amp_threshold_fill_zeros;

d_type phase_min = 120;
d_type phase_max = 10;
float beta = .9;

// support
Support *support_attr;
PartialCoherence *partial_coherence = NULL;

bool d_type_precision;

// number of iterates to average
int avg_iterations;

// calculated number of iterations
int number_iterations;

int twin;

int regularized_amp = REGULARIZED_AMPLITUDE_NONE;
int gc = -1;



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

    try {
        gc = cfg.lookup("gc");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'gcd' parameter in configuration file.");
    }

    std::vector<int> support_area;
    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["support_area"];
        for (int i = 0; i < tmp.getLength(); ++i)
        {
            try {
                //support_area[i] = Utils::GetDimension(tmp[i]);
                support_area.push_back(tmp[i]);
            }
            catch ( const SettingTypeException &nfex)
            {
                float ftmp = tmp[i];
                //support_area[i] = Utils::GetDimension(int(ftmp * data_dim[i]));
                support_area.push_back(int(ftmp * data_dim[i]));
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
    bool support_threshold_adjust = true;
    try {
        support_threshold_adjust = cfg.lookup("support_threshold_adjust");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_threshold_adjust' parameter in configuration file.");
    }
    int support_sigma = 0;
    try {
        support_sigma = cfg.lookup("support_sigma");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_sigma' parameter in configuration file.");
    }
    std::vector<int> support_triggers = ParseTriggers("support");
    int support_alg = -1;
    try {
        support_alg = algorithm_id_map[cfg.lookup("support_type")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("'No support_type' parameter in configuration file.")).c_str());
    }
    support_attr = new Support(data_dim, support_area, support_threshold, support_threshold_adjust, support_sigma, support_triggers, support_alg);
    printf("created support\n");

    int pcdi_alg = 0;
    try {
        pcdi_alg = algorithm_id_map[cfg.lookup("partial_coherence_type")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("'No partial_coherence_type' parameter in configuration file.")).c_str());
    }

    if (pcdi_alg > 0)
    {
        std::vector<int>  roi;
        try {
            const Setting& root = cfg.getRoot();
            const Setting &tmp = root["partial_coherence_roi"];
            for (int i = 0; i < tmp.getLength(); ++i)
            {
                try {
                    roi.push_back(Utils::GetDimension(tmp[i]));
                }
                catch ( const SettingTypeException &nfex)
                {
                    float ftmp = tmp[i];
                    roi.push_back(Utils::GetDimension(int(ftmp * data_dim[i])));
                }
            }
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf("No 'partial_coherence_kernel' parameter in configuration file. Setting the dimensions to roi");
            int * kernel = new int[3];
            kernel[0] = roi[0];
            kernel[1] = roi[1];
            kernel[2] = roi[2];
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

        std::vector<int> partial_coherence_trigger = ParseTriggers("partial_coherence");
        bool pcdi_normalize = false;
        try {
            pcdi_normalize = cfg.lookup("partial_coherence_normalize");
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf((std::string("'No partial_coherence_normalize' parameter in configuration file.")).c_str());
        }
        bool pcdi_clip = false;
        try {
            pcdi_clip = cfg.lookup("partial_coherence_clip");
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf((std::string("'No partial_coherence_clip' parameter in configuration file.")).c_str());
        }
        int pcdi_iter = 1;
        try {
            pcdi_iter = cfg.lookup("partial_coherence_iteration_num");
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf((std::string("'No partial_coherence_iteration_num' parameter in configuration file.")).c_str());
        }
        if (partial_coherence_trigger.size() > 0)
        {
            partial_coherence = new PartialCoherence(roi, kernel, partial_coherence_trigger, pcdi_alg, pcdi_normalize, pcdi_iter, pcdi_clip);
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

    try {
        matlab_order = cfg.lookup("matlab_order");
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'matlab_order' parameter in configuration file., setting to true");
    }
//    try {
//        data_type = cfg.lookup("data_type");
//    }
//    catch ( const SettingNotFoundException &nfex)
//    {
//        printf((std::string("'No data_type' parameter in configuration file. Setting to double.")).c_str());
//        data_type = "double";
//    }

}

void Params::BuildAlgorithmMap()
{
    // hardcoded
    algorithm_id_map.insert(std::pair<char*,int>("ER", ALGORITHM_ER));
    algorithm_id_map.insert(std::pair<char*,int>("HIO", ALGORITHM_HIO));
    algorithm_id_map.insert(std::pair<char*,int>("ER_NORM", ALGORITHM_ER_NORM));
    algorithm_id_map.insert(std::pair<char*,int>("HIO_NORM", ALGORITHM_HIO_NORM));
    algorithm_id_map.insert(std::pair<char*,int>("LUCY", ALGORITHM_LUCY));
    algorithm_id_map.insert(std::pair<char*,int>("LUCY_PREV", ALGORITHM_LUCY_PREV));
    algorithm_id_map.insert(std::pair<char*,int>("GAUSS", ALGORITHM_GAUSS));
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

//std::string Params::GetDataType()
//{
//    return data_type;
//}

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

bool Params::IsMatlabOrder()
{
    return matlab_order;
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

int Params::GetGC()
{
    return gc;
}


