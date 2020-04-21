import pandas as pd
import numpy as np
import requests
import statistics as stat
from pathlib import Path


class Team(object):
    def __init__(self, number, year, authKey):
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
        t = Path("MatchData/Teams/"+self.code+".pkl.xz")
        if t.is_file():
            self.data = pd.read_pickle("MatchData/Teams/"+self.code+".pkl.xz")
        else:
            self.collectTBAData()
        #self.primaryScoringMean, self.primaryScoringSTD, self.secondaryScoringMean, self.secondaryScoringSTD, self.autoScoringMean, self.autoScoringSTD, self.endgameScoringMean, self.endgameScoringSTD, self.foulScoringMean, self.foulScoringSTD = self.collectStats()

    def collectTBAData(self):
        matchesResponse = requests.get(
            'https://www.thebluealliance.com/api/v3/team/' + self.code + '/matches/' + str(self.year),
            headers=self.headers)
        matchesJson = matchesResponse.json()
        totalMatchesJSON = {}
        for match in matchesJson:
            if not self.checkIfNone(match):
                self.validMatches += 1
                totalMatchesJSON[match["key"]] = self.flatten_json(match)
        teamData = pd.DataFrame.from_dict(totalMatchesJSON, orient='index')
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
