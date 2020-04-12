import httplib2
import requests
import numpy as np
import sklearn
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
from scipy.sparse.linalg import lsmr
from Objects.SparseMatrixConstructor import SparseMatrix
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import plot_confusion_matrix
from sklearn import metrics


class DataProcessor(object):
    def __init__(self, authKey, year, data=None, teamList=None):
        self.headers = {
            'accept': 'application/json',
            'X-TBA-Auth-Key': authKey,
        }
        self.year = year

        d = Path("MatchData/data" + str(year) + ".pkl.xz")
        if data is not None:
            self.data = data
        elif data is None and d.is_file():
            self.data = pd.read_pickle("MatchData/data" + str(year) + ".pkl.xz")
        else:
            self.data = pd.DataFrame()

        t = Path("Results/SortedTeamList" + str(year) + ".txt")
        if teamList is not None:
            self.teamList = teamList
        elif t.is_file():
            self.readTeamListfromtxt(year)
        else:
            self.teamList = pd.Series()

        self.numberOfMatches = None
        self.numberOfTeams = self.teamList.shape[0]
        self.numberOfFiles = None
        self.numberOfValidMatches = self.data.shape[0]
        self.percentageOfValidMatches = None
        self.currentXPR = None

    def collectMatchesDataFrame(self):
        totalMatches = 0
        validMatches = 0
        team_list = []
        Events_response = requests.get('https://www.thebluealliance.com/api/v3/events/' + str(self.year) + '/keys',
                                       headers=self.headers)
        Events_json = Events_response.json()
        for i in range(len(Events_json)):
            print(i / len(Events_json))
            eventMatches = requests.get(
                'https://www.thebluealliance.com/api/v3/event/' + Events_json[i] + '/matches', headers=self.headers
            ).json()
            totalMatches += len(eventMatches)
            if len(eventMatches) > 0:
                for event_match in eventMatches:
                    total_match_list = {}
                    if not self.checkIfNone(event_match):
                        validMatches += 1
                        # match_list[event_match["key"]] = event_match
                        match = self.flatten_json(event_match)
                        total_match_list[match["key"]] = match
                        # match_list.to_pickle("MatchData/Matches/"+event_match["key"]+".pkl.xz", compression="infer")
                        for team in event_match["alliances"]["blue"]["team_keys"]:
                            team_list.append(team)
                        for team in event_match["alliances"]["red"]["team_keys"]:
                            team_list.append(team)
                        team_list = list(dict.fromkeys(team_list))
                print("Creating Dataframe")
                pdMatchList = pd.DataFrame.from_dict(total_match_list, orient='index')
                badColumns = pdMatchList.isna().any()
                for index, item in badColumns.iteritems():
                    if item:
                        pdMatchList = pdMatchList.drop(index, 1)
                pdMatchList.to_pickle("MatchData/Events/data" + eventMatches[0]["event_key"] + ".pkl.xz",
                                      compression="infer")
                # total_match_list.to_csv("MatchData/data.csv")
        team_list.sort()
        with open('Results/SortedTeamList' + str(self.year) + '.txt', 'w') as f:
            for item in team_list:
                f.write("%s\n" % item)
        self.data = pdMatchList
        self.numberOfMatches = totalMatches
        self.numberOfValidMatches = validMatches
        self.percentageOfValidMatches = round(validMatches / totalMatches, 2)
        self.teamList = pd.Series(team_list)
        self.numberOfTeams = len(team_list)

    def XPR(self, x):
        sparseA = SparseMatrix((self.numberOfValidMatches * 2, len(self.teamList)), np.int32)
        sparseB = SparseMatrix((self.numberOfValidMatches * 2, 1), np.int32)
        for index, row in self.data.iterrows():  # TODO: Replace with Splicing Columns
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
        print(self.currentXPR)
        np.savetxt("Results/" + x + "PR.txt", ans)

    def PCA(self, numberOfComponents, features):

        featuresA = [i[:15] + "_blue" + i[15:] for i in features]
        featuresB = [i[:15] + "_red" + i[15:] for i in features]
        x = self.data.loc[:, featuresA]
        x.columns = features
        b = self.data.loc[:, featuresB]
        b.columns = features
        x = x.sub(b, fill_value=0).values
        y = self.data.loc[:, ['alliances_blue_score']].values
        np.savetxt("Results/PCATest.txt", x)
        x = StandardScaler().fit_transform(x)
        y = StandardScaler().fit_transform(y)
        pca = PCA(n_components=numberOfComponents)
        principalComponents = pca.fit_transform(x)
        principalDf = pd.DataFrame(data=principalComponents
                                   ,
                                   columns=['principal component ' + str(i) for i in range(1, numberOfComponents + 1)])
        dif = self.data.loc[:, 'alliances_blue_score'].sub(self.data.loc[:, 'alliances_red_score']).reset_index(
            drop=True)
        finalDf = pd.concat([principalDf, dif], axis=1)
        finalDf.to_pickle("Results/PCAResult.pkl.xz")
        return finalDf, pca.explained_variance_ratio_

    def readTeamListfromtxt(self, year):
        teamList = []
        with open("Results/SortedTeamList" + str(year) + ".txt") as f:
            for line in f:
                teamList.append(line.strip())
        self.teamList = pd.Series(teamList)
        self.teamList.to_pickle("Results/SortedTeamList" + str(year) + ".pkl.xz")

    def findTeam(self, team):
        return list(self.teamList[self.teamList == team].index.values)[0]

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

    def publish(self):
        SCOPES = 'https://www.googleapis.com/auth/drive'

        # This points to the JSON key file for the service account
        # You should have downloaded the file when creating your service account
        # It should be in the same directory as this script
        KEY_FILE_NAME = '../Credentials/our-audio-273419-1865397ccbc2.json'
        print("Acquiring credentials...")
        credentials = ServiceAccountCredentials.from_json_keyfile_name(filename=KEY_FILE_NAME, scopes=SCOPES)

        # Has to check the credentials with the Google servers
        print("Authorizing...")
        http = credentials.authorize(httplib2.Http())

        # Build the service object for use with any API
        print("Acquiring service...")
        service = discovery.build(serviceName="drive", version="v3", credentials=credentials)

        print("Service acquired!")

    # Next two functions are standins until Team Data is finished
    def TreeClassifier(self):
        features = ["score_breakdown_cargoPoints", "score_breakdown_foulPoints",
                    "score_breakdown_habClimbPoints", "score_breakdown_hatchPanelPoints",
                    "score_breakdown_sandStormBonusPoints", "score_breakdown_autoPoints"]
        featuresA = [i[:15] + "_blue" + i[15:] for i in features]
        featuresB = [i[:15] + "_red" + i[15:] for i in features]
        x = self.data.loc[:, featuresA]
        x.columns = features
        b = self.data.loc[:, featuresB]
        b.columns = features
        x = x.sub(b, fill_value=0).values
        y = self.data.loc[:, "winning_alliance"]
        z = y.apply(lambda x: 0 if x == "red" else 1)
        X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(x, z, test_size=0.20)
        print(X_train.shape)
        classifier = DecisionTreeClassifier(criterion="gini", max_depth=50)
        classifier.fit(X_train, y_train)
        y_pred = classifier.predict(X_test)
        print(y_pred.shape)
        print(sklearn.metrics.confusion_matrix(y_test, y_pred))
        print(sklearn.metrics.classification_report(y_test, y_pred))

    def TreeRegressor(self):
        features = ["score_breakdown_cargoPoints", "score_breakdown_foulPoints",
                    "score_breakdown_habClimbPoints", "score_breakdown_hatchPanelPoints",
                    "score_breakdown_sandStormBonusPoints", "score_breakdown_autoPoints", "score_breakdown_totalPoints"]
        featuresA = [i[:15] + "_blue" + i[15:] for i in features]
        featuresB = [i[:15] + "_red" + i[15:] for i in features]
        x = self.data.loc[:, featuresA]
        x.columns = features
        b = self.data.loc[:, featuresB]
        b.columns = features
        o = pd.concat([x, b])
        print(o)
        z = o.drop("score_breakdown_totalPoints", axis=1)
        X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(o, z, test_size=0.20)
        print(X_train.shape)
        classifier = DecisionTreeClassifier(criterion="gini", max_depth=50)
        classifier.fit(X_train, y_train)
        y_pred = classifier.predict(X_test)
        print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, y_pred))
        print('Mean Squared Error:', metrics.mean_squared_error(y_test, y_pred))
        print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(y_test, y_pred)))
