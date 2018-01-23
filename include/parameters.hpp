/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef parameters_hpp
#define parameters_hpp

#include "string"
#include "common.h"
#include "vector"
//#include "arrayfire.h"

//using namespace af;

struct Trigger_setting
{
    int start_iteration;
    int step_iteration;
    int end_iteration;
    Trigger_setting(int start, int step, int end)
    {
        start_iteration = start;
        step_iteration = step;
        end_iteration = end;
    }
};
typedef struct Trigger_setting trigger_setting;

// This class holds parameters defining the reconstruction process. The parameters are set based on configuration file.
// Methods of this class are getters.
class Params
{
private:
    std::vector<int> ParseTriggers(std::string trigger_name, int);
    void BuildAlgorithmMap();
    void BuildActionMap();

public:
    // Constructor. Takes in configuration file, parses the configuration and sets the parameters accordingly.
    Params(const char* config_file, int stage, std::vector<int> data_dim);
    ~Params();
       
    // returns data type (float/double). Used by python code
    std::string GetDataType();

    // Returns number of all iterations. It is calculated from the "algorithm_sequence" parameter.
    int GetNumberIterations();

    std::vector<int> GetSupportArea();
    float GetSupportThreshold();
    float GetSupportSigma();
    std::vector<int> GetSupportTriggers();
    int GetSupportAlg();

    int GetPcdiAlgorithm();
    std::vector<int> GetPcdiRoi();
    std::vector<int> GetPcdiTriggers();
    bool GetPcdiNormalize();
    int GetPcdiIterations();

    float GetIterLowResSigmaMin();
    float GetIterLowResSigmaMax();
    std::vector<int> GetUpdateResolutionTriggers();
    int GetLowResolutionIter();

    // Returns amplitude threshold. Used by ER and HIO algorithms.
    d_type GetAmpThreshold();
    
    // Returns true if the ER/HIO algorithms should fill the image if not met amplitude threshold condition with zeros.
    // Returns false, if the values should not be modified.
    bool IsAmpThresholdFillZeros();
    
    // Returns minimum phase value for the HIO processing.
    d_type GetPhaseMin();
    
    // Returns maximum phase value for the HIO processing.
    d_type GetPhaseMax();
    
    // Returns beta parameter for the HIO processing.
    float GetBeta();
    
    // Returns iteration number at which the amplitudes are averaged.
    int GetAvgIterations();

    // Returns iteration number at which the "twin" gets zeroed out.
    int GetTwin();

    // Returns a vector containing algorithm switch sequence.
    // Algorithm switch is defined as a pair of two elements, the first defines an algorithm, and the second defines
    // iteration at which the algorithm stops and switches to a next algorithm.
    std::vector<alg_switch> GetAlgSwitches();

    // Returns a constant indication a scheme for modifying data when calculation ratio in modulus projection
    int GetRegularizedAmp();
    
    // Returns directory to save results
    const char * GetSaveDir();

    // Returns directory to retrieve previous results to continue
    const char * GetContinueDir();

    // Returns action the program will perform. Choices are "prep_only", "new_guess", "continue"
    int GetAction();

    // Returns boolean flag indication whether to save the raw results
    bool IsSaveResults();

    // Returns boolean flag indication whether to plot errors in during calculations
    bool IsPlotErrors();

    // Returns number of iterations between calling garbage collection.
    int GetGC();

    // Returns ID of target device (cpu or gpu).
    int GetDeviceId();

    int GetActionStage();

};


#endif /* parameters_hpp */
