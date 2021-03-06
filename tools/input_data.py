import pickle
import logging

import numpy as np
import pandas as pd

from tools.config import Config
from tools.general import singleton


@singleton
class InputData:
    def __init__(self):
        self._config = Config()

        self._municipal_df = self._prepare_municipal_df()

        with open(self._config.get('migration_matrix'), 'rb') as f:
            self._migration_matrix = pickle.load(f)

        min_inhabitants = self._config.get('min_inhabitants')

        inhabitants = self._municipal_df.popul.values

        population_size_mask = inhabitants > min_inhabitants

        self._municipal_df = self._municipal_df.loc[population_size_mask]
        self._migration_matrix = self._migration_matrix[population_size_mask].T[population_size_mask].T

        logging.info(f'Municipal data preview:\n {self._municipal_df}')

        self.mean_travel_ratio = self._get_mean_travel_ratio()

    def _get_mean_travel_ratio(self) -> float:
        """
        :returns:       Ratio of mean number of daily travelling people
                        to the full population size
        """
        total_meetings = 0

        for i in range(len(self._migration_matrix)):
            for j in range(len(self._migration_matrix)):
                if i == j:
                    continue

                total_meetings += self._migration_matrix[i][j]

        return total_meetings / self._municipal_df.popul.sum()

    def get_population_sizes(self) -> np.ndarray:
        return self._municipal_df.popul.values

    def get_longitudes(self) -> np.ndarray:
        return self._municipal_df.long.values

    def get_latitudes(self) -> np.ndarray:
        return self._municipal_df.lat.values

    def get_city_names(self) -> list:
        return self._municipal_df.NM4.tolist()

    def get_infected(self) -> np.ndarray:
        return self._municipal_df.infected.values

    def get_migration(self, i: int, j: int) -> int:
        """
        :param i:       index of the first city
        :param j:       index of the second city

        :returns:       mean number of people who daily travel between city i and j
        """
        return int(self._migration_matrix[i][j])

    def get_migration_row(self, i) -> np.ndarray:
        return self._migration_matrix[i]

    def get_migration_by_names(self, city_name_a: str, city_name_b: str) -> int:
        city_names = self.get_city_names()

        i = city_names.index(city_name_a)
        j = city_names.index(city_name_b)

        return self.get_migration(i, j)

    def _prepare_municipal_df(self):
        population_df = pd.read_excel(
            self._config.get('populations_file')
        )

        town_location_df = pd.read_excel(
            self._config.get('town_locations_file')
        )

        return population_df.merge(
            town_location_df,
            left_on='munic',
            right_on='IDN4'
        )
