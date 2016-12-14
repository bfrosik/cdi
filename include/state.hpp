//
//  state.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef state_hpp
#define state_hpp

#include "arrayfire.h"
#include "vector"
#include "common.h"


using namespace af;

class Params;

// This class maintain the state of the reconstruction process.
class State
{
public:
    // Constructor. Takes pointer to the Param object. Uses the Param object to set the initial values.
    State(Params *params);
    
    // Needs destructor to free allocated memory.
    ~State();
    
    // This initializes the object. It does the following:
    // - sets current algorithm
    // - sets the total number of iterations
    void Init();
    
    // This method determines the attributes of the current state (i.e. iteration).
    // It returns false if the program reached the end of iterations, and true otherwise.
    // It finds which algorithm will be run in this state .
    // It sets the algorithm to run convolution based on state. (convolution is run at the algorithm switch)
    // It calculates the averaging iteration (current iteration - start of averaging)
    // It updates support at the correct iterations.
    int Next();
    
    // Returns current iteration number
    int GetCurrentIteration();

    // Returns an algorithm that should be run in a current state (i.e. iteration).
    int GetCurrentAlg();
    
    // Returns true if the current state should include support update.
    bool IsUpdateSupport();

    // Returns true if the current state should include partial coherence update.
    bool IsUpdatePartialCoherence();

    // Returns the difference of current iteration and iteration of averaging start
    int GetAveragingIteration();
    
    // Stores the error
    void RecordError(d_type error);
    
    // Returns vector containing errors
    std::vector<d_type> GetErrors();
};


#endif /* state_hpp */
