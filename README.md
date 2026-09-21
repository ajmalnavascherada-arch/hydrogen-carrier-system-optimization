# Dynamic Modelling and Optimization of a Hydrogen Carrier System

> **Python-based dynamic simulation and optimization of a renewable-powered hydrogen carrier system using ammonia (NH₃) for hydrogen storage and reconversion.**

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python\&logoColor=white)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-Numerical%20Computing-013243?logo=numpy\&logoColor=white)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas\&logoColor=white)](https://pandas.pydata.org/)
[![SciPy](https://img.shields.io/badge/SciPy-Optimization-8CAAE6?logo=scipy\&logoColor=white)](https://scipy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557c)](https://matplotlib.org/)

---

## Overview

This project develops a **dynamic process model and optimization framework for a renewable-powered hydrogen carrier system**.

The model represents the conversion of variable renewable electricity into hydrogen, direct hydrogen utilization, conversion of excess hydrogen into ammonia, ammonia storage, and subsequent ammonia cracking to recover hydrogen when direct renewable-powered hydrogen production is insufficient.

The objective is to investigate how **dynamic operation and electrolyzer scheduling** can improve the utilization of renewable electricity while maintaining hydrogen supply and respecting ammonia storage constraints.

The project combines:

* Renewable energy modelling
* Electrolyzer operation
* Hydrogen production
* Hydrogen demand modelling
* Ammonia synthesis
* Ammonia storage dynamics
* Ammonia cracking
* Dynamic mass balances
* Energy balances
* Hydrogen supply tracking
* Numerical optimization
* Engineering data analysis

---

## System Architecture

The simulated energy and material flow is:

```text
                  Renewable Electricity
                           │
                           ▼
                    ┌─────────────┐
                    │ Electrolyzer│
                    └──────┬──────┘
                           │
                           │ H₂
                           ▼
                    ┌──────────────┐
                    │ H₂ Allocation │
                    └──────┬───────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
          Direct H₂ Demand      Excess H₂
                                      │
                                      ▼
                              ┌──────────────┐
                              │ NH₃ Synthesis│
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ NH₃ Storage  │
                              └──────┬───────┘
                                     │
                                     │ NH₃
                                     ▼
                              ┌──────────────┐
                              │ NH₃ Cracking │
                              └──────┬───────┘
                                     │
                                     │ H₂
                                     ▼
                              Hydrogen Demand
```

The model prioritizes direct hydrogen supply from the electrolyzer. Excess hydrogen can be routed through the ammonia pathway, while stored ammonia can subsequently be cracked to provide hydrogen during periods of insufficient direct production.

---

## Engineering Objective

The central engineering problem is the operation of an electrolyzer under a **time-varying renewable power supply and hydrogen demand**.

The model investigates:

1. How much hydrogen can be supplied directly from renewable-powered electrolysis?
2. How can excess hydrogen be converted into a storable carrier?
3. How does ammonia storage support hydrogen availability during renewable fluctuations?
4. How much hydrogen demand remains unmet?
5. How does electrolyzer scheduling influence system performance?
6. Can optimization reduce hydrogen shortage while preserving the ammonia inventory?

The optimization therefore considers both the **instantaneous energy system** and the **dynamic state of the ammonia storage system**.

---

# Model Components

## 1. Renewable Power Profile

A synthetic solar-based renewable power profile is generated for the simulation period.

The renewable input represents the time-dependent electrical power available to the electrolyzer and downstream processes.

The model supports:

* Variable renewable power
* Peak power limitations
* Time-dependent operation
* Renewable intermittency

---

## 2. Electrolyzer Model

The electrolyzer converts renewable electricity into hydrogen.

The model considers:

* Nominal electrolyzer power
* Minimum operating load
* Load-dependent efficiency
* Hydrogen lower heating value
* Hydrogen production rate
* Electrical energy consumption

The hydrogen production rate is determined from the electrical input and electrolyzer efficiency.

A simplified energy relationship is:

$$
\dot{m}_{H_2} = \frac{P_{el}\eta_{el}}{LHV_{H_2}}
$$

where:

- $P_{el}$ = electrolyzer electrical power
- $\eta_{el}$ = electrolyzer efficiency
- $LHV_{H_2}$ = hydrogen lower heating value
- $\dot{m}_{H_2}$ = hydrogen production rate



---

## 3. Hydrogen Demand

The system includes a time-dependent hydrogen demand profile.

The demand model allows the simulation to evaluate:

* Hydrogen supply
* Hydrogen shortage
* Direct hydrogen utilization
* Hydrogen recovered from ammonia
* Total hydrogen coverage

The main performance metric is:



**H₂ Coverage (%) = (1 − Unmet H₂ / Total H₂ Demand) × 100**

---

## 4. Ammonia Synthesis

Excess hydrogen can be converted into ammonia.

The stoichiometric relationship is based on:

$$
N_2 + 3H_2 \rightarrow 2NH_3
$$

The model converts hydrogen mass to ammonia mass using the corresponding molar-mass ratio and applies an assumed synthesis efficiency.

The implementation also considers the energy required for ammonia synthesis.

---

## 5. Ammonia Storage

Ammonia acts as the intermediate hydrogen carrier.

The storage model tracks:

* Initial inventory
* Storage level
* Storage capacity
* Charging
* Discharging
* State of charge

The storage state is updated dynamically during the simulation.

The model prevents the storage inventory from exceeding its physical capacity or becoming negative.

---

## 6. Ammonia Cracking

When direct hydrogen production is insufficient, stored ammonia can be cracked to recover hydrogen.

The process follows the reverse stoichiometric relationship:

$$
2NH_3 \rightarrow N_2 + 3H_2
$$

The model includes a cracking efficiency and an associated energy requirement.

The available renewable energy is therefore shared between:

* Electrolysis
* Ammonia synthesis
* Ammonia cracking

---

# Dynamic System Model

The system operates using a discrete time-stepping approach.

For each simulation step:

```text
Renewable power
      │
      ▼
Electrolyzer dispatch
      │
      ▼
H₂ production
      │
      ├──────────────► Direct H₂ demand
      │
      ▼
Excess H₂
      │
      ▼
NH₃ synthesis
      │
      ▼
NH₃ storage
      │
      ▼
NH₃ cracking when required
      │
      ▼
Additional H₂ supply
```

The model tracks both **mass flows and energy flows** throughout the system.

---

# Mass Balance Validation

A key feature of the project is explicit conservation-law validation.

## Hydrogen balance

The hydrogen balance accounts for:

* Hydrogen produced by electrolysis
* Direct hydrogen demand
* Hydrogen consumed for ammonia synthesis
* Unused hydrogen

The implementation checks:

**H₂ produced − H₂ direct − H₂ used for NH₃ − H₂ unused = 0** 

---

## Ammonia balance

The ammonia storage balance is:



**NH₃ initial + NH₃ produced − NH₃ discharged − NH₃ final = 0**

This ensures that ammonia inventory is conserved throughout the simulation.

---

## Energy balance

The renewable electricity balance accounts for:

* Electrolyzer electricity consumption
* Ammonia synthesis energy
* Ammonia cracking energy
* Renewable electricity curtailment

The model verifies:

**Renewable Energy = Electrolyzer Energy + NH₃ Synthesis Energy + NH₃ Cracking Energy + Curtailed Energy**

These checks are important because optimization results are only meaningful if the underlying dynamic model remains physically consistent.

---

# Optimization Framework

The optimization problem determines an improved electrolyzer operating schedule under a variable renewable power supply.

Instead of optimizing all individual simulation time steps independently, the control problem is reduced to a lower-resolution schedule.

For the current implementation:

```text
1-minute simulation
       │
       ▼
24-hour simulation
       │
       ▼
24 hourly optimization variables
       │
       ▼
Interpolation
       │
       ▼
1-minute electrolyzer power schedule
```

This reduces the optimization problem from potentially thousands of variables to a manageable set of engineering control decisions.

The optimized control vector is expanded to the full simulation resolution before being evaluated by the dynamic system model.

---

## Optimization Objective

The optimization prioritizes hydrogen availability.

The objective function includes penalties for:

1. Unmet hydrogen demand
2. Depletion of the initial ammonia inventory
3. Renewable energy curtailment
4. Excessive process energy consumption

Conceptually:

$$
J =
w_1 U_{H_2}
+
w_2 D_{NH_3}
+
w_3 E_{curtail}
+
w_4 E_{process}
$$

where:

- $$U_{H_2}$$ = unmet hydrogen demand
- $$D_{NH_3}$$ = depletion of the initial ammonia inventory
- $$E_{curtail}$$ = curtailed renewable energy
- $$E_{process}$$ = process energy consumption
- $$w_{i}$$ = objective-function weighting factors

The optimization uses **SciPy SLSQP** with physically meaningful electrolyzer power bounds.

---

# Baseline vs Optimized Operation

The project evaluates two operating strategies.

### Baseline

The electrolyzer follows the available renewable power up to its nominal operating limit.

### Optimized

The electrolyzer power is controlled according to the optimization result while remaining constrained by:

* Available renewable power
* Electrolyzer nominal power
* Dynamic system behaviour
* Hydrogen demand
* Ammonia storage state

The resulting simulations can be compared using:

* H₂ coverage
* Unmet H₂
* Renewable curtailment
* Electrolyzer utilization
* NH₃ production
* NH₃ storage level
* NH₃ consumption
* Process energy consumption

---

# Key Model Parameters

The current model uses representative engineering parameters including:

| Parameter                       |          Value |
| ------------------------------- | -------------: |
| Simulation duration             |           24 h |
| Simulation time step            |           60 s |
| Electrolyzer nominal power      |         100 kW |
| Minimum electrolyzer load       |            10% |
| Nominal electrolyzer efficiency |            68% |
| H₂ LHV                          |   33.33 kWh/kg |
| NH₃ synthesis efficiency        |            90% |
| NH₃ cracking efficiency         |            85% |
| NH₃ synthesis energy            | 9.5 kWh/kg NH₃ |
| NH₃ cracking energy             | 4.5 kWh/kg NH₃ |
| NH₃ storage capacity            |         100 kg |
| Initial NH₃ inventory           |          20 kg |
| Base H₂ demand                  |      0.70 kg/h |
| Renewable peak power            |         100 kW |

> **Note:** These values represent the current simulation configuration and are intended for modelling and methodology development rather than direct plant-design specifications.

---

# Project Structure

```text
hydrogen-carrier-system-optimization/
│
├── src/
│   ├── __init__.py
│   ├── parameters.py
│   ├── renewable_profile.py
│   ├── electrolyzer.py
│   ├── ammonia.py
│   ├── storage.py
│   ├── hydrogen_demand.py
│   ├── system_model.py
│   └── optimizer.py
│
├── analysis/
│   ├── run_simulation.py
│   └── run_optimization.py
│
├── data/
│   ├── baseline_results.csv
│   ├── optimized_results.csv
│   └── optimization_profile.csv
│
├── results/
│   └── figures/
│
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Technologies

### Programming

* Python

### Numerical Computing

* NumPy

### Data Processing

* Pandas

### Optimization

* SciPy

### Visualization

* Matplotlib

### Engineering Applications

* Hydrogen systems
* Electrolysis
* Ammonia as a hydrogen carrier
* Renewable energy integration
* Dynamic process modelling
* Energy-system optimization
* Mass and energy balance analysis

---



The optimization workflow:

```text
Generate renewable profile
        ↓
Generate hydrogen demand
        ↓
Run baseline simulation
        ↓
Define optimization problem
        ↓
Optimize electrolyzer dispatch
        ↓
Run optimized dynamic simulation
        ↓
Compare baseline vs optimized operation
        ↓
Save CSV results
```

---

# Generated Data

The analysis scripts generate:

### `baseline_results.csv`

Minute-resolution results from the baseline system.

### `optimized_results.csv`

Minute-resolution results from the optimized system.

### `optimization_profile.csv`

Combined time-series data containing:

* Renewable power
* Baseline electrolyzer power
* Optimized electrolyzer power
* Hydrogen demand

These files allow the simulation results to be independently inspected and further analyzed.

---

# Results and Visualization

The project is designed to generate engineering visualizations comparing baseline and optimized operation.

Recommended analyses include:

### Renewable Power

```text
Renewable power vs time
```

### Electrolyzer Dispatch

```text
Baseline electrolyzer power
vs
Optimized electrolyzer power
```

### Hydrogen Supply

```text
Hydrogen demand
vs
Direct H₂ supply
vs
NH₃-derived H₂ supply
```

### Ammonia Storage

```text
NH₃ storage level vs time
```

### Energy Utilization

```text
Renewable energy
→ Electrolysis
→ NH₃ synthesis
→ NH₃ cracking
→ Curtailment
```

---

# Engineering Insights

The model is designed to demonstrate several important characteristics of renewable-powered hydrogen systems:

### Renewable intermittency

Electrolyzer operation is constrained by time-varying renewable electricity availability.

### Hydrogen storage requirement

Direct electrolysis alone may not satisfy hydrogen demand during periods of insufficient renewable generation.

### Chemical hydrogen carriers

Ammonia provides a mechanism for storing hydrogen in a chemically bound form and recovering it later through cracking.

### Storage dynamics

The value of ammonia storage depends not only on its capacity but also on its state of charge and the timing of hydrogen demand.

### Integrated optimization

Optimizing the electrolyzer without considering downstream storage dynamics can produce misleading results. The current framework therefore evaluates candidate operating schedules through the complete dynamic system model.

---

# Current Limitations

This project is an engineering modelling and optimization study rather than a detailed industrial plant simulator.

Current simplifications include:

* Simplified electrolyzer efficiency representation
* Simplified ammonia synthesis model
* Simplified ammonia cracking model
* Synthetic renewable power profile
* Simplified hydrogen demand profile
* Constant process-specific energy consumption parameters
* No detailed thermodynamic equilibrium calculations
* No detailed catalyst kinetics
* No compressor model
* No nitrogen separation model
* No heat integration model
* No detailed equipment sizing
* No capital or operating cost model

The results should therefore be interpreted as **system-level modelling results**, not as final equipment-design specifications.

---

# Future Development

Potential extensions include:

* [ ] Thermodynamic ammonia synthesis modelling
* [ ] Detailed ammonia cracking kinetics
* [ ] Electrolyzer degradation modelling
* [ ] Temperature-dependent process efficiency
* [ ] Dynamic heat integration
* [ ] Hydrogen compression modelling
* [ ] Nitrogen separation and purification
* [ ] Multi-day renewable profiles
* [ ] Real weather/renewable datasets
* [ ] Electricity-price optimization
* [ ] Hydrogen production cost calculation
* [ ] Levelized cost of hydrogen (LCOH)
* [ ] Multi-objective optimization
* [ ] Model Predictive Control (MPC)
* [ ] Mixed-integer operating constraints
* [ ] Equipment sizing optimization
* [ ] Sensitivity analysis
* [ ] Uncertainty analysis
* [ ] Automated test coverage
* [ ] Interactive result visualization

---

# Reproducibility

The model is structured so that the major system parameters are centralized in:

```text
src/parameters.py
```

The dynamic system model is implemented in:

```text
src/system_model.py
```

and the optimization framework is implemented in:

```text
src/optimizer.py
```

This separation makes it possible to modify individual subsystem assumptions without rewriting the complete simulation workflow.

---

# Validation Philosophy

A central design principle of this project is:

> **An optimization result is only meaningful if the underlying physical model satisfies its conservation laws.**

Therefore, the simulation explicitly checks:

```text
Hydrogen mass balance
Ammonia mass balance
Renewable energy balance
Storage constraints
```

This provides a basic physical consistency layer before interpreting optimization results.

---

# Author

**Ajmal Navas**

M.Sc. Chemical and Energy Engineering
Otto von Guericke University Magdeburg, Germany

Areas of interest:

* Hydrogen technologies
* Renewable energy systems
* Process engineering
* Energy-system modelling
* Electrochemical systems
* Battery and energy-storage technologies
* Python-based engineering simulation
* System optimization

---

# License

This project is intended for educational, research, and portfolio purposes.

A formal open-source license can be added if the project is later released for external reuse.
