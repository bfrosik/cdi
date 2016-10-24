//
//  state.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef state_hpp
#define state_hpp

#include "stdio.h"
#include "arrayfire.h"
#include "vector"
#include "common.h"


using namespace af;

class Params;

// This class maintain the state of the reconstruction process.
class State
{
private:
    // This method is called
    void UpdateSupport();
    int GetCurrentIteration();
    
public:
    // Constructor. Takes pointer to the param object. Uses the param object to set the initial values.
    State(Params *params);
    
    // Needs destructor to free allocated memory.
    ~State();
    
    // This initializes the object. It's called by the Reconstruction object, as part of initialization.
    // It does the following:
    // 1. sets the number of iterations
    // 2. creates array to store error values for each iteration
    // 3. create initial support array based on the configured roi values
    void Init(const dim4 data_dim);
    
    // This method determines the attributes of the next state, which is next iteration.
    // It returns false if the program reached the end of iterations, and true otherwise.
    // It finds which algorithm will be run in this state (ER or HIO)
    // It updates support at the correct iterations.
    // It finds whether the algorithm should include convolve.
    bool Next(af::array data);
    
    // Returns which algorithm (ER or HIO) should be run in a current state (i.e. iteration).
    int GetCurrentAlg();
    
    // Returns true if the current state should include convolution.
    bool IsConvolve();
    
    // Stores the error parameter
    void RecordError(d_type error);
    
    // Returns the support array
    af::array GetSupport();
    std::vector<d_type> GetErrors();
};


#endif /* state_hpp */
