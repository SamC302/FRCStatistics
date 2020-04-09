from Objects.DataProcessor import DataProcessor
from Objects.DriveInterface import DriveInterface

# authkey is C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c

D = DriveInterface("C:/Users/samch/PycharmProjects/FRCStatistics/MatchData/Events")
D.uploadFilesToFolder()
