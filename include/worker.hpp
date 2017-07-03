//
//  worker.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/12/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef worker_hpp
#define worker_hpp

#include "stdio.h"
#include "vector"
#include "map"
#include "common.h"


class Params;
class State;
class Support;
class PartialCoherence;
#include "arrayfire.h"

using namespace af;

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
    // A reference to Support object
    Support *support;
    // A reference to PartialCoherence
    PartialCoherence *partialCoherence;

    // This method returns sum of squares of all elements in the array
    double GetNorm(af::array arr);
    
    // This method calculates ratio of amplitudes and correction arrays replacing zero divider with 1.
    af::array GetRatio(af::array ar, af::array correction);

    // Averages amplitudes
    void Average();

    // This method applies amplitude threshold constraint to correct the amplitudes of rs_amplitudes
    // i.e. if data amplitude is over the threshold, the rs_amplitudes value is modified.
    // Other values are either zeroed out or intact depending on configuration.
    void AmplitudeThreshold();

    d_type CalculateError();

public:
    // The class constructor takes data array, an image guess array in reciprocal space, and configuration file. The image guess
    // is typically generated as an complex random array. This image can be also the best outcome of previous calculations. The
    // data is saved and is used for processing. Configuration file is used to construct the Param object.
    Reconstruction(af::array data, af::array guess, const char* config);
    
    // This initializes the object. It must be called after object is created.
    // 1. it calculates and sets norm of the data
    // 2. it calculates and sets size of data array
    // 3. it calculates and set an amplitude threshold condition boolean array
    // 4. it normalizes the image with the first element of the data array
    // 5. it initializes other components (i.e. state)
    void Init();
    
    // Each iteration of the image, is considered as a new state. This method executes one iteration.
    // First it calls Next() on State, which determines which algorithm should be run in this state. It also determines whether the
    // algorithms should be modified by applying convolution or updating support. This method returns false if all iterations have
    // been completed (i.e. the code reached last state), and true otherwise. Typically this method will be run in a while loop.
    void Iterate();

    int GetCurrentIteration();

    // This code is common for ER and HIO algorithms.
    void ModulusProjection();

    // Runs one iteration of ER algorithm.
    void ModulusConstrainEr();

    // Runs one iteration of ER with normalizing algorithm. 
    void ModulusConstrainErNorm();

    // Runs one iteration of HIO algorithm. 
    void ModulusConstrainHio();

    // Runs one iteration of HIO with normalizing algorithm. 
    void ModulusConstrainHioNorm();

    af::array GetImage();
    std::vector<d_type>  GetErrors();

};

#endif /* worker_hpp */
