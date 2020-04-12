from Objects.DataProcessor import DataProcessor
from Objects.DriveInterface import DriveInterface
from Objects.Team import Team

# authkey is C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c

T = Team(1885, 2019, "C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c")
T.collectTBAData()
T.consistency(["alliances_blue_score", "alliances_red_score"])
