import numpy as np


class Electrolyzer:
    """
    Simplified PEM electrolyzer model.

    Converts electrical power into hydrogen.
    """

    def __init__(
        self,
        nominal_power_kw: float,
        minimum_load: float,
        nominal_efficiency: float,
        h2_lhv_kwh_kg: float,
    ):

        self.nominal_power_kw = nominal_power_kw
        self.minimum_load = minimum_load
        self.nominal_efficiency = nominal_efficiency
        self.h2_lhv_kwh_kg = h2_lhv_kwh_kg

    def efficiency(self, power_kw: float) -> float:

        if power_kw <= 0:
            return 0.0

        load_fraction = power_kw / self.nominal_power_kw

        load_fraction = np.clip(
            load_fraction,
            0.0,
            1.0,
        )

        # Simple load-dependent efficiency model
        efficiency = (
            self.nominal_efficiency
            - 0.10 * (1.0 - load_fraction) ** 2
        )

        return float(
            np.clip(
                efficiency,
                0.50,
                self.nominal_efficiency,
            )
        )

    def operate(self, available_power_kw: float) -> dict:

        if available_power_kw < (
            self.minimum_load *
            self.nominal_power_kw
        ):
            power_kw = 0.0

        else:
            power_kw = min(
                available_power_kw,
                self.nominal_power_kw,
            )

        efficiency = self.efficiency(power_kw)

        hydrogen_kg_h = (
            power_kw *
            efficiency /
            self.h2_lhv_kwh_kg
        )

        return {
            "power_kw": power_kw,
            "efficiency": efficiency,
            "hydrogen_kg_h": hydrogen_kg_h,
        }