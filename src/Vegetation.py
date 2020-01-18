#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 15:30:03 2020

This code was implemented by
Louis Weyland & Robin van den Berg, Philippe Nicolau, Hildebert Mouilé & Wiebe Jelsma

"""
import random
from mesa import Agent
import math
import numpy as np
from numpy import linalg as LA


class TreeCell(Agent):

    '''
    A tree cell.

    Attributes:
        x, y: Grid coordinates
        condition: Can be "Fine", "On Fire", or "Burned Out"
        unique_id: (x,y) tuple.
        life_bar : looks at the life bar of the tree

    unique_id isn't strictly necessary here,
    but it's good practice to give one to each
    agent anyway.
    '''

    def __init__(self, model, unique_id, pos):
        '''
        Create a new tree.
        Args:
        pos: The tree's coordinates on the grid. Used as the unique_id
        '''
        super().__init__(unique_id, model)
        self.pos = pos
        self.unique_id = unique_id
        self.condition = "Fine"
        self.life_bar = 100       # give the tree a life bar
        self.burning_rate = 20   # need to change that as well

        self.veg_state = 0.4
        self.veg_density = 0.3

        #

    def step(self):
        '''
        If the tree is on fire, spread it to fine trees nearby.
        '''
        if self.condition == "On Fire":
            neighbors = self.model.grid.get_neighbors(self.pos, moore=True)
            for neighbor in neighbors:

                if isinstance(neighbor, TreeCell) and neighbor.condition == "Fine":

                    # probability of spreading
                    prob_sp= TreeCell.prob_of_spreading(self, neighbor, self.model.wind_dir, self.model.wind_strength)
                    if random.uniform(0,1) <  prob_sp:
                        neighbor.condition = "On Fire"

            # if on fire reduce life_bar
            if self.life_bar != 0:
                self.life_bar -= self.burning_rate
            else:
                self.condition = "Burned Out"

    def get_pos(self):
        return self.pos

    def prob_of_spreading(self, neighbour, wind_dir, wind_strength):

        p_h = 0.58
        p_veg = neighbour.veg_state
        p_den = neighbour.veg_density
        p_s = 1  # no elavation
        a = 0.078
        c1 = 0.045
        c2 = 0.131
        theta = 0  # in case wind_strength is zero

        # if winf actually exists
        if self.model.wind_strength != 0:
            neighbour_vec = [neighbour.pos[0] - self.pos[0], neighbour.pos[1] - self.pos[1]]
            wind_vec = [wind_dir[0], wind_dir[1]]

            # get the angle theat between wind in the spreading direction
            dot_product = np.dot(neighbour_vec, wind_vec)
            theta = math.acos((dot_product / (LA.norm(neighbour_vec) * LA.norm(wind_vec))))

        p_w = math.exp(c2 * wind_strength * (math.cos(theta) - 1))

        p_burn = p_h * (1 + p_veg) * (1 + p_den) * p_w * p_s

        print(p_burn)
        return p_burn
