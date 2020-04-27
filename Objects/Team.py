import pandas as pd
import numpy as np
import requests
import statistics as stat
from pathlib import Path
import Objects.DataProcessor as DataProcessor


class Team(object):
    def __init__(self, number, year, authKey):
        self.authKey = authKey
        if number[:3] == "frc":
            self.code = number
        elif type(number) is int:
            self.code = "frc" + str(number)
        self.year = year
        self.headers = {
            'accept': 'application/json',
            'X-TBA-Auth-Key': authKey,
        }
        self.data = None
        self.validMatches = 0
        t = Path("MatchData/Teams/" + self.code + ".pkl.xz")
        if t.is_file():
            self.data = pd.read_pickle("MatchData/Teams/" + self.code + ".pkl.xz")
        else:
            self.collectTBAData()
        # self.primaryScoringMean, self.primaryScoringSTD, self.secondaryScoringMean, self.secondaryScoringSTD, self.autoScoringMean, self.autoScoringSTD, self.endgameScoringMean, self.endgameScoringSTD, self.foulScoringMean, self.foulScoringSTD = self.collectStats()

    def collectTBAData(self):
        yearData = DataProcessor.DataProcessor(self.authKey, self.year).data
        teamData = yearData.loc[(yearData["alliances_blue_team_keys_0"] == self.code) | (
                yearData["alliances_blue_team_keys_1"] == self.code) | (
                                        yearData["alliances_blue_team_keys_2"] == self.code) | (
                                        yearData["alliances_red_team_keys_0"] == self.code) | (
                                        yearData["alliances_red_team_keys_1"] == self.code) | (
                                        yearData["alliances_red_team_keys_2"] == self.code)]
        badColumns = teamData.isna().any()
        for index, item in badColumns.iteritems():
            if item:
                teamData = teamData.drop(index, 1)
        teamData.to_pickle("MatchData/Teams/" + self.code + ".pkl.xz")
        self.data = teamData

    def collectScoutingData(self):
        return None

    def totalScoreStats(self, stats):
        data = pd.Series()
        fullList = []
        for feature in ["alliances_blue_score", "alliances_red_score"]:
            data = data.append(self.data.loc[:, feature])
        for s in stats:
            expr = "np." + str(s) + "(data)"
            fullList.append(eval(expr))
        fullList.append(len(data))
        return fullList

    @staticmethod
    def flatten_json(y):
        out = {}

        def flatten(x, name=''):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + '_')
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + '_')
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(y)
        return out

    @staticmethod
    def checkIfNone(data):
        y = pd.Series(data)
        x = y.isna()
        z = x.any()
        return z
