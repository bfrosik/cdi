//
//  Reconstruction.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/12/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef Reconstruction_hpp
#define Reconstruction_hpp

#include "stdio.h"
#include "arrayfire.h"
#include "vector"
#include "common.h"

using namespace af;

class Params;
class State;

// This class represents a single image phase reconstruction processing.
// It constructs the following objects:
// 1. Params, which is initialized from configuration file, and keeps the attributes that do not change during processing.
// 2. State, which keeps the variables that mutate during processing.
// The class does calculations defined by the configuration file. The result of the calculation is an image that is a close
// match to the recoprocical space data in the opposite space.

class Reconstruction
{
private:

    // Params object constructed by the Reconstruction class
    Params *params;
    // State object constructed by the Reconstruction class
    State *state;
    
    // This initializes the object. It must be called after object is created.
    // 1. it calculates and sets norm of the data
    // 2. it calculates and sets size of data array
    // 3. it calculates and set an amplitude threshold condition boolean array
    // 4. it normalizes the image with the first element of the data array
    // 5. it initializes other components (i.e. state)
    void Init();
    
    // This method returns a norm of an array.
    d_type GetNorm(af::array arr);
    
    // This code is common for ER and HIO algorithms.
    void CommonErHio();
    
    // runs one iteration of ER algorithm. It checks if the convolution algorithm should be run in this state, and if so, alters
    // the processing.
    void Er();
    
    // runs one iteration of HIO algorithm. It checks if the convolution algorithm should be run in this state, and if so, alters
    // the processing.
    void Hio();
    
    // This method runs the convolution algorithm on the image array. It calculates an error and records it.
    // The method returns a norm that is used in the next step of the algoritms - amplitude threashold normalization.
    d_type Convolve();
    
    // Each iteration of the image, whether it is ER or HIO, is considered as a new state. This method executes one iteration.
    // First it calls Next() on State, which determines which algorithm should be run in this state. It also determines whether the
    // algorithms should be modified by applying convolution or updating support. This method returns false if all iterations have
    // been completed (i.e. the code reached last state), and true otherwise. Typically this method will be run in a while loop.
    bool Next();

public:
    
    // The class constructor takes data array, an image guess array in reciprocal space, and configuration file. The image guess
    // is typically generated as an complex random array. This image can be also the best outcome of previous calculations. The
    // data is saved and is used for processing. Configuration file is used to construct the Param object.
    Reconstruction(af::array data, af::array guess, const char* config);
    
    //
    void Iterate();

    af::array GetImage();
    std::vector<d_type>  GetErrors();

};


#endif /* Reconstruction_hpp */