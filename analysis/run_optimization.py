from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
import numpy as np
import pandas as pd
from scipy.optimize import minimize


class HydrogenSystemOptimizer:
    """
    Dynamic optimizer for the renewable-powered hydrogen carrier system.

    The optimizer controls electrolyzer power at a reduced hourly resolution
    while the underlying system model operates at the simulation resolution
    (e.g. 1-minute time steps).

    Optimization objectives:
        1. Minimize unmet hydrogen demand.
        2. Preserve the initial ammonia inventory.
        3. Minimize renewable-energy curtailment.
        4. Avoid unnecessary process energy consumption.

    The optimization uses the complete dynamic system model, including:
        - Electrolyzer
        - Direct hydrogen demand
        - Ammonia synthesis
        - Ammonia storage
        - Ammonia cracking
        - Hydrogen demand
        - Renewable energy limitations
    """

    def __init__(
        self,
        system,
        time_hours,
        renewable_power_kw,
        hydrogen_demand_kg_h,
        control_interval_hours=1.0,
    ):
        """
        Parameters
        ----------
        system : HydrogenCarrierSystem
            Dynamic hydrogen carrier system model.

        time_hours : array-like
            Simulation time vector in hours.

        renewable_power_kw : array-like
            Renewable electrical power profile in kW.

        hydrogen_demand_kg_h : array-like
            Hydrogen demand profile in kg/h.

        control_interval_hours : float, optional
            Time interval between optimization control points.
            Default = 1 hour.
        """

        self.system = system

        self.time_hours = np.asarray(
            time_hours,
            dtype=float,
        )

        self.renewable_power_kw = np.asarray(
            renewable_power_kw,
            dtype=float,
        )

        self.hydrogen_demand_kg_h = np.asarray(
            hydrogen_demand_kg_h,
            dtype=float,
        )

        self.control_interval_hours = float(
            control_interval_hours
        )

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if len(self.time_hours) == 0:
            raise ValueError(
                "time_hours cannot be empty."
            )

        if len(self.renewable_power_kw) != len(
            self.time_hours
        ):
            raise ValueError(
                "renewable_power_kw and time_hours "
                "must have the same length."
            )

        if len(self.hydrogen_demand_kg_h) != len(
            self.time_hours
        ):
            raise ValueError(
                "hydrogen_demand_kg_h and time_hours "
                "must have the same length."
            )

        if self.control_interval_hours <= 0:
            raise ValueError(
                "control_interval_hours must be greater than zero."
            )

        # ----------------------------------------------------
        # Determine number of optimization variables
        # ----------------------------------------------------

        simulation_duration_hours = (
            self.time_hours[-1]
            - self.time_hours[0]
        )

        self.n_controls = int(
            np.ceil(
                simulation_duration_hours
                / self.control_interval_hours
            )
        )

        self.n_controls = max(
            1,
            self.n_controls,
        )

        # ----------------------------------------------------
        # Store optimized power profile
        # ----------------------------------------------------

        self.optimized_power = None

        # ----------------------------------------------------
        # Store optimization results
        # ----------------------------------------------------

        self.last_results = None

    # ========================================================
    # CONTROL VECTOR EXPANSION
    # ========================================================

    def expand_control_vector(
        self,
        control_vector,
    ):
        """
        Convert the reduced-resolution optimization vector
        into a full simulation-resolution electrolyzer power
        profile.

        Example:

            24 hourly optimization variables
                    ↓
            interpolation
                    ↓
            1440 one-minute power values
        """

        control_vector = np.asarray(
            control_vector,
            dtype=float,
        )

        if len(control_vector) != self.n_controls:
            raise ValueError(
                f"Expected {self.n_controls} control variables, "
                f"received {len(control_vector)}."
            )

        # ----------------------------------------------------
        # Construct optimization control times
        # ----------------------------------------------------

        control_times = (
            self.time_hours[0]
            + np.arange(self.n_controls)
            * self.control_interval_hours
        )

        # Make sure the control time vector does not extend
        # unnecessarily beyond the simulation period.
        control_times = np.minimum(
            control_times,
            self.time_hours[-1],
        )

        # Remove duplicate control times if the simulation
        # duration is shorter than the requested interval.
        control_times, unique_indices = np.unique(
            control_times,
            return_index=True,
        )

        control_values = control_vector[
            unique_indices
        ]

        # ----------------------------------------------------
        # Interpolate hourly control to simulation resolution
        # ----------------------------------------------------

        expanded_power = np.interp(
            self.time_hours,
            control_times,
            control_values,
        )

        # ----------------------------------------------------
        # Apply physical electrolyzer constraints
        # ----------------------------------------------------

        maximum_power = np.minimum(
            self.renewable_power_kw,
            self.system.p.electrolyzer_nominal_power_kw,
        )

        expanded_power = np.clip(
            expanded_power,
            0.0,
            maximum_power,
        )

        return expanded_power

    # ========================================================
    # OBJECTIVE EVALUATION
    # ========================================================

    def evaluate(
        self,
        control_vector,
        return_results=False,
    ):
        """
        Evaluate one candidate electrolyzer operating strategy.

        Parameters
        ----------
        control_vector : array-like
            Reduced-resolution electrolyzer power schedule.

        return_results : bool
            If True, return both objective value and simulation
            results.

        Returns
        -------
        float
            Objective value.

        or

        tuple
            (objective_value, results_dataframe)
        """

        # ----------------------------------------------------
        # Convert reduced control vector to full-resolution
        # power profile.
        # ----------------------------------------------------

        electrolyzer_power = (
            self.expand_control_vector(
                control_vector
            )
        )

        # ----------------------------------------------------
        # Reset dynamic storage state before every evaluation.
        #
        # This is essential because the optimizer evaluates
        # hundreds of candidate solutions. Every candidate
        # must start from exactly the same physical state.
        # ----------------------------------------------------

        self.system.storage.level_kg = (
            self.system.p.ammonia_initial_storage_kg
        )

        # ----------------------------------------------------
        # Run complete dynamic system simulation
        # ----------------------------------------------------

        results = self.system.simulate(
            self.time_hours,
            self.renewable_power_kw,
            self.hydrogen_demand_kg_h,
            electrolyzer_power_override=electrolyzer_power,
        )

        # ----------------------------------------------------
        # Convert list of dictionaries to DataFrame
        # ----------------------------------------------------

        results = pd.DataFrame(
            results
        )

        # ----------------------------------------------------
        # Hydrogen performance
        # ----------------------------------------------------

        unmet_h2 = results[
            "unmet_h2_kg"
        ].sum()

        # ----------------------------------------------------
        # Renewable curtailment
        # ----------------------------------------------------

        curtailment = results[
            "curtailed_energy_kwh"
        ].sum()

        # ----------------------------------------------------
        # Process energy consumption
        # ----------------------------------------------------

        electrolyzer_energy = results[
            "electrolyzer_energy_kwh"
        ].sum()

        synthesis_energy = results[
            "nh3_synthesis_energy_kwh"
        ].sum()

        cracking_energy = results[
            "nh3_cracking_energy_kwh"
        ].sum()

        process_energy = (
            electrolyzer_energy
            + synthesis_energy
            + cracking_energy
        )

        # ----------------------------------------------------
        # NH3 inventory preservation
        # ----------------------------------------------------

        initial_nh3 = (
            self.system.p.ammonia_initial_storage_kg
        )

        final_nh3 = results[
            "nh3_storage_level_kg"
        ].iloc[-1]

        inventory_depletion = max(
            0.0,
            initial_nh3 - final_nh3,
        )

        # ----------------------------------------------------
        # Optional additional penalty for excessive NH3
        # production/storage cycling.
        #
        # We do not strongly penalize NH3 production itself,
        # because ammonia is an intended hydrogen carrier.
        # ----------------------------------------------------

        total_nh3_produced = results[
            "nh3_produced_kg"
        ].sum()

        # ----------------------------------------------------
        # Objective function
        # ----------------------------------------------------
        #
        # Primary objective:
        #     unmet hydrogen demand
        #
        # Secondary:
        #     preserve initial NH3 inventory
        #
        # Tertiary:
        #     reduce curtailment
        #
        # Small process-energy penalty:
        #     avoid unnecessary operation
        #
        # ----------------------------------------------------

        unmet_h2_penalty = (
            100000.0
            * unmet_h2
        )

        inventory_penalty = (
            10000.0
            * inventory_depletion
        )

        curtailment_penalty = (
            10.0
            * curtailment
        )

        energy_penalty = (
            0.01
            * process_energy
        )

        objective = (
            unmet_h2_penalty
            + inventory_penalty
            + curtailment_penalty
            + energy_penalty
        )

        # ----------------------------------------------------
        # Store latest results
        # ----------------------------------------------------

        self.last_results = results

        if return_results:
            return (
                objective,
                results,
            )

        return objective

    # ========================================================
    # OPTIMIZATION
    # ========================================================

    def optimize(self):
        """
        Perform the dynamic electrolyzer scheduling optimization.

        Returns
        -------
        result : scipy.optimize.OptimizeResult
            Optimization result from SciPy.

        optimized_results : pandas.DataFrame
            Full dynamic simulation results corresponding to
            the optimized operating strategy.
        """

        # ----------------------------------------------------
        # Maximum physically available electrolyzer power
        # ----------------------------------------------------

        renewable_limit = np.minimum(
            self.renewable_power_kw,
            self.system.p.electrolyzer_nominal_power_kw,
        )

        # ----------------------------------------------------
        # Create reduced-resolution control times
        # ----------------------------------------------------

        control_times = (
            self.time_hours[0]
            + np.arange(self.n_controls)
            * self.control_interval_hours
        )

        # Keep control times inside simulation horizon.
        control_times = np.minimum(
            control_times,
            self.time_hours[-1],
        )

        # Remove duplicates.
        control_times = np.unique(
            control_times
        )

        # ----------------------------------------------------
        # Calculate power bounds for each control variable.
        # ----------------------------------------------------

        hourly_limits = np.interp(
            control_times,
            self.time_hours,
            renewable_limit,
        )

        bounds = [
            (
                0.0,
                float(limit),
            )
            for limit in hourly_limits
        ]

        # ----------------------------------------------------
        # Initial guess
        #
        # Start from maximum available renewable power.
        # This corresponds approximately to the baseline
        # operating strategy.
        # ----------------------------------------------------

        initial_guess = hourly_limits.copy()

        # ----------------------------------------------------
        # Make sure the initial guess has the same length as
        # the number of bounds.
        # ----------------------------------------------------

        if len(initial_guess) != len(bounds):
            raise RuntimeError(
                "Initial guess and optimization bounds "
                "have different lengths."
            )

        # ----------------------------------------------------
        # Run SLSQP optimization
        # ----------------------------------------------------

        result = minimize(
            self.evaluate,
            initial_guess,
            method="SLSQP",
            bounds=bounds,
            options={
                "maxiter": 200,
                "ftol": 1e-6,
                "disp": True,
            },
        )

        # ----------------------------------------------------
        # Expand optimized hourly control schedule into
        # simulation-resolution power profile.
        # ----------------------------------------------------

        self.optimized_power = (
            self.expand_control_vector(
                result.x
            )
        )

        # ----------------------------------------------------
        # Run one final simulation using the optimized
        # operating strategy.
        # ----------------------------------------------------

        objective, optimized_results = (
            self.evaluate(
                result.x,
                return_results=True,
            )
        )

        # ----------------------------------------------------
        # Store final results
        # ----------------------------------------------------

        self.last_results = optimized_results

        return (
            result,
            optimized_results,
        )