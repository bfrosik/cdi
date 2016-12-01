//
//  parameters.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef parameters_hpp
#define parameters_hpp

#include "stdio.h"
#include "arrayfire.h"
#include "common.h"
#include "vector"

class Reconstruction;
using namespace af;


// This class holds parameters defining the reconstruction process. The parameters are set based on configuration file.
// Methods of this class are getters.
class Params
{
private:
    // This method creates a map of string definitions for algorithms to numeric identifiers.
    void BuildAlgorithmMap();

public:
    // Constructor. Takes in configuration file, parses the configuration and sets the parameters accordingly.
    Params(const char* config_file);

    // Returns number of all ierations. It is calculated from the "algorithm_sequence" parameter.
    int GetIterationsNumber();
    
    // Returns a three dimentional array containing coordinates defining initial support.
    // The initial support is cuboid defined by zero coordinates, and roi.
    std::vector<int> GetRoi();
    
    // Returns a number defining number of iterations between support update.
    int GetSuportUpdateStep();
    
    // Returns amplitude threshold. Used by ER and HIO algorithms.
    d_type GetAmpThreshold();
    
    // Returns true if the ER/HIO algorims should fill the image if not met amplitude threshold condition with zeros.
    // Returns false, if the values should not be modified.
    bool IsAmpThresholdFillZeros();
    
    // Returns minimum phase value for the HIO processing.
    d_type GetPhaseMin();
    
    // Returns maximum phase value for the HIO processing.
    d_type GetPhaseMax();
    
    // Returns beta parameter for the HIO processing.
    float GetBeta();
    
    // Returns iteration number at which the amplitudes are averaged.
    int GetIterateAvgStart();

    // Returns a vector containing algorithm switch sequence.
    // Algorithm switch is defined as a pair of two elements, the first defins an algorithm, and the second defins
    // iteration at which the algorithm stops and switches to a next algorithm.
    std::vector<alg_switch> GetAlgSwitches();
    
};


#endif /* parameters_hpp */
