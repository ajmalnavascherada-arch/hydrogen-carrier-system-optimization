from dataclasses import dataclass


@dataclass
class SystemParameters:
    # -----------------------------
    # Simulation
    # -----------------------------
    dt_s: float = 60.0
    simulation_hours: float = 24.0

    # -----------------------------
    # Electrolyzer
    # -----------------------------
    electrolyzer_nominal_power_kw: float = 100.0
    electrolyzer_min_load: float = 0.10
    electrolyzer_nominal_efficiency: float = 0.68

    # Lower heating value of hydrogen
    h2_lhv_kwh_kg: float = 33.33

    # -----------------------------
    # Ammonia process
    # -----------------------------
    h2_molar_mass: float = 2.016
    nh3_molar_mass: float = 17.031

    ammonia_synthesis_efficiency: float = 0.90
    ammonia_cracking_efficiency: float = 0.85

    # Electricity required by process units
    # These are configurable engineering assumptions.
    ammonia_synthesis_energy_kwh_per_kg: float = 9.5
    ammonia_cracking_energy_kwh_per_kg: float = 4.5

    # -----------------------------
    # NH3 storage
    # -----------------------------
    ammonia_storage_capacity_kg: float = 100.0
    ammonia_initial_storage_kg: float = 20.0

    # -----------------------------
    # Hydrogen demand
    # -----------------------------
    hydrogen_demand_kg_h: float = 0.70

    # -----------------------------
    # Renewable generation
    # -----------------------------
    renewable_peak_power_kw: float = 100.0