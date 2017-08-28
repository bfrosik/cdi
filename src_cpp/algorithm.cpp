#include "iostream"
#include "algorithm.hpp"
#include "worker.hpp"
#include "common.h"

Reconstruction * rec;

void Algorithm::RunAlgorithm(Reconstruction * reconstruction)
{
    rec = reconstruction;
    ModulusConstrain(ModulusProjection());
}

af::array Algorithm::ModulusProjection()
{
    return rec->ModulusProjection();
}

void Algorithm::ModulusConstrain(af::array arr)
{

}

//-------------------------------------------------------------------
// Hio sub-class

void Hio::ModulusConstrain(af::array arr)
{
    rec->ModulusConstrainHio(arr);
}

//-------------------------------------------------------------------
// Er sub-class

void Er::ModulusConstrain(af::array arr)
{
    rec->ModulusConstrainEr(arr);
}

//-------------------------------------------------------------------
// Hio sub-class

void HioNorm::ModulusConstrain(af::array arr)
{
    rec->ModulusConstrainHioNorm(arr);
}

//-------------------------------------------------------------------
// Er sub-class

void ErNorm::ModulusConstrain(af::array arr)
{
    rec->ModulusConstrainErNorm(arr);
}
