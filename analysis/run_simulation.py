import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT)
)

from src.parameters import SystemParameters
from src.renewable_profile import (
    solar_profile,
    add_variability,
)
from src.hydrogen_demand import (
    variable_hydrogen_demand,
)
from src.system_model import (
    HydrogenCarrierSystem,
)


# ============================================================
# PARAMETERS
# ============================================================

params = SystemParameters()

dt_h = params.dt_s / 3600.0

n = int(
    params.simulation_hours /
    dt_h
)

time_hours = (
    pd.Series(range(n)) *
    dt_h
).values


# ============================================================
# RENEWABLE PROFILE
# ============================================================

solar_power = solar_profile(
    time_hours,
    params.electrolyzer_nominal_power_kw,
)

renewable_power = add_variability(
    solar_power,
    seed=42,
    variability=0.05,
)


# ============================================================
# HYDROGEN DEMAND
# ============================================================

hydrogen_demand = variable_hydrogen_demand(
    time_hours,
    params.hydrogen_demand_kg_h,
)


# ============================================================
# SYSTEM SIMULATION
# ============================================================

system = HydrogenCarrierSystem(
    params
)

results = system.simulate(
    time_hours,
    renewable_power,
    hydrogen_demand,
)


# ============================================================
# SAVE DATA
# ============================================================

data_directory = (
    ROOT / "data"
)

data_directory.mkdir(
    exist_ok=True
)
results = pd.DataFrame(results)
# ============================================================
# MASS AND ENERGY BALANCE CHECKS
# ============================================================

initial_nh3 = params.ammonia_initial_storage_kg
final_nh3 = results["nh3_storage_level_kg"].iloc[-1]

total_nh3_produced = results[
    "nh3_produced_kg"
].sum()

total_nh3_discharged = results[
    "nh3_discharged_kg"
].sum()

nh3_balance_error = (
    initial_nh3
    + total_nh3_produced
    - total_nh3_discharged
    - final_nh3
)

h2_balance_error = (
    results["h2_produced_kg"].sum()
    - results["h2_direct_kg"].sum()
    - results["h2_used_for_nh3_kg"].sum()
    - results["h2_unused_kg"].sum()
)

energy_balance_error = (
    results["renewable_energy_kwh"].sum()
    - results["electrolyzer_energy_kwh"].sum()
    - results["nh3_synthesis_energy_kwh"].sum()
    - results["nh3_cracking_energy_kwh"].sum()
    - results["curtailed_energy_kwh"].sum()
)

print()
print("========== BALANCE CHECKS ==========")

print(
    f"NH3 mass balance error: "
    f"{nh3_balance_error:.10f} kg"
)

print(
    f"H2 mass balance error: "
    f"{h2_balance_error:.10f} kg"
)

print(
    f"Energy balance error: "
    f"{energy_balance_error:.10f} kWh"
)
results.to_csv(
    data_directory /
    "simulation_results.csv",
    index=False,
)
# ============================================================
# SYSTEM SUMMARY
# ============================================================

renewable_energy = results["renewable_energy_kwh"].sum()

electrolyzer_energy = results[
    "electrolyzer_energy_kwh"
].sum()

synthesis_energy = results[
    "nh3_synthesis_energy_kwh"
].sum()

cracking_energy = results[
    "nh3_cracking_energy_kwh"
].sum()

total_process_energy = (
    electrolyzer_energy
    + synthesis_energy
    + cracking_energy
)

h2_produced = results[
    "h2_produced_kg"
].sum()

h2_demand = results[
    "h2_demand_kg"
].sum()

h2_direct = results[
    "h2_direct_kg"
].sum()

h2_from_nh3 = results[
    "h2_from_nh3_kg"
].sum()

unmet_h2 = results[
    "unmet_h2_kg"
].sum()

curtailed_energy = results[
    "curtailed_energy_kwh"
].sum()

peak_nh3_storage = results[
    "nh3_storage_level_kg"
].max()

minimum_nh3_storage = results[
    "nh3_storage_level_kg"
].min()

if h2_demand > 0:
    supply_coverage = (
        (h2_demand - unmet_h2)
        / h2_demand
        * 100
    )
else:
    supply_coverage = 100.0


print()
print("========== SYSTEM SUMMARY ==========")

print(
    f"Renewable energy: "
    f"{renewable_energy:.2f} kWh"
)

print(
    f"Electrolyzer energy: "
    f"{electrolyzer_energy:.2f} kWh"
)

print(
    f"NH3 synthesis energy: "
    f"{synthesis_energy:.2f} kWh"
)

print(
    f"NH3 cracking energy: "
    f"{cracking_energy:.2f} kWh"
)

print(
    f"Total process energy: "
    f"{total_process_energy:.2f} kWh"
)

print(
    f"H2 produced: "
    f"{h2_produced:.2f} kg"
)

print(
    f"H2 direct supply: "
    f"{h2_direct:.2f} kg"
)

print(
    f"H2 from NH3: "
    f"{h2_from_nh3:.2f} kg"
)

print(
    f"H2 demand: "
    f"{h2_demand:.2f} kg"
)

print(
    f"Unmet H2: "
    f"{unmet_h2:.4f} kg"
)

print(
    f"H2 supply coverage: "
    f"{supply_coverage:.2f} %"
)

print(
    f"Peak NH3 storage: "
    f"{peak_nh3_storage:.2f} kg"
)

print(
    f"Minimum NH3 storage: "
    f"{minimum_nh3_storage:.2f} kg"
)

print(
    f"Curtailed renewable energy: "
    f"{curtailed_energy:.2f} kWh"
)



# ============================================================
# PLOTS
# ============================================================

figure_directory = (
    ROOT /
    "results" /
    "figures"
)

figure_directory.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# Figure 1: Renewable and electrolyzer power
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(
    results["time_h"],
    results["renewable_power_kw"],
    label="Renewable power",
)

plt.plot(
    results["time_h"],
    results["electrolyzer_power_kw"],
    label="Electrolyzer power",
)

plt.xlabel("Time [h]")
plt.ylabel("Power [kW]")
plt.title(
    "Renewable Power and Electrolyzer Operation"
)

plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    figure_directory /
    "power_profile.png",
    dpi=200,
)

plt.show()


# ------------------------------------------------------------
# Figure 2: Hydrogen balance
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(
    results["time_h"],
    results["h2_demand_kg"],
    label="H2 demand",
)

plt.plot(
    results["time_h"],
    results["h2_direct_kg"],
    label="Direct H2",
)

plt.plot(
    results["time_h"],
    results["h2_from_nh3_kg"],
    label="H2 from NH3 cracking",
)

plt.plot(
    results["time_h"],
    results["unmet_h2_kg"],
    label="Unmet H2",
)

plt.xlabel("Time [h]")
plt.ylabel("Hydrogen flow [kg/h]")
plt.title(
    "Hydrogen Supply and Demand"
)

plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    figure_directory /
    "hydrogen_balance.png",
    dpi=200,
)

plt.show()


# ------------------------------------------------------------
# Figure 3: NH3 storage
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(
    results["time_h"],
    results["nh3_storage_level_kg"],
    label="NH3 storage",
)

plt.xlabel("Time [h]")
plt.ylabel("NH3 inventory [kg]")
plt.title(
    "Dynamic Ammonia Storage"
)

plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(
    figure_directory /
    "ammonia_storage.png",
    dpi=200,
)

plt.show()