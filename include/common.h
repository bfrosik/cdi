//
//  Constants.h
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/8/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef common_h
#define common_h

// defines the type of the data; can be float or double
typedef float d_type;

// a pair that defines an algorithm, and an iteration at which the algorithm is replaced by another or the process ends
struct Alg_switch 
{
    int algorithm_id;
    int iterations;
    Alg_switch(int alg, int iter)
    {
        algorithm_id = alg;
        iterations = iter;
    }
};
typedef struct Alg_switch alg_switch;

const int ALGORITHM_ER = 1;
const int ALGORITHM_HIO = 2;
const int ALGORITHM_LUCY = 3;
const int ALGORITHM_LUCY_PREV = 4;
const int ALGORITHM_GAUSS = 5;
const int ALGORITHM_BOX = 6;
const int ALGORITHM_PERCENT = 7;
const int ALGORITHM_GAUSS_FILL = 8;
const int ALGORITHM_GAUSS_PERCENT = 9;
const int ALGORITHM_PERCENT_AUTO = 10;
const int ALGORITHM_GAUSS_MINAREA = 11;

const int REGULARIZED_AMPLITUDE_NONE = 0;
const int REGULARIZED_AMPLITUDE_GAUSS = 1;
const int REGULARIZED_AMPLITUDE_POISSON = 2;
const int REGULARIZED_AMPLITUDE_UNIFORM = 3;

#endif /* common_h */
