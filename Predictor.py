from Objects.DataProcessor import DataProcessor
from Objects.DriveInterface import DriveInterface
from Objects.Team import Team

# authkey is C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c

P = DataProcessor("C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c", 2019)
print(P.tTestPredictor([4099, 4099, 4099], [4099, 4099, 4099]))
