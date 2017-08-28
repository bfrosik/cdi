//
//  parameters.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef parameters_hpp
#define parameters_hpp

#include "common.h"
#include "vector"
#include "arrayfire.h"

using namespace af;

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

class Reconstruction;
class Support;
class PartialCoherence;

// This class holds parameters defining the reconstruction process. The parameters are set based on configuration file.
// Methods of this class are getters.
class Params
{
private:
    std::vector<int> ParseTriggers(std::string trigger_name);
    void BuildAlgorithmMap();

public:
    // Constructor. Takes in configuration file, parses the configuration and sets the parameters accordingly.
    Params(const char* config_file, const dim4 data_dim);
    
    // returns data type (float/double). Used by python code
    std::string GetDataType();

    // Returns number of all iterations. It is calculated from the "algorithm_sequence" parameter.
    int GetNumberIterations();

    // Returns info for support update. trigger list contains starting iteration, step, and ending iteration
    // (if missing, run to the end) 
    Support * GetSupport();

    // Returns info for partial coherence. trigger list contains starting iteration, step, and ending iteration
    // (if missing, run to the end)
    PartialCoherence * GetPartialCoherence();

    // Returns amplitude threshold. Used by ER and HIO algorithms.
    d_type GetAmpThreshold();
    
    // Returns true if the ER/HIO algorithms should fill the image if not met amplitude threshold condition with zeros.
    // Returns false, if the values should not be modified.
    bool IsAmpThresholdFillZeros();
    
    // Returns true if the modulus projector follows Matlab algorithm, i.e. first apply fft to go into reciprocal space, 
    // then ifft to direct space. Retirn false if reverse order.
    bool IsMatlabOrder();
    
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

};


#endif /* parameters_hpp */
