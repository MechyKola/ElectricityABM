# importing the library
import numpy as np
import matplotlib.pyplot as plt
from main import *

global_appliances = {
    "kettle": CycleAppliance("kettle", 1, [3000, 3000, 3000], [1, 1.5, 1.5]),
    "stove": ContinuousAppliance("stove", 1, [1000], [1, 1.5, 2, 2.5, 3, 3])
}

# load appliances
with open('appliance_data.csv') as data,\
    open('appliance_busy.csv') as busy,\
    open('appliance_names.csv') as names,\
    open('appliance_scaling.csv') as scalings:
    for nameLine in names.readlines():
        name = nameLine[:-1]
        load = [ int(x) for x in data.readline()[:-1].split(',') ]
        busy_time = int(busy.readline()[:-1])
        scaling = [ float(x) for x in scalings.readline().split(',')[:-1] ]

        if len(load) > 1:
            global_appliances[name] = CycleAppliance(name, busy_time, load, scaling)
        else:
            global_appliances[name] = ContinuousAppliance(name, busy_time, load, scaling)

# plotting
plt.title("Load graph")
plt.xlabel("t (minute)")
plt.ylabel("power usage (watts)")

allHouses = [ 0 for _ in range(1440) ]

for _ in range(500):
    test_model = HouseModel([18, 21], global_appliances.values(), 360, 1200, 60)
    for _ in range(1440):
        test_model.step()
    test_model.processLighting()

    household_result = [ sum([ test_model.humanAgents[i].power[x] for i in range(test_model.num_human_agents)]) for x in range(1440) ]
    x = np.arange(0, 1440)
    y = np.array(household_result)

    for j in range(1440):
        allHouses[j] += household_result[j] + test_model.extraPower[j]

    plt.plot(x, y)

x = np.arange(0, 1440)
y = np.array(allHouses)
plt.plot(x, y)

plt.show()