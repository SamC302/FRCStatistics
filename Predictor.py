from Objects.DataProcessor import DataProcessor
from Objects.DriveInterface import DriveInterface
from Objects.Team import Team

# authkey is C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c

with open("Results/SortedTeamList" + str(2019) + ".txt") as f:
    for line in f:
        line = line.strip()
        print(line)
        T = Team(line, 2019, "C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c")
        print(line)
