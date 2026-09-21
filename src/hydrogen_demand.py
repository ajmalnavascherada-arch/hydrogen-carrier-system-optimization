import numpy as np


def constant_hydrogen_demand(
    time_hours: np.ndarray,
    demand_kg_h: float,
) -> np.ndarray:

    return np.full(
        len(time_hours),
        demand_kg_h,
    )


def variable_hydrogen_demand(
    time_hours: np.ndarray,
    base_demand_kg_h: float,
) -> np.ndarray:

    demand = np.full(
        len(time_hours),
        base_demand_kg_h,
    )

    # Higher demand during daytime
    daytime = (
        (time_hours >= 8.0) &
        (time_hours <= 18.0)
    )

    demand[daytime] *= 1.25

    return demand