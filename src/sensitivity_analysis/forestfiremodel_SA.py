"""
Created on Wed Jan  8 15:30:03 2020

This code was implemented by
Louis Weyland & Robin van den Berg, Philippe Nicolau, Hildebert Mouilé & Wiebe Jelsma

"""

import random
import math
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from src.datacollector_v2 import DataCollector
from src.environment.river import RiverCell
from src.environment.vegetation import TreeCell
from src.agents.firetruck import Firetruck
from src.environment.rain import Rain

# defines the model


class ForestFire(Model):
    '''
    Simple Forest Fire model.
    '''

    height = 100
    width = 100
    density = 0.6
    temperature = 0
    truck_strategy = 'Goes to the closest fire'
    river_number = 0
    river_width = 0
    random_fires = 0
    num_firetruck = 30
    truck_max_speed = 2
    vision = 100
    wind_strength = 10
    wind_dir = "\u2B06 North"

    def __init__(
            self,
            height=100,
            width=100,
            density=0.6,
            temperature=0,
            truck_strategy='Goes to the closest fire',
            river_number=0,
            river_width=0,
            random_fires=0,
            num_firetruck=30,
            vision=100,
            truck_max_speed=2,
            wind_strength=10,
            wind_dir="\u2B07 North"):
        super().__init__()
        '''
        Create a new forest fire model.

        Args:
            height, width: The size of the grid to model
            density: What fraction of grid cells have a tree in them.
        '''
        # Initialize model parameters
        self.height = height
        self.width = width
        self.density = density

        self.river_length = width
        # Will suck when set to higher than 2
        self.river_width = river_width

        self.temperature = temperature

        self.n_agents = 0
        self.agents = []
        self.initial_tree = height * width * density - \
            self.river_length * self.river_width

        self.river_size = width

        # Set up model objects
        self.schedule_TreeCell = RandomActivation(self)
        self.schedule_FireTruck = RandomActivation(self)
        self.schedule = RandomActivation(self)
        self.current_step = 0

        # Set the wind
        self.wind = wind_strength
        self.wind_dir = wind_dir

        # Translate the wind_dir string into vector
        wind_vector = {"\u2B06  South": (0, 1), "\u2198 South/West": (1, 1), "\u27A1 West": (1, 0),
                       "\u2197 North/West": (1, -1), "\u2B07 North": (0, -1), "\u2196 North/East": (-1, -1),
                       "\u2B05 East": (-1, 0), "\u2199 South/East": (-1, 1)}
        self.wind_dir = wind_vector[self.wind_dir]

        self.grid = MultiGrid(height, width, torus=False)

        random.seed(1)
        self.init_river(self.river_size)
        self.init_rain()

        # agent_reporters={TreeCell: {"Life bar": "life_bar"}})

        random.seed(1)
        self.init_vegetation(TreeCell, self.initial_tree)

        for i in range(len(self.agents)):
            self.schedule_TreeCell.add(self.agents[i])
            self.schedule.add(self.agents[i])

        random.seed(1)
        self.init_firefighters(
            Firetruck,
            num_firetruck,
            truck_strategy,
            vision,
            truck_max_speed)

        self.random_fires = random_fires
        self.temperature = temperature
        self.num_firetruck = num_firetruck
        self.truck_strategy = truck_strategy

        # Initialise fire in the middle otherwise del
        self.agents[10].condition = "On Fire"
        self.grid.move_agent(
            self.agents[10], (int(width / 2), int(height / 2)))

        # initiate the datacollector
        self.dc = DataCollector(self,
                                model_reporters={
                                    "Fine": lambda m: self.count_type(m, "Fine"),
                                    "On Fire": lambda m: self.count_type(m, "On Fire"),
                                    "Burned Out": lambda m: self.count_type(m, "Burned Out"),
                                    "Extinguished": lambda m: self.count_extinguished_fires(m)
                                },

                                # tables={"Life bar": "life_bar", "Burning rate": "burning_rate"},

                                agent_reporters={TreeCell: {"Life bar": "life_bar", "Burning rate": "burning_rate"},
                                                 Firetruck: {"Condition": "condition"}})

        self.running = True
        self.dc.collect(self, [TreeCell, Firetruck])
        self.wind_strength = wind_strength

    def init_river(self, n):
        '''
        Creating a river
        '''
        if self.river_width == 0:
            pass
        else:
            # initiating the river offgrid
            x = -1
            y_init = random.randrange(self.height - 1)

            # increasing the length of the river
            for i in range(int(n)):
                x += 1
                y = y_init + random.randint(-1, 1)

                while y < 0 or y >= self.height:
                    y += random.randint(-1, 1)
                self.new_river(RiverCell, (x, y))

                y_init = y

                # increasing the width of the river
                for j in range(self.river_width - 1):
                    new_width = random.choice([-1, 1])
                    if y + new_width < 0 or y + new_width == self.height:
                        new_width = -new_width
                    y += new_width
                    while not self.grid.is_cell_empty((x, y)):
                        if y + new_width < 0 or y + new_width == self.height:
                            new_width = -new_width
                        y += new_width
                    self.new_river(RiverCell, (x, y))

    def init_vegetation(self, agent_type, n):
        '''
        Creating trees
        '''
        for i in range(int(n)):
            x = random.randrange(self.width)
            y = random.randrange(self.height)
            while not self.grid.is_cell_empty((x, y)):
                x = random.randrange(self.width)
                y = random.randrange(self.height)
            self.new_agent(agent_type, (x, y))

    def init_firefighters(self, agent_type, num_firetruck,
                          truck_strategy, vision, truck_max_speed):
        for i in range(num_firetruck):
            x = random.randrange(self.width)
            y = random.randrange(self.height)
            while self.grid.get_cell_list_contents((x, y)):
                if isinstance(self.grid.get_cell_list_contents(
                        (x, y))[0], RiverCell):
                    x = random.randrange(self.width)
                    y = random.randrange(self.height)
                else:
                    break

            firetruck = self.new_firetruck(
                Firetruck, (x, y), truck_strategy, vision, truck_max_speed)
            self.schedule_FireTruck.add(firetruck)
            self.schedule.add(firetruck)

    def init_rain(self):
        '''
        Creating rain
        '''
        x = random.randrange(self.width)
        y = random.randrange(self.height)
        self.new_agent(Rain, (x, y))
        neighbors = self.grid.get_neighbors((x, y), moore=True)
        for neighbor in neighbors:
            self.new_agent(Rain, neighbor.pos)

    def step(self):
        '''
        Advance the model by one step.
        '''

        self.schedule_TreeCell.step()
        self.schedule_FireTruck.step()

        self.dc.collect(self, [TreeCell, Firetruck])
        self.current_step += 1

        if self.random_fires:
            randtree = int(random.random() * len(self.agents))
            if self.agents[randtree].condition == "Fine":
                self.randomfire(self, randtree)

        # Halt if no more fire
        if self.count_type(self, "On Fire") == 0:
            self.running = False

    @staticmethod
    def randomfire(self, randtree):
        if (random.random() < (math.exp(self.temperature / 10) / 300.0)):
            self.agents[randtree].condition = "On Fire"

    @staticmethod
    def count_type(model, tree_condition):
        '''
        Helper method to count trees in a given condition in a given model.
        '''
        count = 0
        for tree in model.schedule_TreeCell.agents:

            if tree.condition == tree_condition:
                count += 1
        return count

    @staticmethod
    def count_extinguished_fires(model):
        '''
        Helper method to count extinguished fires in a given condition in a given model.
        '''

        count = 0
        for firetruck in model.schedule_FireTruck.agents:
            count += firetruck.extinguished

        return count

    def new_agent(self, agent_type, pos):
        '''
        Method that enables us to add agents of a given type.
        '''
        self.n_agents += 1

        # Create a new agent of the given type
        new_agent = agent_type(self, self.n_agents, pos)

        # Place the agent on the grid
        self.grid.place_agent(new_agent, pos)

        # And add the agent to the model so we can track it
        self.agents.append(new_agent)

        return new_agent

    def new_firetruck(self, agent_type, pos, truck_strategy,
                      vision, truck_max_speed):
        '''
        Method that enables us to add agents of a given type.
        '''
        self.n_agents += 1

        # Create a new agent of the given type
        new_agent = agent_type(
            self,
            self.n_agents,
            pos,
            truck_strategy,
            vision,
            truck_max_speed)

        # Place the agent on the grid
        self.grid.place_agent(new_agent, pos)

        # And add the agent to the model so we can track it
        self.agents.append(new_agent)

        return new_agent

    def new_river(self, agent_type, pos):

        # Create a new agent of the given type
        new_agent = agent_type(self, self.n_agents, pos)

        # Place the agent on the grid
        self.grid.place_agent(new_agent, pos)

        # And add the agent to the model so we can track it

        return new_agent

    def remove_agent(self, agent):
        '''
        Method that enables us to remove passed agents.
        '''
        self.n_agents -= 1

        # Remove agent from grid
        self.grid.remove_agent(agent)

        # Remove agent from model
        self.agents.remove(agent)
