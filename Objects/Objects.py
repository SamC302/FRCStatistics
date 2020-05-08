import json
import numpy as np
import requests
import pandas as pd
from pathlib import Path
from pandas import json_normalize
from scipy.sparse.linalg import lsmr
from tqdm import tqdm
import os
import sqlalchemy
from sqlalchemy import orm

from Objects.SparseMatrixConstructor import SparseMatrix


class DataProcessor(object):
    def __init__(self, authKey, year, events=None, data=None, teamList=None):
        self.headers = {
            'accept': 'application/json',
            'X-TBA-Auth-Key': authKey,
        }
        self.year = year
        self.authKey = authKey
        if events is None:
            Events_response = requests.get(
                'https://www.thebluealliance.com/api/v3/events/{self.year}/keys'.format(self=self),
                headers=self.headers)
            self.events = Events_response.json()
        else:
            self.events = events
        self.directory = Path(__file__).parent.parent

        self.cols = {

        }

        pathtoDB = "sqlite:///" + (str(self.directory) + "\\MatchData/{self.year}.db".format(self=self)).replace("\\",
                                                                                                                 "\\\\").replace(
            "/", '\\\\')
        self.engine = sqlalchemy.create_engine(pathtoDB)
        self.conn = self.engine.connect()

        try:
            storedteamList = pd.read_sql_table("Teams", self.conn)['0']
        except:
            storedteamList = []
        if teamList is not None:
            self.teamList = teamList
        elif len(storedteamList):
            self.readTeamListfromtxt(year)
        else:
            self.collectMatchesTBA()

        self.numberOfTeams = len(self.teamList)
        self.numberOfValidMatches = pd.read_sql_table("Info",self.conn)['0'][0]
        self.currentXPR = None

    def collectMatchesTBA(self):
        totalMatches = 0
        validMatches = 0
        team_list = []

        for i in tqdm(range(len(self.events))):
            eventMatches = requests.get(
                'https://www.thebluealliance.com/api/v3/event/' + self.events[i] + '/matches', headers=self.headers
            ).json()
            totalMatches += len(eventMatches)
            if len(eventMatches) > 0:
                eventJSON = [self.flatten_json(match) for match in eventMatches]
                pdMatchList = pd.read_json(json.dumps(eventJSON))
                badColumns = pdMatchList.isna().any()
                for index, item in badColumns.iteritems():
                    if item:
                        pdMatchList = pdMatchList.drop(index, 1)
                pdMatchList = pdMatchList.set_index("key")
                try:
                    pdMatchList = pdMatchList.drop("videos_0_key", axis=1)
                    pdMatchList = pdMatchList.drop("videos_0_type", axis=1)
                except:
                    pass
                pdMatchList = pdMatchList.infer_objects()
                pdMatchList.to_sql(self.events[i], self.engine, if_exists="replace")
                try:
                    team_list.extend(pdMatchList.alliances_blue_team_keys_0.unique())
                except:
                    team_list.extend(pdMatchList.alliances_red_team_keys_0.unique())

                validMatches += len(pdMatchList)

        team_list = list(set(team_list))
        team_list.sort()
        self.teamList = pd.Series(team_list)
        self.teamList.to_sql("Teams", self.conn, if_exists="replace")
        self.numberOfValidMatches = validMatches
        self.numberOfTeams = len(team_list)
        info = {"Number of Matches": self.numberOfValidMatches, "Number of Teams": self.numberOfTeams}
        infoS = pd.Series(info)
        print(infoS)
        infoS.to_sql("Info", self.conn, if_exists="replace")

    def readTeamListfromtxt(self, year):
        teamList = []
        with open("Results/SortedTeamList" + str(year) + ".txt") as f:
            for line in f:
                teamList.append(line.strip())
        i = 0
        self.teamList = pd.Series(teamList)
        self.teamList.to_pickle("Results/SortedTeamList" + str(year) + ".pkl.xz")

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

    def XPR(self, x):
        sparseA = SparseMatrix((self.numberOfValidMatches * 2, len(self.teamList)), np.int32)
        sparseB = SparseMatrix((self.numberOfValidMatches * 2, 1), np.int32)
        allData = []
        for event in self.events:
            data = pd.read_sql_table(event, self.conn,
                                     columns=["alliances_blue_team_keys_0", "alliances_blue_team_keys_1",
                                              "alliances_blue_team_keys_2", "alliances_red_team_keys_0",
                                              "alliances_red_team_keys_1", "alliances_red_team_keys_2",
                                              "score_breakdown_blue_" + x, "score_breakdown_red_" + x])
            allData.append(data)
        xprData = pd.concat(allData)
        print(xprData)
        for index, row in tqdm(xprData.iterrows()):  # TODO: Replace with Splicing Columns
            u = 0
            match_blue_teams = [row["alliances_blue_team_keys_0"], row["alliances_blue_team_keys_1"],
                                row["alliances_blue_team_keys_2"]]
            match_red_teams = [row["alliances_red_team_keys_0"], row["alliances_red_team_keys_1"],
                               row["alliances_red_team_keys_2"]]
            sparseB.append(2 * u, 0, int(row["score_breakdown_blue_" + x]))
            sparseB.append(2 * u + 1, 0, int(row["score_breakdown_red_" + x]))
            for team in match_blue_teams:
                sparseA.append(2 * u, self.findTeam(team), 1)
            for team in match_red_teams:
                sparseA.append(2 * u + 1, self.findTeam(team), 1)
            u += 1

        A = sparseA.tocoo().tocsr()
        B = np.ndarray.flatten(sparseB.tocoo().tocsc().toarray())

        ans = lsmr(A, B)[0]
        self.currentXPR = pd.Series(ans)
        oprs = pd.concat(self.teamList, self.currentXPR)
        oprs.to_sql("Teams", self.conn)
        np.savetxt("Results/" + x + "PR.txt", ans)
