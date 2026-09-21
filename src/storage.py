class AmmoniaStorage:

    def __init__(self, capacity_kg, initial_level_kg=0.0):
        self.capacity_kg = capacity_kg
        self.level_kg = initial_level_kg

    def charge(self, ammonia_kg):
        """
        Store NH3 and return the amount actually stored.
        """

        if ammonia_kg <= 0:
            return 0.0

        available_space = self.capacity_kg - self.level_kg

        stored = min(ammonia_kg, available_space)

        self.level_kg += stored

        return stored

    def discharge(self, ammonia_kg):
        """
        Remove NH3 from storage.
        """

        if ammonia_kg <= 0:
            return 0.0

        discharged = min(ammonia_kg, self.level_kg)

        self.level_kg -= discharged

        return discharged

    def state_of_charge(self):
        """
        NH3 storage state of charge [%].
        """

        if self.capacity_kg <= 0:
            return 0.0

        return 100.0 * self.level_kg / self.capacity_kg