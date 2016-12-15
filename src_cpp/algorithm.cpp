
#include "algorithm.hpp"
#include "worker.hpp"
#include "common.h"

Algorithm::Algorithm()
{
}

Algorithm * Algorithm::GetObject(int alg_id)
{
    // TODO consider refactoring if there are many subclasses
    // this method is called only during initialization, so it might be ok
    switch (alg_id) {
        case ALGORITHM_HIO :
            return new Hio();
            break;
        case ALGORITHM_ER :
            return new Er();
            break;
        default :
            return NULL;
            break;
    }
    
}

void Algorithm::RunAlgorithm(Reconstruction reconstruction)
{
    rec = reconstruction;
    ModulusProjection();
    ApplyAmplThreshold();
}

void Algorithm::ModulusProjection()
{
    // the common code
    rec->rs_amplitudes = ifft3(rec->ds_image)*rec->data_size;
    
    // TODO pcdi
    
    state->RecordError(sum<d_type>(pow( (abs(rec->rs_amplitudes)-abs(data)) ,2))/rec->norm_data);
    // need to check timing of the expressions below.
    // notice that the top one does not work for c64
    //af::replace(rs_amplitudes, amplitude_condition, data * exp(complex(0, arg(rs_amplitudes))));
    af::replace(rec->rs_amplitudes, rec->amplitude_condition, rec->data * rec->rs_amplitudes / (abs(rs_amplitudes) + .0001));
    
    if (params->IsAmpThresholdFillZeros())
    {
        replace(rs_amplitudes, ! amplitude_condition, 0);
    }
    ds_image = fft3(rs_amplitudes)/data_size;
}

void Algorithm::ApplyAmplThreshold()
{
    // the common code
}

//-------------------------------------------------------------------
// Hio sub-class
Hio::Hio() : Algorithm() { }

void Hio::ModulusProjection()
{
    af::array prev_ds_image = ds_image;
    Algorithm::ModulusProjection();
    
    // find phase
    d_type norm_ds_image = GetNorm(ds_image);
    
    //calculate phase
    af::array phase = atan2(imag(ds_image), real(ds_image));
    af::array phase_condition = operator>(params->GetPhaseMin(), phase) && operator<(params->GetPhaseMax(), phase) && (support->GetSupportArray() == 1);
    replace(ds_image, phase_condition, (prev_ds_image - ds_image * params->GetBeta()));
    
    d_type norm_ds_image_with_support = GetNorm(ds_image);
    
    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    ds_image *= ratio;
}

void Hio::ApplyAmplThreshold()
{
    
}

//-------------------------------------------------------------------
// Er sub-class
Er::Er() : Algorithm() { }

void Er::ModulusProjection()
{
    Algorithm::ModulusProjection();
    d_type norm_ds_image = GetNorm(ds_image);
    ds_image *= support->GetSupportArray();
    
    d_type norm_ds_image_with_support = GetNorm(ds_image);
    
    d_type ratio = sqrt(norm_ds_image/norm_ds_image_with_support);
    ds_image *= ratio;
    
}

void Er::ApplyAmplThreshold()
{
    
}
