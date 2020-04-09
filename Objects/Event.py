import pandas as pd
import numpy as np


class Event(object):
    def __init__(self, code):
        self.code = code
        self.data = pd.read_pickle("MatchData/Events/data" + code + ".pkl.xz")
        self.teamList = self.constructTeamList()

    def constructTeamList(self):
        return None
