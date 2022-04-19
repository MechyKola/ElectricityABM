from cgi import test
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


class ApplianceAgent(Agent):
    def __init__(self, unique_id, model, appliance):
        super().__init__(unique_id, model)
        self.appliance = appliance

    def use(self, power, startMinute):
        # cycle appliance use
        i = startMinute
        for duration, load in self.appliance.useCycle:
            for _ in range(duration):
                power[i] += load
                i += 1
        for duration, load in self.appliance.postUseCycle:
            for _ in range(duration):
                power[i] += load
                i += 1
        
    
    def use(self, power, startMinute, duration):
        # continuous appliance
        for i in range(startMinute, startMinute + duration):
            power[i] += self.appliance.load

class HumanAgent(Agent):
    def __init__(self, unique_id, model, applianceAgents, age):
        super().__init__(unique_id, model)
        self.appliances = applianceAgents
        self.age = age
        self.food = 60
        self.meal_of_the_day = 1
        self.dishes = 0
        self.laundry_capacity = 1440 * 7 / 2
        self.laundry = random.randint(0, self.laundry_capacity)
        # self.energy = 100

        self.busy_until = 0
        self.power = [0] * 1440

    def schedule_activity(self):
        activity_length = 1 # resting - time filler

        # first and foremost, the user will worry about how hungry they are
        if (self.food < 0):
            # make something
            if (self.meal_of_the_day == 1):
                # make breakfast using kettle

                activity_length = 20
                self.food += 240
            elif (self.meal_of_the_day == 2):
                # lunch using stove
                activity_length = 40
                self.food += 300
            else:
                # dinner using oven and stove
                activity_length = 60
                self.food += 400 # 360 until the end of the day and then another 60 for the morning after ;)
        
        # then they will check their laundry
        if (self.laundry > self.laundry_capacity):
            activity_length = 5
        
        # 20-30 minute interval using computer,
        # this is roughly 8 hours, so
        # 8/14 of the hours awake and not eating
        if (random.randint(0, 12) < 8):
            activity_length = random.randint(20, 30)
            # computer use

        self.busy_until = self.model.schedule.steps + activity_length
        print("Activity scheduled for " + str(activity_length) + " minutes")

    def step(self):
        if(self.busy_until <= self.model.schedule.steps):
            self.schedule_activity()


class HouseModel(Model):
    def __init__(self, humans, appliances):
        self.num_human_agents = len(humans)
        self.num_appliance_agents = len(appliances)
        self.schedule = RandomActivation(self)
        # Create agents
        applianceAgents = [ ApplianceAgent(i, self, appliance) for i, appliance in enumerate(appliances) ]
        self.humanAgents = [ HumanAgent(i, self, applianceAgents, age) for i, age in enumerate(humans) ]
        
        for i in range(self.num_human_agents):
            self.schedule.add(self.humanAgents[i])

    def step(self):
        self.schedule.step()

# request handler to process appliances and humans

# data collector and batch runner at some point here
