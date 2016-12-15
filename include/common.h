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
const int ALGORITHM_GAUSS = 4;
const int ALGORITHM_BOX = 5;
const int ALGORITHM_PERCENT = 6;
const int ALGORITHM_GAUSS_FILL = 7;
const int ALGORITHM_GAUSS_PERCENT = 8;
const int ALGORITHM_PERCENT_AUTO = 9;
const int ALGORITHM_GAUSS_MINAREA = 10;


#endif /* common_h */
