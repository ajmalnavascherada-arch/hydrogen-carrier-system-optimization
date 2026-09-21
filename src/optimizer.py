import numpy as np
import pandas as pd
from scipy.optimize import minimize



class HydrogenSystemOptimizer:

    def __init__(
        self,
        system,
        time_hours,
        renewable_power_kw,
        hydrogen_demand_kg_h,
        control_interval_hours=1.0,
    ):
        self.system = system
        self.time_hours = np.asarray(time_hours)
        self.renewable_power_kw = np.asarray(renewable_power_kw)
        self.hydrogen_demand_kg_h = np.asarray(hydrogen_demand_kg_h)

        self.control_interval_hours = control_interval_hours

        self.simulation_minutes = len(self.time_hours)

        # Number of optimization control points.
        # For a 24 h simulation with 1 h control intervals:
        # 24 decision variables.
        self.n_controls = int(
            np.ceil(
                (self.time_hours[-1] - self.time_hours[0])
                / self.control_interval_hours
            )
        )

        if self.n_controls < 1:
            self.n_controls = 1

    def expand_control_vector(self, control_vector):
        """
        Convert hourly control decisions into minute-resolution
        electrolyzer power commands.
        """

        control_vector = np.asarray(control_vector)

        renewable = self.renewable_power_kw

        control_times = np.linspace(
            self.time_hours[0],
            self.time_hours[-1],
            len(control_vector),
        )

        expanded_power = np.interp(
            self.time_hours,
            control_times,
            control_vector,
        )

        # Physical limits
        expanded_power = np.clip(
            expanded_power,
            0.0,
            np.minimum(
                renewable,
                self.system.p.electrolyzer_nominal_power_kw,
            ),
        )

        return expanded_power

    def evaluate(self, control_vector, return_results=False):

        electrolyzer_power = self.expand_control_vector(control_vector)

        # IMPORTANT:
        # Every optimization evaluation must start from the same
        # initial NH3 inventory.
        self.system.storage.level_kg = (
            self.system.p.ammonia_initial_storage_kg
        )

        results = self.system.simulate(
            self.time_hours,
            self.renewable_power_kw,
            self.hydrogen_demand_kg_h,
            electrolyzer_power_override=electrolyzer_power,
        )

        results = pd.DataFrame(results)

        unmet_h2 = results["unmet_h2_kg"].sum()

        curtailment = results["curtailed_energy_kwh"].sum()

        process_energy = (
            results["electrolyzer_energy_kwh"].sum()
            + results["nh3_synthesis_energy_kwh"].sum()
            + results["nh3_cracking_energy_kwh"].sum()
        )

        final_nh3 = results["nh3_storage_level_kg"].iloc[-1]

        initial_nh3 = self.system.p.ammonia_initial_storage_kg

        # Penalize depletion of the initial NH3 inventory.
        inventory_depletion = max(
            0.0,
            initial_nh3 - final_nh3,
        )

        # Primary objective:
        # minimize unmet hydrogen.
        #
        # Secondary objectives:
        # minimize curtailment and excessive process energy.
        #
        # Strong penalty for NH3 inventory depletion.
        objective = (
            100000.0 * unmet_h2
            + 1000.0 * inventory_depletion
            + 10.0 * curtailment
            + 0.01 * process_energy
        )

        if return_results:
            return objective, results

        return objective

    def optimize(self):

        renewable_limit = np.minimum(
            self.renewable_power_kw,
            self.system.p.electrolyzer_nominal_power_kw,
        )

        # Hourly renewable limits for optimization variables.
        control_times = np.linspace(
            self.time_hours[0],
            self.time_hours[-1],
            self.n_controls,
        )

        hourly_limits = np.interp(
            control_times,
            self.time_hours,
            renewable_limit,
        )

        bounds = [
            (0.0, float(limit))
            for limit in hourly_limits
        ]

        # Initial guess:
        # operate electrolyzer at available renewable power.
        initial_guess = hourly_limits.copy()

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

        objective, optimized_results = self.evaluate(
            result.x,
            return_results=True,
        )

        return result, optimized_results