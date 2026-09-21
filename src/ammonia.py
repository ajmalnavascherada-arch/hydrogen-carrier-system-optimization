class AmmoniaProcess:
    """
    Simplified ammonia synthesis and cracking model.

    Stoichiometry:

        N2 + 3H2 -> 2NH3

        2NH3 -> N2 + 3H2
    """

    def __init__(
        self,
        h2_molar_mass,
        nh3_molar_mass,
        synthesis_efficiency=0.90,
        cracking_efficiency=0.85,
    ):
        self.h2_molar_mass = h2_molar_mass
        self.nh3_molar_mass = nh3_molar_mass

        self.synthesis_efficiency = synthesis_efficiency
        self.cracking_efficiency = cracking_efficiency

    def h2_to_nh3(self, hydrogen_kg):
        """
        Convert available H2 mass into NH3 mass.
        """

        if hydrogen_kg <= 0:
            return 0.0

        # 3 mol H2 -> 2 mol NH3
        theoretical_ratio = (
            2 * self.nh3_molar_mass
        ) / (
            3 * self.h2_molar_mass
        )

        return (
            hydrogen_kg
            * theoretical_ratio
            * self.synthesis_efficiency
        )

    def nh3_to_h2(self, ammonia_kg):
        """
        Convert NH3 mass into recoverable H2 mass.
        """

        if ammonia_kg <= 0:
            return 0.0

        # 2 mol NH3 -> 3 mol H2
        theoretical_ratio = (
            3 * self.h2_molar_mass
        ) / (
            2 * self.nh3_molar_mass
        )

        return (
            ammonia_kg
            * theoretical_ratio
            * self.cracking_efficiency
        )