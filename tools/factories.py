from typing import List

from tools.input_data import InputData
from tools.simulation.virus import Virus
from tools.simulation.population import PopulationBase
from tools.simulation.population_centre import PopulationCentreBase


def city_factory(virus: Virus) -> List[PopulationCentreBase]:
    """
    Prepares cities based on the given csv file.
    Expected csv structure:
        <city:str>,<population: int>, <longitude: float>, <latitude: float>, <infected: int>
        (column order does not matter)

    :param virus:               desired virus type

    :return:                    instances of PopulationCentreBase ready for a simulation
    """
    input_data = InputData()

    cities = []

    for name, population, long, lat, infected in zip(input_data.get_city_names(),
                                                     input_data.get_population_sizes(),
                                                     input_data.get_longitudes(),
                                                     input_data.get_latitudes(),
                                                     input_data.get_infected()):
        populations = [
            PopulationBase(int(population / 10), virus) for i in range(10)
        ]

        current_city = PopulationCentreBase(
            name=name,
            longitude=long,
            latitude=lat,
            populations=populations,
            virus=virus
        )

        if infected != 0:
            current_city.infect(infected)

        cities.append(current_city)

    return cities
