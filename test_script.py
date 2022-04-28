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

# load appliances
with open('appliances_data.csv') as data,\
    open('appliance_busy') as busy,\
    open('applinace_name') as names,\
    open('appliance scaling') as scalings:
    for name in names.readline():
        load = [ int(x) for x in data.readline()[:-1].split(',') ]
        busy_time = int(busy.readline()[:-1])
        scaling = [ int(x) for x in scalings.readline()[:-1].split(',') ]

        if len(load) > 1:
            global_appliances[name] = CycleAppliance(name, data, scaling)
        else:
            global_appliances[name] = ContinuousAppliance(name, data, scaling)

# plotting
plt.title("Load graph")
plt.xlabel("t (minute)")
plt.ylabel("power usage (watts)")

allHouses = [ 0 for _ in range(1440) ]

for _ in range(20):
    test_model = HouseModel([18, 21], global_appliances.values())
    for _ in range(1440):
        test_model.step()

    household_result = [ sum([ test_model.humanAgents[i].power[x] for i in range(test_model.num_human_agents)]) for x in range(1440) ]
    x = np.arange(0, 1440)
    y = np.array(household_result)

    for j in range(1440):
        allHouses[j] += household_result[j]

    plt.plot(x, y)

x = np.arange(0, 1440)
y = np.array(allHouses)
plt.plot(x, y)

plt.show()