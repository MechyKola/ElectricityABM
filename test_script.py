# importing the library
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
from main import *

global_appliances = {}

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

allHouses = [0] * 1440

households = input('Enter occupants, seperating households with a semicolon, e.g. \"21 22 23; 10, 12, 35, 36; 65 70\": ')
households = [ [ int(occupant) for occupant in house.split(' ') ] for house in households.split('; ') ]
iterations = int(input('Enter number of iterations that you want to run: '))

for _ in range(iterations):
    for house in households:
        test_model = HouseModel(house, global_appliances, 360, 1200, 60)
        for _ in range(1440):
            test_model.step()
        test_model.processLighting()
        test_model.processAppliances()

        household_result = [ sum([ test_model.humanAgents[i].power[x] for i in range(test_model.num_human_agents)]) for x in range(1440) ]

        for j in range(1440):
            allHouses[j] += test_model.extraPower[j] + household_result[j]


# plotting
dataY = np.array(allHouses)
dataX = np.arange(0, 1, 1/1440) + 1 # preventing errors where time values are < 1

fig, ax = plt.subplots()
timeformat = md.DateFormatter('%H:%M')
plt.Axes.format_xdata = timeformat
ax.xaxis_date()
ax.xaxis.set_major_formatter(timeformat)
plt.xlim(1,2)

plt.plot(dataX,dataY)
plt.title("Load graph")
plt.xlabel("Time [hh:mm]")
plt.ylabel("power usage (watts)")

plt.show()
