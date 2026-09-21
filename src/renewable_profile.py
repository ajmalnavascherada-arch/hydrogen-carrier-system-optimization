import numpy as np


def solar_profile(
    time_hours: np.ndarray,
    peak_power_kw: float = 100.0,
) -> np.ndarray:
    """
    Generate a synthetic solar-like power profile.

    Solar generation occurs approximately between 06:00 and 18:00.
    """

    x = (time_hours - 6.0) / 12.0 * np.pi

    normalized_power = np.sin(x)

    normalized_power = np.clip(
        normalized_power,
        0.0,
        None,
    )

    # Slightly sharper solar profile
    normalized_power = normalized_power ** 1.7

    return peak_power_kw * normalized_power


def add_variability(
    power_kw: np.ndarray,
    seed: int = 42,
    variability: float = 0.05,
) -> np.ndarray:
    """
    Add small stochastic fluctuations to the renewable profile.
    """

    rng = np.random.default_rng(seed)

    noise = rng.normal(
        loc=0.0,
        scale=variability,
        size=len(power_kw),
    )

    variable_power = power_kw * (1.0 + noise)

    return np.clip(variable_power, 0.0, None)