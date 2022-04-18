from mesa import Agent, Model
from mesa.time import RandomActivation
import random


class Appliance:
    def __init__(self, name, continuous):
        self.name = name
        self.continuous = continuous
    
class ContinuousAppliance(Appliance):
    def __init__(self, name, load, scaling):
        super().__init__(name, True)
        self.load = load
        self.scaling = scaling

class CycleAppliance(Appliance):
    def __init__(self, name, useCycle, postUseCycle, scaling):
        super().__init__(name, False)
        self.useCycle = useCycle
        self.postUseCycle = postUseCycle
        self.useCycleLength = sum([ y for (x, y) in useCycle])
        self.postUseCycleLength = sum([ y for (x, y) in postUseCycle])
        self.scaling = scaling


global_appliances = {
    "washing machine": CycleAppliance("washing machine", [(0, 5)], [(2000, 20), (100, 30), (500, 5), (100, 15), (500, 10)], [1]),
    "computer": ContinuousAppliance("computer", 200, [1]),
    "oven": ContinuousAppliance("oven", 2300, [1, 1.5, 1.8, 2, 2, 2, 2, 2]),
    "kettle": CycleAppliance("kettle", [(0, 1)], [2000, 3], [1, 1.5, 1.5]),
    "stove": ContinuousAppliance("stove", 1000, [1, 1.5, 2, 2.5, 3, 3])
}
    

class ApplianceAgent(Agent):
    def __init__(self, unique_id, model, appliance):
        super().__init__(unique_id, model)
        self.appliance = appliance


class HumanAgent(Agent):
    def __init__(self, unique_id, model, applianceAgents, age):
        super().__init__(unique_id, model)
        self.appliances = applianceAgents
        self.age = age
        self.hunger = 0
        self.dishes = 0
        self.clothes = 0
        self.energy = 100

        self.busy_until = 0

    def schedule_activity(self):
        activity_length = random.randint(0, 10)
        self.busy_until = self.model.schedule.steps + activity_length
        print("Activity scheduled for " + str(activity_length) + " minutes")

    def step(self):
        # due for cooking

        # due for laundry


        if(self.busy_until <= self.model.schedule.steps):
            self.schedule_activity()
            print("Activity schedules for agent " + str(self.unique_id))


class HouseModel(Model):
    def __init__(self, humans, appliances):
        self.num_human_agents = len(humans)
        self.num_appliance_agents = len(appliances)
        self.schedule = RandomActivation(self)
        # Create agents
        applianceAgents = [ ApplianceAgent(i, self, appliance) for i, appliance in enumerate(appliances) ]
        humanAgents = [ HumanAgent(i, self, applianceAgents, age) for i, age in enumerate(humans) ]
        
        for i in range(self.num_human_agents):
            self.schedule.add(humanAgents[i])

    def step(self):
        self.schedule.step()

test_model = HouseModel([21], [ value for _, value in global_appliances ])
for _ in range(1440):
    test_model.step()

# request handler to process appliances and humans

# data collector and batch runner at some point here
