import requests
import json
import numpy as np
from scipy.sparse.linalg import lsmr
from SparseMatrixConstructor import SparseMatrix
import math
import pandas as pd


class FRCDataProcessor(object):
    def __init__(self, authKey, year, data=None):
        self.headers = {
            'accept': 'application/json',
            'X-TBA-Auth-Key': authKey,
        }
        self.year = year
        self.numberOfMatches = None
        self.numberOfTeams = None
        self.numberOfFiles = None
        self.numberOfValidMatches = None
        self.percentageOfValidMatches = None
        self.teamList = None
        self.data = data

    def collectMatchesDataFrame(self):
        totalMatches = 0
        validMatches = 0
        fileCounter = 0
        total_match_list = pd.DataFrame()
        team_list = []
        Events_response = requests.get('https://www.thebluealliance.com/api/v3/events/' + self.year + '/keys',
                                       headers=self.headers)
        Events_json = Events_response.json()
        for i in range(len(Events_json)):
            print(i / len(Events_json))
            eventMatches = requests.get(
                'https://www.thebluealliance.com/api/v3/event/' + Events_json[i] + '/matches', headers=self.headers
            ).json()
            totalMatches += len(eventMatches)
            if len(eventMatches) > 0 and eventMatches[0]["score_breakdown"] is not None:
                fileCounter += 1
                validMatches += len(eventMatches)
                for event_match in eventMatches:
                    # match_list[event_match["key"]] = event_match
                    match_list =  pd.json_normalize(event_match)
                    total_match_list = total_match_list.append(match_list)
                    #match_list.to_pickle("MatchData/Matches/"+event_match["key"]+".pkl.xz", compression="infer")
                    for team in event_match["alliances"]["blue"]["team_keys"]:
                        team_list.append(team)
                    for team in event_match["alliances"]["red"]["team_keys"]:
                        team_list.append(team)
                    team_list = list(dict.fromkeys(team_list))
        total_match_list.to_pickle("MatchData/data2020.pkl.xz", compression="infer")
        #total_match_list.to_csv("MatchData/data.csv")
        team_list.sort()
        with open('Results/SortedTeamList' + self.year + '.txt', 'w') as f:
            for item in team_list:
                f.write("%s\n" % item)
        self.data = total_match_list
        self.numberOfMatches = totalMatches
        self.numberOfFiles = math.ceil(fileCounter / 2)
        print(self.numberOfFiles)
        self.numberOfValidMatches = validMatches
        self.percentageOfValidMatches = round(validMatches / totalMatches, 2)
        self.teamList = team_list
        self.numberOfTeams = len(team_list)

    def collectMatchesJSON(self):
        totalMatches = 0
        validMatches = 0
        fileCounter = 0
        match_list = {}
        team_list = []
        Events_response = requests.get('https://www.thebluealliance.com/api/v3/events/' + self.year + '/keys',
                                       headers=self.headers)
        Events_json = Events_response.json()
        for i in range(len(Events_json)):
            eventMatches = requests.get(
                'https://www.thebluealliance.com/api/v3/event/' + Events_json[i] + '/matches', headers=self.headers
            ).json()
            totalMatches += len(eventMatches)
            if len(eventMatches) > 0 and eventMatches[0]["score_breakdown"] is not None:
                fileCounter += 1
                validMatches += len(eventMatches)
                for event_match in eventMatches:
                    match_list[event_match["key"]] = event_match
                    for team in event_match["alliances"]["blue"]["team_keys"]:
                        team_list.append(team)
                    for team in event_match["alliances"]["red"]["team_keys"]:
                        team_list.append(team)
                    team_list = list(dict.fromkeys(team_list))
                if fileCounter % 2 == 0 or i == len(eventMatches):
                    with open('MatchData/MatchData' + self.year + '/' + str(round(fileCounter / 2, 1)) + '.json',
                              'w') as outfile:
                        json.dump(match_list, outfile, indent=4)
                        match_list = {}

        team_list.sort()
        with open('Results/SortedTeamList' + self.year + '.txt', 'w') as f:
            for item in team:
                f.write("%s\n" % item)

        self.numberOfMatches = totalMatches
        self.numberOfFiles = math.ceil(fileCounter / 2)
        print(self.numberOfFiles)
        self.numberOfValidMatches = validMatches
        self.percentageOfValidMatches = round(validMatches / totalMatches, 2)
        self.teamList = team_list
        self.numberOfTeams = len(team_list)

    def provideMatches(self, numberOfValidMatches, numberOfTeams, numberOfFiles, teamList):
        self.numberOfValidMatches = numberOfValidMatches
        self.numberOfTeams = numberOfTeams
        self.numberOfFiles = numberOfFiles
        self.teamList = teamList

    def XPR(self, x):
        sparseA = SparseMatrix((self.numberOfValidMatches * 2, len(self.teamList)), np.int32)
        sparseB = SparseMatrix((self.numberOfValidMatches * 2, 1), np.int32)
        for i in range(1, self.numberOfFiles):
            with open("MatchData/MatchData" + self.year + "/" + str(i) + ".0.json", newline='') as r:
                readfile = json.load(r)
                u = 0
                for match in readfile:
                    match_blue_teams = [*readfile[match]["alliances"]["blue"]["team_keys"]]
                    match_red_teams = [*readfile[match]["alliances"]["red"]['team_keys']]
                    sparseB.append(2 * u, 0, readfile[match]["score_breakdown"]["blue"][x])
                    sparseB.append(2 * u + 1, 0, readfile[match]["score_breakdown"]["red"][x])
                    for team in match_blue_teams:
                        sparseA.append(2 * u, self.teamList.index(team), 1)
                    for team in match_red_teams:
                        sparseA.append(2 * u + 1, self.teamList.index(team), 1)
                    u += 1

        A = sparseA.tocoo().tocsr()
        B = np.ndarray.flatten(sparseB.tocoo().tocsc().toarray())

        ans = lsmr(A, B)[0]
        np.savetxt("Results/" + x + "PR.txt", ans)

    def PCA(self, numberOfComponents):
        return None

    @staticmethod
    def readpkl():
        df = pd.read_pickle("MatchData/data.pkl.xz",compression="infer")
        print(df)
