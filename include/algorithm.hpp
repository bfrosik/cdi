
#ifndef algorithm_hpp
#define algorithm_hpp

class Reconstruction;
#include "arrayfire.h"

using namespace af;

class Algorithm
{
public:   
    // Using strategy pattern. The RunAlgorihm calls sequence of methods
    // overridden by concrete classes
    void RunAlgorithm(Reconstruction * reconstruction);
    
    // the following methods are overridden in concrete algorithms
    // they are part of strategy pattern
    af::array ModulusProjection();
    virtual void ModulusConstrain(af::array);
};

class Hio : public Algorithm
{
public:
    void ModulusConstrain(af::array);
};

class Er : public Algorithm
{
public:
    void ModulusConstrain(af::array);
};


#endif /*algorithm_hpp */
