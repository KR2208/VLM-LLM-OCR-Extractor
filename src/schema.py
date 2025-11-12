"""Pydantic schema for spall experiment data extraction."""

from typing import Optional
from pydantic import BaseModel, Field


class SpallExperiment(BaseModel):
    """Schema for a single spall experiment with evidence fields for every data point."""
    
    # Sample Information
    sample: Optional[str] = Field(None, alias="Sample")
    sample_evidence: str = Field("", alias="Sample_evidence")
    
    synthesis: Optional[str] = Field(None, alias="Synthesis")
    synthesis_evidence: str = Field("", alias="Synthesis_evidence")
    
    treatment: Optional[str] = Field(None, alias="Treatment")
    treatment_evidence: str = Field("", alias="Treatment_evidence")
    
    initial_sample_temperature_k: Optional[float] = Field(None, alias="Initial sample temperature (K)")
    initial_sample_temperature_k_evidence: str = Field("", alias="Initial sample temperature (K)_evidence")
    
    # Mechanical Properties
    yield_stress_mpa: Optional[float] = Field(None, alias="Yield stress (Mpa)")
    yield_stress_mpa_evidence: str = Field("", alias="Yield stress (Mpa)_evidence")
    
    ultimate_stress_mpa: Optional[float] = Field(None, alias="Ultimate stress (Mpa)")
    ultimate_stress_mpa_evidence: str = Field("", alias="Ultimate stress (Mpa)_evidence")
    
    kic_mpa_m05: Optional[float] = Field(None, alias="KIC (Mpa·m^0.5)")
    kic_mpa_m05_evidence: str = Field("", alias="KIC (Mpa·m^0.5)_evidence")
    
    hardness: Optional[float] = Field(None, alias="Hardness")
    hardness_evidence: str = Field("", alias="Hardness_evidence")
    
    b_gpa: Optional[float] = Field(None, alias="B (Gpa)")
    b_gpa_evidence: str = Field("", alias="B (Gpa)_evidence")
    
    g_gpa: Optional[float] = Field(None, alias="G (Gpa)")
    g_gpa_evidence: str = Field("", alias="G (Gpa)_evidence")
    
    e_gpa: Optional[float] = Field(None, alias="E (Gpa)")
    e_gpa_evidence: str = Field("", alias="E (Gpa)_evidence")
    
    mu: Optional[float] = Field(None, alias="Mu")
    mu_evidence: str = Field("", alias="Mu_evidence")
    
    melting_point_k: Optional[float] = Field(None, alias="Melting point (K)")
    melting_point_k_evidence: str = Field("", alias="Melting point (K)_evidence")
    
    # Sample Dimensions
    sample_thickness_mm: Optional[float] = Field(None, alias="Sample thickness (mm)")
    sample_thickness_mm_evidence: str = Field("", alias="Sample thickness (mm)_evidence")
    
    sample_diameter_mm: Optional[float] = Field(None, alias="Sample diameter (mm)")
    sample_diameter_mm_evidence: str = Field("", alias="Sample diameter (mm)_evidence")
    
    grain_size_um: Optional[float] = Field(None, alias="Grain size (µm)")
    grain_size_um_evidence: str = Field("", alias="Grain size (µm)_evidence")
    
    initial_density_g_cm3: Optional[float] = Field(None, alias="Initial density (g/cm³)")
    initial_density_g_cm3_evidence: str = Field("", alias="Initial density (g/cm³)_evidence")
    
    # Sound Speeds
    longitudinal_sound_speed_m_s: Optional[float] = Field(None, alias="Longitudinal sound speed (m/s)")
    longitudinal_sound_speed_m_s_evidence: str = Field("", alias="Longitudinal sound speed (m/s)_evidence")
    
    shear_sound_speed_m_s: Optional[float] = Field(None, alias="Shear sound speed (m/s)")
    shear_sound_speed_m_s_evidence: str = Field("", alias="Shear sound speed (m/s)_evidence")
    
    bulk_sound_speed_m_s: Optional[float] = Field(None, alias="Bulk sound speed (m/s)")
    bulk_sound_speed_m_s_evidence: str = Field("", alias="Bulk sound speed (m/s)_evidence")
    
    # Flyer Information
    flyer: Optional[str] = Field(None, alias="Flyer")
    flyer_evidence: str = Field("", alias="Flyer_evidence")
    
    flyer_processed: Optional[str] = Field(None, alias="Flyer (processed)")
    flyer_processed_evidence: str = Field("", alias="Flyer (processed)_evidence")
    
    flyer_thickness_mm: Optional[float] = Field(None, alias="Flyer thickness (mm)")
    flyer_thickness_mm_evidence: str = Field("", alias="Flyer thickness (mm)_evidence")
    
    flyer_diameter_mm: Optional[float] = Field(None, alias="Flyer diameter (mm)")
    flyer_diameter_mm_evidence: str = Field("", alias="Flyer diameter (mm)_evidence")
    
    # Experimental Conditions
    impact_velocity_m_s: Optional[float] = Field(None, alias="impact velocity (m/s)")
    impact_velocity_m_s_evidence: str = Field("", alias="impact velocity (m/s)_evidence")
    
    peak_stress_gpa: Optional[float] = Field(None, alias="Peak Stress (GPa)")
    peak_stress_gpa_evidence: str = Field("", alias="Peak Stress (GPa)_evidence")
    
    strain_rate_10_5_s_1: Optional[float] = Field(None, alias="Strain rate (10⁵ s⁻¹)")
    strain_rate_10_5_s_1_evidence: str = Field("", alias="Strain rate (10⁵ s⁻¹)_evidence")
    
    pulse_duration_us: Optional[float] = Field(None, alias="Pulse duration (µs)")
    pulse_duration_us_evidence: str = Field("", alias="Pulse duration (µs)_evidence")
    
    type_of_experiment: Optional[str] = Field(None, alias="Type of experiment")
    type_of_experiment_evidence: str = Field("", alias="Type of experiment_evidence")
    
    gas_gun_diameter_mm: Optional[float] = Field(None, alias="Gas gun diameter (mm)")
    gas_gun_diameter_mm_evidence: str = Field("", alias="Gas gun diameter (mm)_evidence")
    
    # Spall Results
    spall_gpa: Optional[float] = Field(None, alias="Spall (GPa)")
    spall_gpa_evidence: str = Field("", alias="Spall (GPa)_evidence")
    
    spall_direction: Optional[str] = Field(None, alias="Spall direction")
    spall_direction_evidence: str = Field("", alias="Spall direction_evidence")
    
    # References
    references: Optional[str] = Field(None, alias="Refereces")  # Note: typo in original header
    references_evidence: str = Field("", alias="Refereces_evidence")
    
    class Config:
        populate_by_name = True
