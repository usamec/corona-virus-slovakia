import json
import numpy as np

from typing import List, Tuple

from tools.simulation.virus import Virus
from tools.simulation.population import PopulationBase


class PopulationCentreBase:
    """
    Represents a population centre such as a city, town or a village
    """

    def __init__(self,
                 longitude: float,
                 latitude: float,
                 populations: List[PopulationBase],
                 virus: Virus,
                 name: str,
                 random_seed=42):
        self.longitude = longitude
        self.latitude = latitude

        self.name = name

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
        self.hospitalized = []

        self._day_i = 0

    def __len__(self):
        return self._size

    def infect(self, n_infected: int, random_seed=None):
        """
        Infects randomly selected individuals evenly spread among all populations

        :param n_infected:          Number of people to infect

        :param random_seed:         Random seed to be used
        """
        for population in self._populations:
            population.infect(
                len(population) / len(self) * n_infected,
                random_seed=random_seed
            )

    def get_health_states(self, n=None, random_seed=None) -> np.ndarray:
        """
        :param n:               subsample size (returns all members by default)

        :param random_seed:     random seed to be used for the random selection

        :returns:               health state of randomly selected individuals
                                evenly spread among all populations
        """
        health_states = []

        if n is None:
            for population in self._populations:
                health_states.append(
                    population.get_health_states(random_seed=random_seed)
                )

        else:
            for population in self._populations:
                health_states.append(
                    population.get_health_states(
                        int(n * len(population) / len(self)),
                        random_seed=random_seed
                    )
                )

        return np.concatenate(health_states)

    def get_travelling(self, n=None, random_seed=None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns health states and interaction multiplicities for selected individuals

        :param n:               subsample size (returns all members by default)

        :param random_seed:     random seed to be used for the random selection

        :returns:               health_states, interaction_multiplicities
        """
        health_states = []
        interaction_multiplicities = []

        if n is None:
            for population in self._populations:
                health_states.append(
                    population.get_health_states(random_seed=random_seed)
                )

                if random_seed is None:
                    interaction_multiplicities.append(
                        population.get_periodic_interaction_multiplicities(
                            random_seed=random_seed
                        )
                    )

                else:
                    interaction_multiplicities.append(
                        population.get_stochastic_interaction_multiplicities()
                    )

        else:
            for population in self._populations:
                health_states.append(
                    population.get_health_states(
                        int(n * len(population) / len(self)),
                        random_seed=random_seed
                    )
                )

                if random_seed is None:
                    interaction_multiplicities.append(
                        population.get_periodic_interaction_multiplicities(
                            int(n * len(population) / len(self)),
                            random_seed=random_seed
                        )
                    )

                else:
                    interaction_multiplicities.append(
                        population.get_stochastic_interaction_multiplicities(
                            int(n * len(population) / len(self))
                        )
                    )

        return np.concatenate(health_states), np.concatenate(interaction_multiplicities)

    def _interact_stochastic(self):
        """
        Simulate random interactions among people
        living in the given population centre

        TODO: implement transmission matrix among different populations
        """
        n_infected = 0

        for population in self._populations:
            health_states = population.get_health_states()
            interaction_multiplicities = population.get_stochastic_interaction_multiplicities()

            for interaction_i in range(interaction_multiplicities.max()):
                transmission_mask = (interaction_multiplicities > interaction_i) * (
                        np.random.random(len(interaction_multiplicities)) < self._virus.transmission_probability
                )

                n_infected += health_states[transmission_mask].astype(int).sum()

        self.infect(n_infected)

    def _interact_periodic(self):
        """
        Simulate periodic interactions among people
        living in the given population centre (e.g households)
        """
        n_infected = 0

        for population in self._populations:
            health_states = population.get_health_states(random_seed=self._random_seed)
            interaction_multiplicities = population.get_periodic_interaction_multiplicities()

            for interaction_i in range(interaction_multiplicities.max()):
                transmission_mask = (interaction_multiplicities > interaction_i) * (
                        np.random.random(len(interaction_multiplicities)) < self._virus.transmission_probability
                )

                n_infected += health_states[transmission_mask].astype(int).sum()

        self.infect(n_infected, random_seed=self._random_seed)

    def _log_data(self):
        n_unaffected = 0
        n_infected = 0
        n_immune = 0
        n_dead = 0
        n_new_cases = 0
        n_hospitalized = 0

        for population in self._populations:
            n_unaffected += population.get_n_unaffected()
            n_infected += population.get_n_infected()
            n_new_cases += population.get_n_new_cases()
            n_immune += population.get_n_immune()
            n_dead += population.get_n_dead()
            n_hospitalized += population.get_n_hospitalized()

        self.unaffected.append(n_unaffected)
        self.infected.append(n_infected)
        self.immune.append(n_immune)
        self.dead.append(n_dead)
        self.new_cases.append(n_new_cases)
        self.hospitalized.append(n_hospitalized)

        self.simulation_days.append(self._day_i)

    def _heal(self):
        """
        Heals individuals if they are infected
        """
        for population in self._populations:
            population.heal()

    def _kill(self):
        """
        Kills a portion of the infected individuals
        """
        for population in self._populations:
            population.kill()

    def next_day(self):
        """
        Next day of the simulation
        """
        self._interact_stochastic()
        self._interact_periodic()

        self._heal()
        self._kill()

        self._log_data()

        for population in self._populations:
            population.next_day()

        self._day_i += 1

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'size': len(self),
            'longitude': self.longitude,
            'latitude': self.latitude,
            'simulation_days': self.simulation_days,
            'unaffected': self.unaffected,
            'infected': self.infected,
            'immune': self.immune,
            'dead': self.dead,
            'new_cases': self.new_cases,
            'hospitalized': self.hospitalized
        }

    def to_json(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(
                self.to_dict(),
                f
            )
