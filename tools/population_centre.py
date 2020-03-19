import numpy as np

from typing import List

from tools.virus import Virus
from tools.population import PopulationBase


class PopulationCentreBase:
    """
    Represents a population centre such as a city, town or a village
    """

    def __init__(self,
                 longitude: float,
                 latitude: float,
                 populations: List[PopulationBase],
                 virus: Virus,
                 random_seed=42):
        self.longitude = longitude
        self.latitude = latitude

        self._virus = virus
        self._populations = populations

        self._random_seed = random_seed

        self._size = 0

        for population in populations:
            self._size += len(population)

        self.simulation_days = []

        self.infected = []
        self.unaffected = []
        self.immune = []
        self.dead = []
        self.new_cases = []

        self._day_i = 0

    def __len__(self):
        return self._size

    def infect(self, n_infected: int):
        for population in self._populations:
            population.infect(
                int(len(population) / len(self) * n_infected)
            )

    def get_health_states(self, n=None, random_seed=None) -> np.ndarray:
        health_states = []

        if n is None:
            for population in self._populations:
                health_states.append(
                    population.get_healt_states(random_seed=random_seed)
                )

        else:
            for population in self._populations:
                health_states.append(
                    population.get_healt_states(
                        int(n * len(population) / len(self)),
                        random_seed=random_seed
                    )
                )

        return np.concatenate(health_states)

    def _interact_stochastic(self):
        """
        Simulate random interactions among people
        living in the given population centre

        TODO: implement transmission matrix among different populations
        """
        n_infected = 0

        for population in self._populations:
            health_states = population.get_healt_states()
            interaction_multiplicities = population.get_stochastic_interaction_multiplicities()

            for interaction_i in range(interaction_multiplicities.max()):
                transmission_mask = (interaction_multiplicities > interaction_i) * \
                                    (np.random.random(len(health_states)) <= self._virus.get_transmission_probability())

                n_infected += health_states[transmission_mask].astype(int).sum()

        self.infect(n_infected)

    def _interact_periodic(self):
        """
        Simulate periodic interactions among people
        living in the given population centre
        """
        n_infected = 0

        for population in self._populations:
            health_states = population.get_healt_states()
            interaction_multiplicities = population.get_periodic_interaction_multiplicities()

            for interaction_i in range(interaction_multiplicities.max()):
                transmission_mask = (interaction_multiplicities > interaction_i) * \
                                    (np.random.random(len(health_states)) <= self._virus.get_transmission_probability())

                n_infected += health_states[transmission_mask].astype(int).sum()

        self.infect(n_infected)

    def _log_data(self):
        n_unaffected = 0
        n_infected = 0
        n_immune = 0
        n_dead = 0
        n_new_cases = 0

        for population in self._populations:
            n_unaffected += population.get_n_unaffected()
            n_infected += population.get_n_infected()
            n_new_cases += population.get_n_new_cases()
            n_immune += population.get_n_immune()
            n_dead += population.get_n_dead()

        self.unaffected.append(n_unaffected)
        self.infected.append(n_infected)
        self.immune.append(n_immune)
        self.dead.append(n_dead)
        self.new_cases.append(n_new_cases)

        self.simulation_days.append(self._day_i)

    def _heal(self):
        for population in self._populations:
            population.heal(
                self._virus.illness_days_mean,
                self._virus.illness_days_std
            )

    def _kill(self):
        for population in self._populations:
            population.kill(
                self._virus.get_mortality(),
                self._virus.illness_days_mean
            )

    def next_day(self):
        self._interact_stochastic()
        self._interact_periodic()

        self._heal()
        self._kill()

        self._log_data()

        for population in self._populations:
            population.next_day()

        self._day_i += 1