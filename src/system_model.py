import numpy as np

from .parameters import SystemParameters
from .electrolyzer import Electrolyzer
from .ammonia import AmmoniaProcess
from .storage import AmmoniaStorage


class HydrogenCarrierSystem:

    def __init__(self, parameters: SystemParameters):

        self.p = parameters

        self.electrolyzer = Electrolyzer(
            nominal_power_kw=parameters.electrolyzer_nominal_power_kw,
            minimum_load=parameters.electrolyzer_min_load,
            nominal_efficiency=parameters.electrolyzer_nominal_efficiency,
            h2_lhv_kwh_kg=parameters.h2_lhv_kwh_kg,
        )

        self.ammonia = AmmoniaProcess(
            h2_molar_mass=parameters.h2_molar_mass,
            nh3_molar_mass=parameters.nh3_molar_mass,
            synthesis_efficiency=parameters.ammonia_synthesis_efficiency,
            cracking_efficiency=parameters.ammonia_cracking_efficiency,
        )

        self.storage = AmmoniaStorage(
            capacity_kg=parameters.ammonia_storage_capacity_kg,
            initial_level_kg=parameters.ammonia_initial_storage_kg,
        )

    def simulate(
            self,
            time_hours,
            renewable_power_kw,
            hydrogen_demand_kg_h,
            electrolyzer_power_override=None,
    ):

        dt_h = self.p.dt_s / 3600.0

        results = []

        for i, time in enumerate(time_hours):

            renewable_power = max(
                0.0,
                renewable_power_kw[i]
            )

            demand = max(
                0.0,
                hydrogen_demand_kg_h[i]
            ) * dt_h

            renewable_energy = renewable_power * dt_h

            # ==================================================
            # 1. ELECTROLYZER
            # ==================================================

            if electrolyzer_power_override is None:

                electrolyzer_power = min(
                    renewable_power,
                    self.p.electrolyzer_nominal_power_kw
                )

            else:

                electrolyzer_power = min(
                    max(
                        0.0,
                        electrolyzer_power_override[i]
                    ),
                    renewable_power,
                    self.p.electrolyzer_nominal_power_kw
                )

            electrolyzer_output = self.electrolyzer.operate(
                electrolyzer_power
            )

            electrolyzer_energy = (
                electrolyzer_output["power_kw"] * dt_h
            )

            h2_produced = (
                electrolyzer_output["hydrogen_kg_h"] * dt_h
            )

            # ==================================================
            # 2. DIRECT H2 SUPPLY
            # ==================================================

            h2_direct = min(
                h2_produced,
                demand
            )

            remaining_demand = (
                demand - h2_direct
            )

            h2_excess = max(
                0.0,
                h2_produced - h2_direct
            )

            # ==================================================
            # 3. EXCESS H2 -> NH3 SYNTHESIS
            # ==================================================

            nh3_produced = self.ammonia.h2_to_nh3(
                h2_excess
            )

            synthesis_energy = (
                nh3_produced
                * self.p.ammonia_synthesis_energy_kwh_per_kg
            )

            # Available renewable energy after electrolyzer
            remaining_energy = max(
                0.0,
                renewable_energy - electrolyzer_energy
            )

            # Limit NH3 synthesis by available energy
            if synthesis_energy > remaining_energy:

                nh3_energy_limited = (
                    remaining_energy
                    / self.p.ammonia_synthesis_energy_kwh_per_kg
                )

                nh3_produced = min(
                    nh3_produced,
                    nh3_energy_limited
                )

                synthesis_energy = (
                    nh3_produced
                    * self.p.ammonia_synthesis_energy_kwh_per_kg
                )

            # Store NH3
            nh3_stored = self.storage.charge(
                nh3_produced
            )
            # Actual H2 consumed by the NH3 synthesis process
            theoretical_nh3_per_h2 = (
                                             2 * self.p.nh3_molar_mass
                                     ) / (
                                             3 * self.p.h2_molar_mass
                                     )

            h2_used_for_nh3 = (
                    nh3_produced
                    / (
                            theoretical_nh3_per_h2
                            * self.p.ammonia_synthesis_efficiency
                    )
            )

            # H2 that could not be used directly or converted to NH3
            h2_unused = max(
                0.0,
                h2_produced
                - h2_direct
                - h2_used_for_nh3
            )
            # ==================================================
            # 4. NH3 -> H2 CRACKING
            # ==================================================

            h2_from_nh3 = 0.0
            nh3_discharged = 0.0
            cracking_energy = 0.0

            if remaining_demand > 0:

                theoretical_h2_per_nh3 = (
                    3 * self.p.h2_molar_mass
                ) / (
                    2 * self.p.nh3_molar_mass
                )

                effective_h2_per_nh3 = (
                    theoretical_h2_per_nh3
                    * self.p.ammonia_cracking_efficiency
                )

                nh3_needed = (
                    remaining_demand
                    / effective_h2_per_nh3
                )

                nh3_available = self.storage.level_kg

                nh3_discharged = min(
                    nh3_needed,
                    nh3_available
                )

                potential_h2 = self.ammonia.nh3_to_h2(
                    nh3_discharged
                )

                required_cracking_energy = (
                    nh3_discharged
                    * self.p.ammonia_cracking_energy_kwh_per_kg
                )

                # Limit cracking by remaining renewable energy
                remaining_energy_after_synthesis = max(
                    0.0,
                    renewable_energy
                    - electrolyzer_energy
                    - synthesis_energy
                )

                if (
                    required_cracking_energy
                    > remaining_energy_after_synthesis
                ):

                    max_nh3_crackable = (
                        remaining_energy_after_synthesis
                        / self.p.ammonia_cracking_energy_kwh_per_kg
                    )

                    nh3_discharged = min(
                        nh3_discharged,
                        max_nh3_crackable
                    )

                    potential_h2 = self.ammonia.nh3_to_h2(
                        nh3_discharged
                    )

                    required_cracking_energy = (
                        nh3_discharged
                        * self.p.ammonia_cracking_energy_kwh_per_kg
                    )

                h2_from_nh3 = potential_h2

                cracking_energy = (
                    required_cracking_energy
                )

                self.storage.discharge(
                    nh3_discharged
                )

            # ==================================================
            # 5. FINAL H2 BALANCE
            # ==================================================

            total_h2_supplied = (
                h2_direct
                + h2_from_nh3
            )

            unmet_h2 = max(
                0.0,
                demand - total_h2_supplied
            )

            # ==================================================
            # 6. ENERGY BALANCE
            # ==================================================

            total_process_energy = (
                electrolyzer_energy
                + synthesis_energy
                + cracking_energy
            )

            curtailed_energy = max(
                0.0,
                renewable_energy
                - total_process_energy
            )

            # ==================================================
            # 7. STORAGE
            # ==================================================

            storage_level = self.storage.level_kg

            storage_soc = (
                self.storage.state_of_charge()
            )

            # ==================================================
            # 8. RESULTS
            # ==================================================

            results.append({

                "time_h":
                    time,

                "renewable_power_kw":
                    renewable_power,

                "renewable_energy_kwh":
                    renewable_energy,

                "electrolyzer_power_kw":
                    electrolyzer_output["power_kw"],

                "electrolyzer_efficiency":
                    electrolyzer_output["efficiency"],

                "electrolyzer_energy_kwh":
                    electrolyzer_energy,

                "h2_produced_kg":
                    h2_produced,

                "h2_direct_kg":
                    h2_direct,

                "h2_from_nh3_kg":
                    h2_from_nh3,
                "h2_used_for_nh3_kg":
                    h2_used_for_nh3,

                "h2_unused_kg":
                    h2_unused,
                "h2_demand_kg":
                    demand,

                "unmet_h2_kg":
                    unmet_h2,
                "h2_unused_kg":
                    max(
                        0.0,
                        h2_produced
                        - h2_direct
                        - (
                                nh3_produced
                                * (
                                        3 * self.p.h2_molar_mass
                                        / (2 * self.p.nh3_molar_mass)
                                )
                                / self.p.ammonia_synthesis_efficiency
                        )
                    ),
                "nh3_produced_kg":
                    nh3_produced,

                "nh3_stored_kg":
                    nh3_stored,

                "nh3_discharged_kg":
                    nh3_discharged,

                "nh3_storage_level_kg":
                    storage_level,

                "nh3_storage_soc_percent":
                    storage_soc,

                "nh3_synthesis_energy_kwh":
                    synthesis_energy,

                "nh3_cracking_energy_kwh":
                    cracking_energy,

                "curtailed_energy_kwh":
                    curtailed_energy,

                "total_h2_supplied_kg":
                    total_h2_supplied,
            })

        return results