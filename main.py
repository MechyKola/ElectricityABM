from cgi import test
from mesa import Agent, Model
from mesa.time import RandomActivation
import random


class Appliance:
    def __init__(self, name, busy_time, continuous):
        self.name = name
        self.continuous = continuous
        self.busy = False
        self.busy_time = busy_time


class ContinuousAppliance(Appliance):
    def __init__(self, name, busy_time, load, scaling):
        super().__init__(name, busy_time, True)
        self.load = load[0]
        self.scaling = scaling
    

class CycleAppliance(Appliance):
    def __init__(self, name, busy_time, load, scaling):
        super().__init__(name, busy_time, False)
        self.load = load
        self.scaling = scaling


class ApplianceAgent(Agent):
    def __init__(self, unique_id, model, appliance):
        super().__init__(unique_id, model)
        self.appliance = appliance
    
    def use(self, power, startMinute, duration = None):
        if self.appliance.continuous:
            # continuous appliance
            for i in range(startMinute, min(1440, startMinute + duration)):
                power[i] += self.appliance.load
        else:
            # cycle appliance use
            i = startMinute
            for p in self.appliance.load:
                if(i < 1440):
                    power[i] += p


class HumanAgent(Agent):
    def __init__(self, unique_id, model, applianceAgents, age):
        super().__init__(unique_id, model)
        self.appliances = { a.appliance.name : a for a in applianceAgents }
        self.age = age
        self.food = 60 + 480
        self.meal_of_the_day = 1
        self.dishes = 0
        self.laundry_capacity = 1440 * 7 / 2
        self.laundry = random.randint(0, self.laundry_capacity)
        self.model = model
        self.meal_left = 0
        self.cooking_finishing = -1

        self.busy_until = 0
        self.power = [10] * 1440 # ambient power usage, e.g. phone charging

    def cook(self, current_step):
        activity_length = food = 0
        if (self.meal_of_the_day == 1):
            # make breakfast using kettle
            self.appliances["kettle"].use(self.power, current_step)
            activity_length = 20
            food = 240
        elif (self.meal_of_the_day == 2):
            # lunch using stove
            self.appliances["stove"].use(self.power, current_step, 20)
            activity_length = 40
            food = 300
        elif (self.meal_of_the_day == 3):
            # dinner using oven and stove
            self.appliances["oven"].use(self.power, current_step)
            self.appliances["stove"].use(self.power, current_step + 5, 20)
            activity_length = 60
            food = 400 # 360 until the end of the day and then another 60 for the morning after ;)
        # switch to next meal
        self.meal_of_the_day += 1

        return activity_length, food


    def schedule_activity(self, current_step):
        activity_length = 1 # resting - time filler
        # initial sleep of 8 hours +- 15 min
        if(current_step == 0):
            activity_length = 480 - 15 + random.randint(0, 31)
        # pour meals that have been cooked and eat
        elif (self.cooking_finishing == current_step):
            for human in self.model.humanAgents:
                human.meal_left += self.meal_left
        # eat any meals prepared for them
        elif (self.meal_left > 0):
            activity_length = self.meal_left
            self.meal_left = 0
        # cook if user food is too low
        elif (self.food < 0 or random.randint(0, 100) > self.food):
            activity_length, food = self.cook(current_step)
            for human in self.model.humanAgents:
                human.food += food
            self.cooking_finishing = current_step + activity_length
            self.meal_left = food // 10
        # then they will check their laundry
        elif (self.laundry > self.laundry_capacity):
            activity_length = self.appliances["washing_machine"].appliance.busy_time
            self.appliances["washing_machine"].use(self.power, current_step)
            self.laundry -= self.laundry_capacity
        # 20-30 minute interval using computer,
        # this is roughly 8 hours, so
        # 8/14 of the hours awake and not eating
        elif (random.randint(0, 12) < 8):
            activity_length = random.randint(20, 30)
            # computer use
            self.appliances["computer"].use(self.power, current_step, activity_length)

        self.busy_until = self.model.schedule.steps + activity_length

        # update state of human
        self.food -= activity_length
        self.laundry += activity_length

    def step(self):
        if(self.busy_until <= self.model.schedule.steps):
            self.schedule_activity(self.model.schedule.steps)


class HouseModel(Model):
    def __init__(self, humans, appliances, sunrise, sunset, lightingMultiplier):
        self.num_human_agents = len(humans)
        self.num_appliance_agents = len(appliances)
        self.schedule = RandomActivation(self)
        self.lightingMultiplier = lightingMultiplier
        # Create agents
        applianceAgents = [ ApplianceAgent(i, self, appliance) for i, appliance in enumerate(appliances) ]
        self.humanAgents = [ HumanAgent(i, self, applianceAgents, age) for i, age in enumerate(humans) ]

        self.lightingEvents = [(sunrise, - self.num_human_agents)]
        self.applianceEvents = []
        self.extraPower = [0] * 1440
        
        for i in range(self.num_human_agents):
            self.lightingEvents.append((sunset + random.randint(-30, 30), 1))
            self.schedule.add(self.humanAgents[i])

    def step(self):
        self.schedule.step()

    def processLighting(self):
        self.lightingEvents.sort()

        users = self.num_human_agents

        for i in range(1440):
            while self.lightingEvents and self.lightingEvents[0] == i:
                users += self.lightingEvents[1]
                self.lightingEvents = self.lightingEvents[1:]
            self.extraPower[i] += users * self.lightingMultiplier




# request handler to process appliances and humans

# data collector and batch runner at some point here
