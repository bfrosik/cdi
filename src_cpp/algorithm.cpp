#include "iostream"
#include "algorithm.hpp"
#include "worker.hpp"
#include "common.h"

Reconstruction * rec;

void Algorithm::RunAlgorithm(Reconstruction * reconstruction)
{
    rec = reconstruction;
    ModulusProjection();
    ModulusConstrain();
}

void Algorithm::ModulusProjection()
{
    rec->ModulusProjection();
}

void Algorithm::ModulusConstrain()
{

}

//-------------------------------------------------------------------
// Hio sub-class

void Hio::ModulusConstrain()
{
    rec->ModulusConstrainHio();
}

//-------------------------------------------------------------------
// Er sub-class

void Er::ModulusConstrain()
{
    rec->ModulusConstrainEr();
}

//-------------------------------------------------------------------
// Hio sub-class

void HioNorm::ModulusConstrain()
{
    rec->ModulusConstrainHioNorm();
}

//-------------------------------------------------------------------
// Er sub-class

void ErNorm::ModulusConstrain()
{
    rec->ModulusConstrainErNorm();
}
