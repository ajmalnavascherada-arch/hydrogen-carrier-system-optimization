import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT / "src")
)

from parameters import SystemParameters
from electrolyzer import Electrolyzer
from ammonia import AmmoniaProcess


def test_electrolyzer_zero_power():

    p = SystemParameters()

    electrolyzer = Electrolyzer(
        p.electrolyzer_nominal_power_kw,
        p.electrolyzer_min_load,
        p.electrolyzer_nominal_efficiency,
        p.h2_lhv_kwh_kg,
    )

    result = electrolyzer.operate(0)

    assert result["hydrogen_kg_h"] == 0.0


def test_electrolyzer_power_limit():

    p = SystemParameters()

    electrolyzer = Electrolyzer(
        p.electrolyzer_nominal_power_kw,
        p.electrolyzer_min_load,
        p.electrolyzer_nominal_efficiency,
        p.h2_lhv_kwh_kg,
    )

    result = electrolyzer.operate(150)

    assert (
        result["power_kw"]
        <=
        p.electrolyzer_nominal_power_kw
    )


def test_ammonia_conversion():

    ammonia = AmmoniaProcess(
        2.016,
        17.031,
        0.90,
        0.85,
    )

    nh3 = ammonia.h2_to_nh3(1.0)

    assert nh3 > 0


def test_positive_hydrogen_recovery():

    ammonia = AmmoniaProcess(
        2.016,
        17.031,
        0.90,
        0.85,
    )

    h2 = ammonia.nh3_to_h2(1.0)

    assert h2 > 0