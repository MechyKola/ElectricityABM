# importing the library
import numpy as np
import matplotlib.pyplot as plt
from main import *

global_appliances = {
    "washing machine": CycleAppliance("washing machine", [(0, 5)], [(2000, 20), (100, 30), (500, 5), (100, 15), (500, 10)], [1]),
    "computer": ContinuousAppliance("computer", 200, [1]),
    "oven": ContinuousAppliance("oven", 2300, [1, 1.5, 1.8, 2, 2, 2, 2, 2]),
    "kettle": CycleAppliance("kettle", [(0, 1)], [(2000, 3)], [1, 1.5, 1.5]),
    "stove": ContinuousAppliance("stove", 1000, [1, 1.5, 2, 2.5, 3, 3])
}

test_model = HouseModel([21], global_appliances.values())
for _ in range(1440):
    test_model.step()

household_result = [ sum([ test_model.humanAgents[i].power[x] for i in range(test_model.num_human_agents)]) for x in range(1440) ]
x = np.arange(0, 1440)
y = np.array(household_result)
 
# plotting
plt.title("Line graph")
plt.xlabel("t (minute)")
plt.ylabel("power usage (watts)")
plt.plot(x, y, color ="green")
plt.show()