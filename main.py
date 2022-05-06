from cgi import test
from email.mime import application
from mesa import Agent, Model
from mesa.time import RandomActivation
import random
import heapq


class Appliance:
    def __init__(self, name, busy_time, continuous):
        self.name = name
        self.continuous = continuous
        self.busy_until = 0
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
        self.lock = False

    def __eq__(self, other):
        return self == other

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return True
    
    def use(self, power, startMinute, duration = None):
        if self.lock == False:
            self.lock = True
            heapq.heappush(self.model.applianceUnlocks, (duration if duration else len(self.appliance.load), self))
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
                        i += 1
            return True
        else:
            return False


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
        self.work_start = 0
        self.work_end = 0

        self.busy_until = 0
        self.power = [50] * 1440 # ambient power usage, e.g. phone charging

    def cook(self, current_step):
        activity_length = food = 0
        if (self.meal_of_the_day == 1):
            # make breakfast using kettle
            self.appliances["kettle"].use(self.power, current_step)
            activity_length = 20
            food = 240
        elif (self.meal_of_the_day == 2):
            # lunch using hob
            self.appliances["hob"].use(self.power, current_step, 20)
            activity_length = 40
            food = 300
        elif (self.meal_of_the_day == 3):
            # dinner using oven and hob
            self.appliances["oven"].use(self.power, current_step)
            self.appliances["hob"].use(self.power, current_step + 5, 20)
            activity_length = 60
            food = 400 # 360 until the end of the day and then another 60 for the morning after ;)
        # switch to next meal
        self.meal_of_the_day += 1

        return activity_length, food


    def schedule_activity(self, current_step):
        activity_length = 1
        # initial sleep of 8 hours +- 15 min
        if(current_step == 0):
            activity_length = 480 - 15 + random.randint(0, 31)
        # pour meals that have been cooked and eat
        elif (self.cooking_finishing == current_step):
            for human in self.model.humanAgents:
                if human.work_start > current_step or human.work_end < current_step:
                    human.meal_left += self.meal_left
        # eat any meals prepared for them
        elif (self.meal_left > 0):
            activity_length = self.meal_left
            self.meal_left = 0
            self.model.dishes += 2 # add 2 minutes worth of dishes
        # cook if user food is too low
        elif (self.food < 0 or random.randint(0, 100) > self.food):
            activity_length, food = self.cook(current_step)
            for human in self.model.humanAgents:
                human.food += food
            self.cooking_finishing = current_step + activity_length
            self.meal_left = food // 10
        elif (self.work_start == 0 and self.age >= 6 and self.age < 66):
            work_time = 480 + random.randint(20, 80) # commute random):
            activity_length = work_time
            self.meal_of_the_day = 3 # lunch and potentially breakfast at school/work
            self.food += 300
            self.work_start = current_step
            self.work_end = current_step + work_time
        elif (self.laundry > self.laundry_capacity):
            if self.model.washing_machine_full:
                if "dryer" in self.appliances:
                    self.appliances["dryer"].use(self.power, current_step)
                    activity_length = self.appliances["dryer"].appliance.busy_time
                else:
                    # manual drying
                    activity_length = 20
                self.model.washing_machine_full = False
            else:
                activity_length = self.appliances["washing_machine"].appliance.busy_time
                self.appliances["washing_machine"].use(self.power, current_step)
                self.laundry -= self.laundry_capacity
                self.model.washing_machine_full = True
        elif (self.model.dishes > 5):
            if "dishwasher" in self.appliances and not self.appliances["dishwasher"].lock:
                self.appliances["dishwasher"].use(self.power, current_step)
            else:
                # manual dishes
                activity_length = self.model.dishes
            self.model.dishes = 0
        elif(self.model.washing_machine_full):
            if "dryer" in self.appliances and not self.appliances["dryer"].lock:
                self.appliances["dryer"].use(self.power, current_step)
                activity_length = self.appliances["dryer"].appliance.busy_time
            else:
                activity_length = 20
            self.model.washing_machine_full = False
        # tv after dinner
        elif ("TV" in self.appliances and self.meal_of_the_day == 4\
             and current_step < random.randint(1020, 1320)):
            activity_length = 1440 - current_step - random.randint(0, 120)
            self.model.applianceEvents.append((current_step, "TV", 1))
            self.model.applianceEvents.append((current_step + activity_length, "TV", -1))
        elif (random.randint(0, 12) < 8): # no lock as it is assumed each member has their own
            activity_length = random.randint(20, 30)
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
        self.appliances = appliances
        # Create agents
        applianceAgents = [ ApplianceAgent(i, self, appliance) for i, appliance in enumerate(appliances.values()) ]
        self.humanAgents = [ HumanAgent(i, self, applianceAgents, age) for i, age in enumerate(humans) ]

        self.lightingEvents = []
        self.applianceEvents = []
        self.applianceUnlocks = []
        self.extraPower = [0] * 1440
        self.dishes = 0
        self.washing_machine_full = random.randint(0, 20) < 3
        
        for i in range(self.num_human_agents):
            self.lightingEvents.append((sunset + random.randint(-30, 30), 1))
            self.schedule.add(self.humanAgents[i])

    def step(self):
        while self.applianceUnlocks and self.applianceUnlocks[0][0] <= self.schedule.steps:
            self.applianceUnlocks[0][1].lock = False
            heapq.heappop(self.applianceUnlocks)
        self.schedule.step()

    def processAppliances(self):
        self.applianceEvents.sort()

        users = {"TV": 0}

        for i in range(1440):
            while self.applianceEvents and self.applianceEvents[0][0] == i:
                appliance = self.applianceEvents[0]
                self.applianceEvents.pop(0)
                users[appliance[1]] += appliance[2]
            for key in users:
                if users[key] > 0:
                    self.extraPower[i] += self.appliances[key].scaling[users[key]] * self.appliances[key].load


    def processLighting(self):
        self.lightingEvents.sort()

        users = 0 # self.num_human_agents

        for i in range(1440):
            while self.lightingEvents and self.lightingEvents[0][0] == i:
                users += self.lightingEvents[0][1]
                self.lightingEvents.pop(0)
            self.extraPower[i] += max(0, users) * self.lightingMultiplier
