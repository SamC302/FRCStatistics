from FRCDataProcessor import FRCDataProcessor

# authkey is C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c
P = FRCDataProcessor("C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c", 2019)
x, c = P.PCA(5, ["score_breakdown_cargoPoints", "score_breakdown_foulPoints",
                 "score_breakdown_habClimbPoints", "score_breakdown_hatchPanelPoints",
                 "score_breakdown_sandStormBonusPoints"])
print(sum(c))
