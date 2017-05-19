
#ifndef algorithm_hpp
#define algorithm_hpp

class Reconstruction;

class Algorithm
{
public:   
    // Using strategy pattern. The RunAlgorihm calls sequence of methods
    // overriden by concrete classes
    void RunAlgorithm(Reconstruction * reconstruction);
    
    // the following methods are overriden in concrete algorithms
    // they are part of strategy pattern
    void ModulusProjection();
    virtual void ModulusConstrain();
};

class Hio : public Algorithm
{
public:
    void ModulusConstrain();
};

class Er : public Algorithm
{
public:
    void ModulusConstrain();
};

class HioNorm : public Algorithm
{
public:
    void ModulusConstrain();
};

class ErNorm : public Algorithm
{
public:
    void ModulusConstrain();
};

#endif /*algorithm_hpp */
