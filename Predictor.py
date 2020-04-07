from DataProcessor import DataProcessor

# authkey is C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c
import torch
import torchviz

P = DataProcessor("C6StJN6kweYGKqhV5iQURbWX2vRudwcjJYwBobcxINlbAKurqR35lRQsHwc9eQ5c", 2019)
P.TreeRegressor()
