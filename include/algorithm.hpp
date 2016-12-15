
#ifndef algorithm_hpp
#define algorithm_hpp

class Reconstruction;

class Algorithm
{
protected:
    // a reference to the Reconstruction object that the algorithm is run for
    Reconstruction * rec;
    
    // constructor
    Algorithm();
public:
    // creates and returns subclass specified by algorithm id
    static Algorithm * GetObject(int alg_id);
    
    // Using strategy pattern. The RunAlgorihm calls sequence of methods
    // overriden by concrete classes
    void RunAlgorithm(Reconstruction reconstruction);
    
    // the following methods are overriden in concrete algorithms
    // they are part of strategy pattern
    void ModulusProjection();
    void ApplyAmplThreshold();
};

class Hio : public Algorithm
{
public:
    Hio();
    void ModulusProjection();
    void ApplyAmplThreshold();
};

class Er : Algorithm
{
public:
    Er();
    void ModulusProjection();
    void ApplyAmplThreshold();
};

#endif /*algorithm_hpp */
