import pandas as pd
import numpy as np


class Team(object):
    def __init__(self, number, year):
        self.code = "frc" + str(number)
        self.year = year
