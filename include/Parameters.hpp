//
//  Parameters.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef Parameters_hpp
#define Parameters_hpp

#include "stdio.h"
#include "arrayfire.h"
#include "common.h"
#include "vector"


using namespace af;

// This class holds parameters defining the reconstruction process. The parameters are set based on configuration file.
// Methods of this class are generally getters.
class Params
{
public:
    // Constructor. Takes in configuration file, parses the configuration and sets the parameters accordingly.
    Params(const char* config_file);
    
    // Returns an array containing numbers indicating how many iterations will be performed for each alternating algorithm.
    std::vector<int> GetAlgorithmSequence();
    
    // Returns number of all ierations, as defined in the "algorithm sequence" array
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
};


#endif /* Parameters_hpp */
