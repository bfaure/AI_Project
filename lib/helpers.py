# Python 2.7
# This file is automatically copied as helpers.pyx when main.py is run
# and the user has an installation of Cython
from __future__ import print_function
import os
import sys

import time
import random

from math import sqrt

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import heapq

updating_ui = False # will be set by eight_neighbor_grid.update_ui
ui_update_time = 0.05 # will be set by eight_neighbor_grid.update_ui

diagonal_movement_multiplier = sqrt(2) # used as global variable to increase speed
#diagonal_movement_multiplier = 1.0 # used as global variable to increase speed

# class to hold details for a single cell
class cell(object):
	def __init__(self,x_coordinate=None,y_coordinate=None,index=None,in_highway=False):
		self.state = "free"
		self.index = index # index in the self.cells list
		self.x = x_coordinate # not using anymore
		self.y = y_coordinate # not using anymore
		self.cost = 0 # used for Priority Queue to remember cost
		self.parent = None # used in search algos to denote parent of cell
		self.render_coordinate = None # x0,y0,x1,y1 render pixel coordinates
		self.in_highway = in_highway # set to True if cell is in highway path
		self.neighbor_indices = None # list of indices of neighbors in self.cells list
		self.neighbors = None # references to neighbor cells

	def to_string(self):
		cell_str = ""
		cell_str += "("+str(self.x)+","+str(self.y)+"), "
		cell_str += self.state+", "
		cell_str += "cost: "+str(self.cost)
		return cell_str

# similar to eight_neigbor_grid but is only used if the user provides
# command line arguments and is just trying to utilize those functions
# that do not include the use of the main_window or any ui interface
class non_gui_eight_neighbor_grid:
	def __init__(self,num_columns=160,num_rows=120):
		self.num_columns = num_columns
		self.num_rows = num_rows
		self.init_cells()

	def init_cells(self,leave_empty=False):
		self.cells = []
		i = 0
		for y in range(self.num_rows):
			for x in range(self.num_columns):
				new_cell = cell(x,y,i)
				self.cells.append(new_cell)
				i+=1

		self.start_cell = (0,0) # default start cell
		self.end_cell = (self.num_columns-1,self.num_rows-1) # default end cell
		self.hard_to_traverse_regions = [] # empty by default
		self.highways = [] # empty by default
		self.solution_path = [] # the path eventually filled by one of the search algos
		self.shortest_path = []
		self.path_traces = [] # list of all paths tried (shown to user)
		if leave_empty: return

		start_time = time.time()
		self.init_partially_blocked_cells() # init the partially blocked
		self.init_highways() # initialize the 4 highways
		self.init_blocked_cells() # initialize the completely blocked cells
		self.init_start_end_cells() # initialize the start/end locations
		self.solution_path = [] # the path eventually filled by one of the search algos

	def clear_path(self):
		# called from main_window when user selects appropriate File menu item
		self.solution_path 	= []
		self.shortest_path 	= []
		self.path_traces 	= []

	def check_for_highway(self,x_coord,y_coord,temp_highway=None):
		# checks if the coordinates in question contain a highway, the temp_highway
		# input is used by the get_highway function when it is attempting to place
		# another highway down and has already placed part of it
		for highway in self.highways:
			for coord in highway:
				if coord[0]==x_coord and coord[1]==y_coord:
					return True
		if temp_highway!=None:
			for coord in temp_highway:
				if coord[0]==x_coord and coord[1]==y_coord:
						return True
		return False

	def check_for_boundary(self,x,y,conservative=True):
		# checks to see if the coordinates are along one of the grid boundaries,
		# it actually will return false unless the coordinates are just outside
		# the boundary because it is used by the get_highway function to create
		# a river and it ensures the river coordinates extend to at least outside
		# the grid to help with rendering
		if conservative:
			if x>=self.num_columns or x<0:
				return True
			if y>=self.num_rows or y<0:
				return True
			return False
		else:
			if x>=(self.num_columns-1) or x<=0:
				return True
			if y>=(self.num_rows-1) or y<=0:
				return True
			return False

	def check_for_highway_wrapper(self,x_coord,y_coord,temp_highway):
		# called by the get_highway function, will do regular check_for_highway
		# then do check_for_highway with excluding the temp_highway but with checking
		# all neighboring cells of the x_coord and y_coord. This is because we were
		# having a problem loading .grid files if they had segments of highway next
		# to eachother (<=1) cell away because the loading process would just think
		# that these cells were part of the same highway when, in reality, they were
		# just two highways next to eachother.
		if self.check_for_highway(x_coord,y_coord,temp_highway): return True
		temp_cell = cell(x_coord,y_coord)
		neighbors = get_neighbors(temp_cell,self.cells)
		for neighbor in neighbors:
			if self.check_for_highway(neighbor.x,neighbor.y): return True
		return False

	def get_highway(self,head,edge,total_attempts):
		# helper function for the init_highways function, returns True if it can
		# create a highway starting at head that does not intersect with any others
		# that have already been placed on the map. Either max_attempts tries are
		# used or less, if a highway can be placed the function will break out.

		highway_path = []
		highway_path.append(head)

		start_x = head[0] # starting x coordinate
		start_y = head[1] # starting y coordinate

		num_attempts = 0
		max_attempts = 10 # number of attempts to try before choosing a new head

		while num_attempts<max_attempts:

			# figure out which direction we are starting with
			# based on the edge we are starting from...
			if edge == "top": direction = "down"
			if edge == "right": direction = "left"
			if edge == "bottom": direction = "up"
			if edge == "left": direction = "right"

			x = start_x
			y = start_y
			highway_path = [] # list of tuples representing the path of the highway
			highway_path.append(head) # append the starting coordinate

			loop = True
			while loop:
				# go in the direction for 20 steps, if possible
				for i in range(20):
					cur_x = x # current x coordinate
					cur_y = y # current y coordinate

					# figure out which coordinate should be incremented
					# based on the direction we are traveling...
					if direction == "down":
						cur_y = cur_y+1
					if direction == "left":
						cur_x = cur_x-1
					if direction == "up":
						cur_y = cur_y-1
					if direction == "right":
						cur_x = cur_x+1

					# check if we hit a boundary, if so and the length of the
					# highway is over 100 then we can add it to self.highways and return
					if self.check_for_boundary(cur_x,cur_y)==True:
						new_coord = (x,y)
						highway_path.append(new_coord)
						if len(highway_path) >= 100:
							self.highways.append(highway_path) # append the finished highway and return
							return num_attempts
						else:
							loop = False # break from the
							break

					# check if we hit another highway, if not, add it to the current
					# highway, if so, break out (clearing the current highway) and start
					# over from the same head location.
					if self.check_for_highway_wrapper(cur_x,cur_y,highway_path)==False:
						x = cur_x
						y = cur_y
						new_coord = (x,y)
						highway_path.append(new_coord)
					else:
						loop = False # clear the current highway attempt and start over from the same head location
						break

				if loop: # continue the current highway and get a new random direction
					next_direction = random.randint(1,10) # random integer in [1,...,10]
					if next_direction <= 6: # 60% chance same direction
						# keep going same direction
						direction = direction
					elif next_direction in [7,8]: # 20% chance perpendicular direction
						# go perpendicular direction...
						if direction in ["up","down"]:
							direction = "left"
						elif direction in ["left","right"]:
							direction = "up"
					elif next_direction in [9,10]: # 20% chance perpendicular direction
						# go other perpendicular direction...
						if direction in ["up","down"]:
							direction = "right"
						elif direction in ["left","right"]:
							direction = "down"

			num_attempts+=1
		return num_attempts

	def init_highways(self):
		# see Sakai Asisgnment PDF for more explanation.
		self.highways = []
		# select 4 random highway start locations
		num_highways = 4
		total_attempts = 0
		while len(self.highways)<num_highways:
			# must start on an edge cell
			num_head_possibilities = 2*self.num_columns + 2*self.num_rows - 1 # number of possible starting cells
			start_cell = random.randint(0,num_head_possibilities)
			# interpreting as clockwise (i.e. 0 would be top left corner, 160 would be
			# top right corner, 280 would be bottom right corner, 340 would be bottom
			# left corner). Values between those vertices would lie along the corresponding edges
			if start_cell < self.num_columns: # top edge
				coord = (start_cell,0)
				edge = "top"
			elif start_cell >= self.num_columns and start_cell < self.num_columns+self.num_rows: # right edge
				coord = (self.num_columns-1,start_cell-self.num_columns)
				edge = "right"
			elif start_cell >= self.num_columns+self.num_rows and start_cell < (self.num_columns*2)+self.num_rows: # bottom edge
				coord = (start_cell-self.num_rows-self.num_columns ,self.num_rows-1)
				edge = "bottom"
			elif start_cell >= (self.num_columns*2)+self.num_rows and start_cell < (self.num_columns*2)+(self.num_rows*2): # left edge
				coord = (0,start_cell-(self.num_columns*2)-self.num_rows)
				edge = "left"
			else:
				return
			total_attempts+=self.get_highway(coord,edge,total_attempts) # try to place highway from that head
		
		# let cells know if they're in a highway
		for h in self.highways:
			for x,y in h:
				for cell in self.cells:
					if cell.x==x and cell.y==y:
						self.cells[self.cells.index(cell)].in_highway = True
						break

	def init_blocked_cells(self):
		# choose 20% of the remaining cells to mark as fully blocked, Sakai PDF
		num_blocked_cells = 3840
		cur_blocked_cells = 0
		while cur_blocked_cells<num_blocked_cells:
			x_coord = random.randint(0,self.num_columns-1)
			y_coord = random.randint(0,self.num_rows-1)
			if self.check_for_highway(x_coord,y_coord)==False:

				if self.start_cell[0]==x_coord and self.start_cell[1]==y_coord:
					continue # skip if already used as start cell
				if self.end_cell[0]==x_coord and self.end_cell[1]==y_coord:
					continue # skip if already used as end cell

				self.set_cell_state(x_coord,y_coord,"full",False)
				cur_blocked_cells+=1

	def get_start_or_end_cell(self):
		# helper function for the init_start_end_cells function, see the
		# sakai PDF for details on how the location is chosen
		x_offset = random.randint(0,20)
		y_offset = random.randint(0,20)

		y_ground = random.randint(0,1) # choose if the cell will be in top 20 or bottom 20
		x_ground = random.randint(0,1) # choose if the cell will be in left 20 or right 20

		if x_ground==0:
			x_coord = x_offset
		else:
			x_coord = self.num_columns - 1 - x_offset

		if y_ground==0:
			y_coord = y_offset
		else:
			y_coord = self.num_rows - 1 - y_offset

		coordinate = (x_coord,y_coord)
		return coordinate

	def init_start_end_cells(self):
		# initializes the locations of the start and end cells
		while True:
			# gereate random start and end cells according to the
			# rules in the Sakai PDF...
			temp_start = self.get_start_or_end_cell()
			temp_end = self.get_start_or_end_cell()

			# check if the generated cells are far enough apart
			if self.get_manhattan_distance(temp_start,temp_end) >= 100:
				if self.get_cell_state(temp_start[0],temp_start[1])=="full":
					continue # cant use if already a fully blocked cell
				if self.get_cell_state(temp_end[0],temp_end[1])=="full":
					continue # cant use if already a fully blocked cell

				self.start_cell = temp_start
				self.end_cell = temp_end
				return

	def init_partially_blocked_cells(self):
		# see Sakai Assignment PDF for explanation.
		# select 8 random regions:
		self.hard_to_traverse_regions = []
		num_regions = 8
		for _ in range(num_regions):
			random.seed()
			x_rand = random.randint(0,self.num_columns-1)
			y_rand = random.randint(0,self.num_rows-1)
			coord = (x_rand,y_rand)
			self.hard_to_traverse_regions.append(coord)

		# iterate over the 8 regions and make a random 50% of the
		# cells in the region be partially blocked. The size of a
		# region is the 31x31 cells centered at that point (15 away
		# in all directions from the center)
		for region_center in self.hard_to_traverse_regions:

			region_center_x = region_center[0]
			region_center_y = region_center[1]

			# top left corner coordinates...
			region_start_x = region_center_x - 15
			region_start_y = region_center_y - 15

			# iterate over every cell in range and select with 50%
			# probability to mark it as partially blocked
			for y in range(region_start_y,region_start_y+30):
				# check that the y coord is in the grid range
				if y>=0 and y<self.num_rows:
					for x in range(region_start_x,region_start_x+30):
						# check that the x coord is in the grid range
						if x>=0 and x<self.num_columns:
							if random.randint(0,1)==1:
								self.set_cell_state(x,y,"partial",add_adjustment=False)

	def clear(self):
		# clears the current grid
		self.init_cells(leave_empty=True)

	def random(self):
		# same as clear but creates a new random grid after clearing
		self.init_cells(leave_empty=False)

	def save(self,filename):
		# saves the current grid to filename location
		f = open(filename, 'w')

		f.write("s_start:("+str(self.start_cell[0])+","+str(self.start_cell[1])+")\n")
		f.write("s_goal:("+str(self.end_cell[0])+","+str(self.end_cell[1])+")\n")
		for hard_cell in self.hard_to_traverse_regions:
			f.write("hard:("+str(hard_cell[0])+","+str(hard_cell[1])+")\n")

		cell_chars = [] # 2D list
		# create 'grid' of cells, each cell represented by a character
		for row in range(self.num_rows):
			row_chars = []
			for column in range(self.num_columns):
				row_chars.append('0')
			row_chars.append('\n')
			cell_chars.append(row_chars)

		num_highway_coordinates = 0
		for cell in self.cells:
			if self.check_for_highway(cell.x,cell.y):
				num_highway_coordinates+=1

		for cell in self.cells:
			x = cell.x
			y = cell.y

			if cell.state == "full":
				continue

			if cell.state == "free":
				cell_chars[y][x] = '1' if self.check_for_highway(x,y)==False else 'a'
			if cell.state == "partial":
				cell_chars[y][x] = '2' if self.check_for_highway(x,y)==False else 'b'

		cell_chars_str = ""
		for row in cell_chars:
			for item in row:
				cell_chars_str += item
		f.write(cell_chars_str)

	def is_finished_highway(self,highway,conservative=True):
		# checks if both of the endpoints of the highway
		# are at the boundary of the grid. If conservative
		# is set to True then it will ensure the highway runs
		# until at least one outside the grid size
		if highway==None:
			return False
		start_cell = highway[0]
		end_cell = highway[len(highway)-1]

		if len(highway)<100:
			return False

		if self.check_for_boundary(start_cell[0],start_cell[1],conservative) and self.check_for_boundary(end_cell[0],end_cell[1],conservative):
			return True
		return False

	def reconstruct_highways(self,coordinate_list):
		# takes in an unordered list of coordinates and reconstructs the 4 highways,
		# called from the load function below
		broken = [] # list of highway segments
		last = None
		last_cut = 0
		# iterate over the list of highway coordinates and if any consecutive
		# coordinates are greater than a distance of 1 away then cut the the
		# coordinate_list and push the onto the broken list
		for item in coordinate_list:
			if last == None: # if this is the first item
				last = item
				continue
			dist = self.get_manhattan_distance(item,last)
			if dist>1: # if a coordinate for a different highway
				# push all of the highway segment we found before this iteration onto the broken list
				broken.append(coordinate_list[last_cut:coordinate_list.index(item)])
				# save this location as the start of a new highway segment
				last_cut = coordinate_list.index(item)
			last = item # use this as the previous location on the next iteration

		# now we have the broken list with partially reconstructed highway
		# segments but they are most likely not complete, iterate over the
		# stuff in the broken list and connect any highway endpoints that
		# are only a distance of 1 away from eachother
		iterations = 0
		max_allowed = 1000
		while True:
			iterations+=1
			if iterations>max_allowed:
				self.highways = broken # save the current reconstruction state for debuggging
				return False

			segment = broken[0] # start,end of highway segment (coordinate form)
			if segment == None:
				del broken[0]
				continue

			segment_start = segment[0] # coordinates of start
			segment_end = segment[len(segment)-1] # coordinates of end

			new_broken = []
			for other_item in broken[1:]:
				other_segment_start = other_item[0] # get coordinate of start of other segment
				other_segment_end = other_item[len(other_item)-1] # get coordinate of end of other segment

				segment_start = segment[0] # get coordinate of start of current segment
				segment_end = segment[len(segment)-1] # get coordinate of end of current segment

				if self.get_manhattan_distance(segment_start,other_segment_start)<=1:
					# reverse the current segment and attach the other_item segment to end
					segment.reverse()
					segment.extend(other_item)
				elif self.get_manhattan_distance(segment_start,other_segment_end)<=1:
					# add the current segment onto the end of the other_item segment
					# and set the current item to be equal to other_item segment
					segment.reverse()
					other_item.reverse()
					segment.extend(other_item)

				elif self.get_manhattan_distance(segment_end,other_segment_start)<=1:
					# add the other_item segment onto the end of the current segment
					segment.extend(other_item)
				elif self.get_manhattan_distance(segment_end,other_segment_end)<=1:
					# reverse the other_item segment and add it onto the end of this segment
					other_item.reverse()
					segment.extend(other_item)
				else:
					# not able to attach other_item to current highway segment
					new_broken.append(other_item)
			# add the current segment (now hopfully larger than before this iteration of
			# the while lop) onto the end of the new_broken list so it wont be used
			# as the current segment until all other segments have been used
			new_broken.append(segment)
			broken = new_broken

			# if we have reconstructed all highways
			if len(broken)==4:
				repaired_all = True
				self.highways = broken
				index = 0
				for h in self.highways:
					if self.is_finished_highway(h,conservative=False)==False:
						if self.repair_highway(index)==False:
							repaired_all = False
					index+=1 

				if repaired_all: return True 
				else: return False

	def get_closest_edge_and_distance(self,coordinates):
		# get the closest wall and the distance to it
		dist_to_top = coordinates[1]
		dist_to_bottom = self.num_rows-coordinates[1]
		dist_to_left = coordinates[0]
		dist_to_right = self.num_columns-coordinates[0]

		#print("Distance to... top:"+str(dist_to_top)+", bottom:"+str(dist_to_bottom)+", left:"+str(dist_to_left)+", right:"+str(dist_to_right))
		if dist_to_top<dist_to_bottom and dist_to_top<dist_to_right and dist_to_top<dist_to_left:
			return ["top",dist_to_top]

		if dist_to_bottom<dist_to_top and dist_to_bottom<dist_to_right and dist_to_bottom<dist_to_left:
			return ["bottom",dist_to_bottom]

		if dist_to_left<dist_to_bottom and dist_to_left<dist_to_right and dist_to_left<dist_to_top:
			return ["left",dist_to_left]

		if dist_to_right<dist_to_bottom and dist_to_right<dist_to_top and dist_to_right<dist_to_left:
			return ["right",dist_to_right]

		return ["None",-1]

	def repair_highway(self,index):
		# if a highway does not register as a legitimate highway using the is_highway_complete function
		# when it is loaded this function is called to try to fix it. added this because sometimes the
		# last cell or two of a highway is lost in the loading process for some reason. if the amount
		# needed to be added to the highway is greater than 5 then it will alert the user and will
		# refrain from fixing it
		broken_highway = self.highways[index]

		start_cell = broken_highway[0]
		end_cell = broken_highway[len(broken_highway)-1]
		if self.check_for_boundary(start_cell[0],start_cell[1],conservative=False)==False:
			# extending the start of the highway to the wall
			edge,distance = self.get_closest_edge_and_distance(start_cell)
			if distance>5:
				return False
			#print("Start cell ("+str(start_cell[0])+","+str(start_cell[1])+") detached from "+edge+" by ",str(distance))
			if edge == "None":
				return False
			if edge == "top":
				const = start_cell[0]
				y_start = start_cell[1]
				new_cells = []
				for i in range(distance):
					new_cells.append([const,i])
				new_cells.extend(self.highways[index])
				self.highways[index] = new_cells

			if edge == "bottom":
				const = start_cell[0]
				y_start = start_cell[1]
				new_cells = []
				for i in range(distance):
					new_cells.append([const,y_start+i])
				new_cells.extend(self.highways[index])
				self.highways[index] = new_cells

			if edge == "left":
				const = start_cell[1]
				new_cells = []
				for i in range(distance):
					new_cells.append([i,const])
				new_cells.extend(self.highways[index])
				self.highways[index] = new_cells

			if edge == "right":
				const = start_cell[1]
				x_start = start_cell[0]
				new_cells = []
				for i in range(distance):
					new_cells.append([x_start+i,const])
				new_cells.extend(self.highways[index])
				self.highways[index] = new_cells

		if self.check_for_boundary(end_cell[0],end_cell[1],conservative=False)==False:
			# extending the end of the highway to the wall
			edge,distance = self.get_closest_edge_and_distance(end_cell)
			if distance>5:
				return False
			#print("End cell ("+str(end_cell[0])+","+str(end_cell[1])+") detached from "+edge+" by ",distance)
			if edge == "None":
				return False

			if edge == "top":
				const = end_cell[0]
				y_start = end_cell[1]
				new_cells = []
				for i in range(distance):
					self.highways[index].append([const,i])

			if edge == "bottom":
				const = end_cell[0]
				y_start = end_cell[1]
				new_cells = []
				for i in range(distance):
					self.highways[index].append([const,y_start+i])

			if edge == "left":
				const = end_cell[1]
				new_cells = []
				for i in range(distance):
					self.highways[index].append([i,const])

			if edge == "right":
				const = end_cell[1]
				x_start = end_cell[0]
				new_cells = []
				for i in range(distance):
					self.highways[index].append([x_start+i,const])

		#print("WARNING: Highway was repaired.")
		return True

	def load(self,filename):
		# loads in a new set of cells from a file, see the assignment pdf for
		# details on the file format
		f 			= open(filename,'r') # open the file
		lines 		= f.read().split('\n') # split file into lines
		new_cells 	= [] # to hold the new cells
		start_cell 	= None # string (x,y)
		end_cell 	= None # string (x,y)
		hard_to_traverse_regions = [] # to hold (x,y) locations of hard to traverse cells
		highways 	= [] # list of disparate highway coordinates

		y = 0
		i=0
		for line in lines: # iterate over each line of file

			# parse the start cell
			if line.find("s_start:")!=-1:
				start_cell = line.split(":")[1]

			# parse the end cell
			elif line.find("s_goal:")!=-1:
				end_cell = line.split(":")[1]

			# parse out the list of hard region center (8 total)
			elif line.find("hard:")!=-1:
				hard_to_traverse_regions.append(line.split(":")[1])

			# check if line has any data
			elif line in [""," "]:
				# just an empty line, skip it
				continue

			# parse out the grid data (1 line for 1 row of grid)
			else:
				x = 0
				# iterate over each column (1 char for 1 column)
				for char in line:

					cell_state = None
					in_highway = False
					if char == '0':
						cell_state = "full"
					elif char == '1':
						cell_state = "free"
					elif char == '2':
						cell_state = "partial"
					elif char == 'a':
						cell_state = "free"
						coord = (x,y)
						highways.append(coord)
						in_highway = True
					elif char == 'b':
						cell_state = "partial"
						coord = (x,y)
						highways.append(coord)
						in_highway = True
					else:
						cell_state = "free"

					new_cell = cell(x,y,i,in_highway)
					new_cell.state = cell_state
					new_cells.append(new_cell)
					i+=1
					x+=1
				y+=1

		self.cells 		= new_cells
		self.start_cell = eval(start_cell)
		self.end_cell 	= eval(end_cell)
		self.hard_to_traverse_regions 	= []
		for item in hard_to_traverse_regions:
			self.hard_to_traverse_regions.append(eval(item))
		# now need to flush the elements from the highways list and reorganize
		# it into individual lists that each represent an individual highway
		self.highways = [] # list of lists of coordinates
		if self.reconstruct_highways(highways): return True 
		else: return False

	def set_cell_state(self,x_coord,y_coord,state,add_adjustment=True):
		# updates a single cell in the grid with a new state then reloads the ui

		# if the coordinates are sent from the UI main_window instance they may
		# not align exactly with the cell coordinates in the grid so we need to adjust
		if add_adjustment:
			size = self.size()
			width = size.width()
			height = size.height()

			x_coord = x_coord - 1.0
			y_coord = y_coord - 1.0

			if x_coord<0: x_coord = 0
			if y_coord<0: y_coord = 0

			x = int(round(float((float(x_coord)/float(width))*float(self.num_columns))))
			y = int(round(float((float(y_coord)/float(height))*float(self.num_rows))))

		else:
			x = x_coord
			y = y_coord

		# if the change is to the start or end cell then we don't need to change any cells
		if state == "start":
			self.start_cell = (x,y)
			return
		if state == "end":
			self.end_cell = (x,y)
			return

		index = 0
		for cell in self.cells:
			#cur_x = index % self.num_columns
			#cur_y = int(index/self.num_columns)

			if x==cell.x and y==cell.y:
				#print("Changing cell to "+state)
				self.cells[index].state = state
				return

			index += 1

	def get_cell_state(self,x_coord,y_coord):
		# locates the cell in question and returns the state
		#index = 0
		for cell in self.cells:

			if x_coord==cell.x and y_coord==cell.y:
				return cell.state
	
	def get_manhattan_distance(self,cell1,cell2):
		# calculates manhattan distance
		x_run = abs(cell1[0]-cell2[0])
		y_run = abs(cell1[1]-cell2[1])
		return x_run+y_run

# UI element (widget) that represents the interface with the grid
class eight_neighbor_grid(QWidget):

	def __init__(self,num_columns=160,num_rows=120,pyqt_app=None):
		# constructor, pass the number of cols and rows
		super(eight_neighbor_grid,self).__init__()
		self.num_columns = num_columns # width of the board
		self.num_rows = num_rows # height of the board
		self.pyqt_app = pyqt_app # allows this class to call parent functions
		self.init_ui() # initialize a bunch of class instance variables

	def init_ui(self):
		# initialize ui elements
		self.mouse_location = None # the current location of the mouse over the widget
		self.mouse_color = [243,243,21] # purple for cell under cursor
		self.mouse_render_location = [0,0]

		self.horizontal_step = 1 # set later
		self.vertical_step = 1 # set later
		self.render_mouse = True
		self.allow_render_mouse = True # to allow for self.render_mouse override

		self.suppress_output = False # if true, suppress command line printing

		self.setMinimumSize(800,600) # ui pixel dimensions (w,h)
		self.grid_line_color = [0,0,0] # black for cell lines
		self.free_cell_color = [255,255,255] # white for free cell
		#self.free_cell_color = [1,166,17] # green for free cell
		self.trans_cell_color = [128,128,128] # gray cell for partially blocked
		self.blocked_cell_color = [0,0,0] # black cell for blocked
		self.end_cell_color = [255,0,0] # red cell for end location
		self.start_cell_color = [0,255,0] # green cell for start location
		self.highway_color = [0,0,255] # blue for highway lines
		self.solution_color = [0,255,0] # green for solution path
		self.solution_swarm_color = [0,255,255] # green for path that has been tested so far
		self.start_gradient = [255,0,0] # if gradient is used, the starting color
		self.end_gradient = [0,255,50] # if gradient is used, the ending color
		self.trace_color = [128,128,128] # if trace is on, the color of the prior solution paths
		self.trace_highlighting = False

		self.solution_swarm_render_density = 1.0 # width of the solution swarm lines (from ~0.1 to ~2.0 probably)
		if os.name == "nt": self.solution_swarm_render_density = 2.0 # better for windows
		self.highway_render_width = 2.0 # width of the highways shown in window (2.0 is default)
		self.solution_render_width = 5.0 # width of the solution path (5.0 is good default)
		self.trace_render_width = 1.0 # width of the solution trace

		self.draw_outer_boundary = False # if true, an outer boundary is drawn in bottom right
		self.draw_grid_lines = False # set to false by default
		self.show_solution_swarm = True # set to true by default
		self.show_path_trace = False # if true then show the prior tried paths
		self.using_gradient = True # if true then solution swarm will be gradient
		self.init_cells(leave_empty=True) # more instance variables that can be reset more easily from within instance

		self.solution_swarm_line_type = "DashLine" # can be one of "SolidLine","DashLine","DotLine",
		self.solution_line_type = "SolidLine" # "DashDotLine", or "DashDotDotLine"
		self.solution_trace_line_type = "DotLine"
		self.highway_line_type = "SolidLine"

	def init_cells(self,leave_empty=False):
		# creates the list of cells in the grid (all default to free), if leave_empty
		# is False then we will fill in the grid following the instructions in the
		# assignment pdf
		self.cells = []
		self.verbose = True # if true then the time to paint the grid will be printed to terminal
		i=0
		for y in range(self.num_rows):
			for x in range(self.num_columns):
				neighbor_indices = []
				if y==0 and x==0:
					neighbor_indices.append(i+1)
					neighbor_indices.append(i+self.num_columns)
					neighbor_indices.append(i+1+self.num_columns)
				elif y==self.num_rows-1 and x==self.num_columns-1:
					neighbor_indices.append(i-1)
					neighbor_indices.append(i-self.num_columns)
					neighbor_indices.append(i-1-self.num_columns)
				elif y==0 and x==self.num_columns-1:
					neighbor_indices.append(i-1)
					neighbor_indices.append(i+self.num_columns)
					neighbor_indices.append(i-1+self.num_columns)
				elif y==self.num_rows-1 and x==0:
					neighbor_indices.append(i+1)
					neighbor_indices.append(i-self.num_columns)
					neighbor_indices.append(i+1-self.num_columns)
				elif y==0:
					neighbor_indices.append(i-1)
					neighbor_indices.append(i+1)
					neighbor_indices.append(i-1+self.num_columns)
					neighbor_indices.append(i+self.num_columns)
					neighbor_indices.append(i+1+self.num_columns)
				elif y==self.num_rows-1:
					neighbor_indices.append(i-1)
					neighbor_indices.append(i+1)
					neighbor_indices.append(i-1-self.num_columns)
					neighbor_indices.append(i-self.num_columns)
					neighbor_indices.append(i+1-self.num_columns)
				elif x==0:
					neighbor_indices.append(i+1)
					neighbor_indices.append(i-self.num_columns)
					neighbor_indices.append(i+1-self.num_columns)
					neighbor_indices.append(i+self.num_columns)
					neighbor_indices.append(i+1+self.num_columns)
				elif x==self.num_columns-1:
					neighbor_indices.append(i-1)
					neighbor_indices.append(i-self.num_columns)
					neighbor_indices.append(i+self.num_columns)
					neighbor_indices.append(i-1-self.num_columns)
					neighbor_indices.append(i-1+self.num_columns)
				else:
					neighbor_indices.append(i+1)
					neighbor_indices.append(i-1)
					neighbor_indices.append(i-self.num_columns)
					neighbor_indices.append(i+self.num_columns)
					neighbor_indices.append(i-1-self.num_columns)
					neighbor_indices.append(i+1-self.num_columns)
					neighbor_indices.append(i-1+self.num_columns)
					neighbor_indices.append(i+1+self.num_columns)

				new_cell = cell(x,y,i)
				new_cell.neighbor_indices = neighbor_indices
				self.cells.append(new_cell)
				i+=1
		self.start_cell = (0,0) # default start cell
		self.end_cell = (self.num_columns-1,self.num_rows-1) # default end cell
		self.hard_to_traverse_regions = [] # empty by default
		self.highways = [] # empty by default
		self.solution_path = [] # the path eventually filled by one of the search algos
		self.shortest_path = []
		self.path_traces = [] # list of all paths tried (shown to user)
		self.current_path = None # path under cursor
		self.associate_cell_neighbors()
		if leave_empty: return

		if self.suppress_output==False: print("\nGenerating a random grid...")
		start_time = time.time()
		self.init_partially_blocked_cells() # init the partially blocked
		self.init_highways() # initialize the 4 highways
		self.init_blocked_cells() # initialize the completely blocked cells
		self.init_start_end_cells() # initialize the start/end locations
		self.solution_path = [] # the path eventually filled by one of the search algos

		if self.suppress_output==False: print("Finished generating random grid, "+str(time.time()-start_time)+" seconds\n")

	def associate_cell_neighbors(self):
		# go through the self.cells list and fill in neighbors
		print("Associating cell neighbors...",end="\r")
		for cell in self.cells:
			print("Associating cell neighbors... "+str(self.cells.index(cell)),end="\r")
			cell.neighbors = []
			if cell.neighbor_indices is not None:
				for i in cell.neighbor_indices:
					cell.neighbors.append(self.cells[i])
			else:
				allowed_x = [cell.x-1,cell.x,cell.x+1]
				allowed_y = [cell.y-1,cell.y,cell.y+1]
				prevent_index = cell.index

				for other_cell in self.cells:
					if other_cell.x in allowed_x and other_cell.y in allowed_y and other_cell.index!=prevent_index:
						cell_neighbors.append(other_cell)
				cell.neighbors = cell_neighbors
		print("\n")

	def mouseMoveEvent(self, event):

		self.verbose = False # dont print render information
		if self.render_mouse and self.allow_render_mouse:
			x = event.x()
			y = event.y()

			self.mouse_location = [x,y]
			self.repaint()

			current_cell_attributes = cell_information()
			current_cell_attributes.coordinates = self.base_coordinates(x,y,and_index=True)
			current_cell_attributes.index = current_cell_attributes.coordinates[2]
			current_cell_attributes.coordinates = current_cell_attributes.coordinates[:2]
			if current_cell_attributes.coordinates == [-1,-1] or current_cell_attributes.index==-1:
				current_cell_attributes.is_valid = False
				return

			self.mouse_render_location = current_cell_attributes.coordinates

			current_cell_attributes.is_valid = True
			current_cell_attributes.state = self.get_cell_state(current_cell_attributes.coordinates[0],current_cell_attributes.coordinates[1])
			current_cell_attributes.h = self.get_h_value(x,y)
			current_cell_attributes.g = self.get_g_value(x,y)
			current_cell_attributes.f = current_cell_attributes.h+current_cell_attributes.g

			if self.trace_highlighting:
				if len(self.solution_path)>0:
					head = None
					for item in self.solution_path:
						if item.x==current_cell_attributes.coordinates[0] and item.y==current_cell_attributes.coordinates[1]:
							head = item
							break

					if head!=None:
						self.current_path = rectify_path(head)
					else:
						self.current_path = None
			else:
				self.current_path = None

			self.emit(SIGNAL("return_current_cell_attributes(PyQt_PyObject)"),current_cell_attributes)
		else:
			self.setMouseTracking(False)

	def enterEvent(self,event):
		# called if the mouse cursor goes over the widget
		#print("Mouse entered widget")
		#self.verbose = False
		self.has_mouse = True
		if self.render_mouse:
			self.setMouseTracking(True)

	def leaveEvent(self,event):
		# called if the mouse cursor leaves the widget
		#print("Mouse left widget")
		#self.verbose = True
		self.has_mouse = False
		self.setMouseTracking(False)
		self.mouse_location = None

	def get_h_value(self,x,y):
		# gets the heuristic vlaue
		return 0

	def get_g_value(self,x,y):
		# gets the cost of the path from the start node to (x,y)
		return 0

	def base_coordinates(self,x_coord,y_coord,and_index=False):
		# takes in coordinates of pixel location and returns x and y of closest cell
		x = -1
		y = -1
		i = 0
		for cell in self.cells:
			if x_coord>=cell.render_coordinate[0] and x_coord<(cell.render_coordinate[0]+cell.render_coordinate[2]):
				if y_coord>=cell.render_coordinate[1] and y_coord<(cell.render_coordinate[1]+cell.render_coordinate[3]):
					return [cell.x,cell.y,cell.index] if and_index else [cell.x,cell.y]
			i+=1
		if x==-1 and y==-1:
			#print("ERROR: Could not locate cell in question ("+str(x)+","+str(y)+")")
			return [-1,-1,-1] if and_index else [-1,-1]

	def clear_path(self):
		# called from main_window when user selects appropriate File menu item
		self.solution_path 	= []
		self.shortest_path 	= []
		self.path_traces 	= []

	def check_for_highway(self,x_coord,y_coord,temp_highway=None):
		# checks if the coordinates in question contain a highway, the temp_highway
		# input is used by the get_highway function when it is attempting to place
		# another highway down and has already placed part of it
		for highway in self.highways:
			for coord in highway:
				if coord[0]==x_coord and coord[1]==y_coord:
					return True
		if temp_highway!=None:
			for coord in temp_highway:
				if coord[0]==x_coord and coord[1]==y_coord:
						return True
		return False

	def check_for_boundary(self,x,y,conservative=True):
		# checks to see if the coordinates are along one of the grid boundaries,
		# it actually will return false unless the coordinates are just outside
		# the boundary because it is used by the get_highway function to create
		# a river and it ensures the river coordinates extend to at least outside
		# the grid to help with rendering
		if conservative:
			if x>=self.num_columns or x<0:
				return True
			if y>=self.num_rows or y<0:
				return True
			return False
		else:
			if x>=(self.num_columns-1) or x<=0:
				return True
			if y>=(self.num_rows-1) or y<=0:
				return True
			return False

	def check_for_highway_wrapper(self,x_coord,y_coord,temp_highway):
		# called by the get_highway function, will do regular check_for_highway
		# then do check_for_highway with excluding the temp_highway but with checking
		# all neighboring cells of the x_coord and y_coord. This is because we were
		# having a problem loading .grid files if they had segments of highway next
		# to eachother (<=1) cell away because the loading process would just think
		# that these cells were part of the same highway when, in reality, they were
		# just two highways next to eachother.
		if self.check_for_highway(x_coord,y_coord,temp_highway): return True
		temp_cell = cell(x_coord,y_coord)
		neighbors = get_neighbors(temp_cell,self.cells)
		for neighbor in neighbors:
			if self.check_for_highway(neighbor.x,neighbor.y): return True
		return False

	def get_highway(self,head,edge,total_attempts):
		# helper function for the init_highways function, returns True if it can
		# create a highway starting at head that does not intersect with any others
		# that have already been placed on the map. Either max_attempts tries are
		# used or less, if a highway can be placed the function will break out.

		highway_path = []
		highway_path.append(head)

		start_x = head[0] # starting x coordinate
		start_y = head[1] # starting y coordinate

		num_attempts = 0
		max_attempts = 10 # number of attempts to try before choosing a new head

		while num_attempts<max_attempts:

			# figure out which direction we are starting with
			# based on the edge we are starting from...
			if edge == "top": direction = "down"
			if edge == "right": direction = "left"
			if edge == "bottom": direction = "up"
			if edge == "left": direction = "right"

			x = start_x
			y = start_y
			highway_path = [] # list of tuples representing the path of the highway
			highway_path.append(head) # append the starting coordinate

			loop = True
			while loop:
				# go in the direction for 20 steps, if possible
				for i in range(20):
					cur_x = x # current x coordinate
					cur_y = y # current y coordinate

					# figure out which coordinate should be incremented
					# based on the direction we are traveling...
					if direction == "down":
						cur_y = cur_y+1
					if direction == "left":
						cur_x = cur_x-1
					if direction == "up":
						cur_y = cur_y-1
					if direction == "right":
						cur_x = cur_x+1

					# check if we hit a boundary, if so and the length of the
					# highway is over 100 then we can add it to self.highways and return
					if self.check_for_boundary(cur_x,cur_y)==True:
						new_coord = (x,y)
						highway_path.append(new_coord)
						if len(highway_path) >= 100:
							self.highways.append(highway_path) # append the finished highway and return
							return num_attempts
						else:
							loop = False # break from the
							break

					# check if we hit another highway, if not, add it to the current
					# highway, if so, break out (clearing the current highway) and start
					# over from the same head location.
					if self.check_for_highway_wrapper(cur_x,cur_y,highway_path)==False:
						x = cur_x
						y = cur_y
						new_coord = (x,y)
						highway_path.append(new_coord)
					else:
						loop = False # clear the current highway attempt and start over from the same head location
						break

				if loop: # continue the current highway and get a new random direction
					next_direction = random.randint(1,10) # random integer in [1,...,10]
					if next_direction <= 6: # 60% chance same direction
						# keep going same direction
						direction = direction
					elif next_direction in [7,8]: # 20% chance perpendicular direction
						# go perpendicular direction...
						if direction in ["up","down"]:
							direction = "left"
						elif direction in ["left","right"]:
							direction = "up"
					elif next_direction in [9,10]: # 20% chance perpendicular direction
						# go other perpendicular direction...
						if direction in ["up","down"]:
							direction = "right"
						elif direction in ["left","right"]:
							direction = "down"

			num_attempts+=1

		#print("                                                                             ",end='\r')
		if self.suppress_output==False: print("Exhausted "+str(num_attempts)+" attempts, "+str(total_attempts)+" total.",end='\r')
		return num_attempts

	def init_highways(self):
		if self.suppress_output==False: print("Placing highways...")
		# see Sakai Asisgnment PDF for more explanation.
		self.highways = []
		# select 4 random highway start locations
		num_highways = 4
		total_attempts = 0
		while len(self.highways)<num_highways:
			# must start on an edge cell
			num_head_possibilities = 2*self.num_columns + 2*self.num_rows - 1 # number of possible starting cells
			start_cell = random.randint(0,num_head_possibilities)
			# interpreting as clockwise (i.e. 0 would be top left corner, 160 would be
			# top right corner, 280 would be bottom right corner, 340 would be bottom
			# left corner). Values between those vertices would lie along the corresponding edges
			if start_cell < self.num_columns: # top edge
				coord = (start_cell,0)
				edge = "top"
			elif start_cell >= self.num_columns and start_cell < self.num_columns+self.num_rows: # right edge
				coord = (self.num_columns-1,start_cell-self.num_columns)
				edge = "right"
			elif start_cell >= self.num_columns+self.num_rows and start_cell < (self.num_columns*2)+self.num_rows: # bottom edge
				coord = (start_cell-self.num_rows-self.num_columns ,self.num_rows-1)
				edge = "bottom"
			elif start_cell >= (self.num_columns*2)+self.num_rows and start_cell < (self.num_columns*2)+(self.num_rows*2): # left edge
				coord = (0,start_cell-(self.num_columns*2)-self.num_rows)
				edge = "left"
			else:
				print("ERROR in init_highways, could not locate edge for start_cell: "+str(start_cell))
				return
			total_attempts+=self.get_highway(coord,edge,total_attempts) # try to place highway from that head
		if self.suppress_output: print("\n",end='\r') # save the last entry output from the get_highway() function

		# let cells know if they're in a highway
		for h in self.highways:
			for x,y in h:
				for cell in self.cells:
					if cell.x==x and cell.y==y:
						self.cells[self.cells.index(cell)].in_highway = True
						break

	def init_blocked_cells(self):
		# choose 20% of the remaining cells to mark as fully blocked, Sakai PDF
		if self.suppress_output==False: print("Creating fully blocked cells...")
		num_blocked_cells = 3840
		cur_blocked_cells = 0
		while cur_blocked_cells<num_blocked_cells:
			x_coord = random.randint(0,self.num_columns-1)
			y_coord = random.randint(0,self.num_rows-1)
			if self.check_for_highway(x_coord,y_coord)==False:

				if self.start_cell[0]==x_coord and self.start_cell[1]==y_coord:
					continue # skip if already used as start cell
				if self.end_cell[0]==x_coord and self.end_cell[1]==y_coord:
					continue # skip if already used as end cell

				self.set_cell_state(x_coord,y_coord,"full",False)
				cur_blocked_cells+=1

	def euclidean_heuristic(self, start, end):
		#end referes to end cell
		#start refers to the node form which euclidean distance is being calculated
		x_run = -1
		y_run = -1

		if (type(start) is tuple) and (type(end) is tuple):
			x_run = abs(start[0] - end[0])
			y_run = abs(start[1] - end[1])
		elif (type(start) is cell) and (type(end) is tuple):
			x_run = abs(start.x - end[0])
			y_run = abs(start.y - end[1])
		elif (type(start) is cell) and (type(end) is cell):
			x_run = abs(start.x - end.x)
			y_run = abs(start.y - end.y)
		elif (type(start) is tuple) and (type(end) is cell):
			x_run = abs(start[0] - end.x)
			y_run = abs(start[1] - end.y)

		if x_run!=-1 and y_run!=-1:
			return sqrt((x_run**2)+(y_run**2))
		else:
			print("ERROR: Input types (start="+str(type(start))+"), (end="+str(type(end))+") to heuristic are unknown.")
			return 1

	def diagonal_distance_heuristic(self, start, end):
		x_run = -1
		y_run = -1

		if (type(start) is tuple) and (type(end) is tuple):
			x_run = abs(start[0] - end[0])
			y_run = abs(start[1] - end[1])

		elif (type(start) is cell) and (type(end) is tuple):
			x_run = abs(start.x - end[0])
			y_run = abs(start.y - end[1])

		elif (type(start) is cell) and (type(end) is cell):
			x_run = abs(start.x - end.x)
			y_run = abs(start.y - end.y)

		elif (type(start) is tuple) and (type(end) is cell):
			x_run = abs(start[0] - end.x)
			y_run = abs(start[1] - end.y)

		if x_run!=-1 and y_run!=-1:
			d_max = max(x_run, y_run)
			d_min = min(x_run, y_run)

			diag = ((1.414 * d_min) + (d_max - d_min))
			return diag
		else:
			print("ERROR: Input types (start="+str(type(start))+"), (end="+str(type(end))+") to heuristic are unknown.")
			return 1

	def approximate_euclidean_heuristic(self, start, end):
		x_run = -1
		y_run = -1

		if (type(start) is tuple) and (type(end) is tuple):
			x_run = abs(start[0] - end[0])
			y_run = abs(start[1] - end[1])

		elif (type(start) is cell) and (type(end) is tuple):
			x_run = abs(start.x - end[0])
			y_run = abs(start.y - end[1])

		elif (type(start) is cell) and (type(end) is cell):
			x_run = abs(start.x - end.x)
			y_run = abs(start.y - end.y)

		elif (type(start) is tuple) and (type(end) is cell):
			x_run = abs(start[0] - end.x)
			y_run = abs(start[1] - end.y)

		if x_run!=-1 and y_run!=-1:
			if(y_run >= x_run):
				return (0.41*x_run + 0.94126*y_run)
			else:
				return (0.41*y_run + 0.94126*x_run)
		else:
			print("ERROR: Input types (start="+str(type(start))+"), (end="+str(type(end))+") to heuristic are unknown.")
			return 1

	def manhattan_heuristic(self,start,end):
		x_run = -1
		y_run = -1

		if (type(start) is tuple) and (type(end) is tuple):
			x_run = abs(start[0] - end[0])
			y_run = abs(start[1] - end[1])

		elif (type(start) is cell) and (type(end) is tuple):
			x_run = abs(start.x - end[0])
			y_run = abs(start.y - end[1])

		elif (type(start) is cell) and (type(end) is cell):
			x_run = abs(start.x - end.x)
			y_run = abs(start.y - end.y)

		elif (type(start) is tuple) and (type(end) is cell):
			x_run = abs(start[0] - end.x)
			y_run = abs(start[1] - end.y)

		if x_run!=-1 and y_run!=-1:
			return x_run + y_run
		else:
			print("ERROR: Input types (start="+str(type(start))+"), (end="+str(type(end))+") to heuristic are unknown.")
			return 1

	def approx_distance_heuristic_wrapper(self, start, end):
		x_run = -1
		y_run = -1

		if (type(start) is tuple) and (type(end) is tuple):
			x_run = abs(start[0] - end[0])
			y_run = abs(start[1] - end[1])

		elif (type(start) is cell) and (type(end) is tuple):
			x_run = abs(start.x - end[0])
			y_run = abs(start.y - end[1])

		elif (type(start) is cell) and (type(end) is cell):
			x_run = abs(start.x - end.x)
			y_run = abs(start.y - end.y)

		elif (type(start) is tuple) and (type(end) is cell):
			x_run = abs(start[0] - end.x)
			y_run = abs(start[1] - end.y)

		if x_run!=-1 and y_run!=-1:
			return self.approx_distance(x_run,y_run)
		else:
			print("ERROR: Input types (start="+str(type(start))+"), (end="+str(type(end))+") to heuristic are unknown.")
			return 1

	def approx_distance(self, x_run, y_run):
		min_value = 0
		max_value = 0
		approx = 0

		if(x_run < 0):
			x_run = -1*x_run

		if(y_run < 0):
			y_run = -1*y_run

		if(x_run < y_run):
			min_value = x_run
			max_value = y_run
		else:
			min_value = y_run
			max_value = x_run

		approx = (max_value * 1007) + (min_value * 441)

		if(max_value < (min_value << 4)):
			approx = approx - (max_value * 40)

		return ((approx + 512) >> 10)

	def highway_heuristic(self,start,end):
		base_cost = self.manhattan_heuristic(start,end)

		x0 = -1
		y0 = -1
		x1 = -1
		y1 = -1

		if type(start) is cell:
			x0=start.x
			y0=start.y
		elif type(start) is tuple:
			x0=start[0]
			y0=start[1]
		else:
			print("ERROR: Input types (start="+str(type(start))+"), (end="+str(type(end))+") to heuristic are unknown.")
			return 1

		if type(end) is cell:
			x1=end.x
			y2=end.y
		elif type(end) is tuple:
			x1=end[0]
			y1=end[1]
		else:
			print("ERROR: Input types (start="+str(type(start))+"), (end="+str(type(end))+") to heuristic are unknown.")
			return 1

		s_highway = self.check_for_highway(x0,y0)
		e_highway = self.check_for_highway(x1,y1)
		if s_highway and e_highway:
			return base_cost*0.1
		if s_highway:
			return base_cost*0.2
		if e_highway:
			return base_cost*0.2
		return base_cost

	def heuristic_manager(self, start, end, code, diagonal_multiplier=False):
		if code == 0:
			h = self.manhattan_heuristic(start,end)

		elif code == 1:
			h = self.diagonal_distance_heuristic(start, end)

		elif code == 2:
			h = self.approximate_euclidean_heuristic(start, end)

		elif code == 3:
			h = self.euclidean_heuristic(start, end)
			#if diagonal_multiplier: h *= diagonal_movement_multiplier

		elif code == 4:
			h = self.approx_distance_heuristic_wrapper(start, end)

		elif code == 5:
			h = self.highway_heuristic(start,end)

		else:
			print("WARNING: Using invalid heuristic code: "+str(code))
			h = 0
		return h

	def get_start_or_end_cell(self):
		# helper function for the init_start_end_cells function, see the
		# sakai PDF for details on how the location is chosen
		x_offset = random.randint(0,20)
		y_offset = random.randint(0,20)

		y_ground = random.randint(0,1) # choose if the cell will be in top 20 or bottom 20
		x_ground = random.randint(0,1) # choose if the cell will be in left 20 or right 20

		if x_ground==0:
			x_coord = x_offset
		else:
			x_coord = self.num_columns - 1 - x_offset

		if y_ground==0:
			y_coord = y_offset
		else:
			y_coord = self.num_rows - 1 - y_offset

		coordinate = (x_coord,y_coord)
		return coordinate

	def init_start_end_cells(self):
		# initializes the locations of the start and end cells
		if self.suppress_output==False: print("Creating start/end cells...")
		while True:
			# gereate random start and end cells according to the
			# rules in the Sakai PDF...
			temp_start = self.get_start_or_end_cell()
			temp_end = self.get_start_or_end_cell()

			# check if the generated cells are far enough apart
			if self.get_manhattan_distance(temp_start,temp_end) >= 100:
				if self.get_cell_state(temp_start[0],temp_start[1])=="full":
					continue # cant use if already a fully blocked cell
				if self.get_cell_state(temp_end[0],temp_end[1])=="full":
					continue # cant use if already a fully blocked cell

				self.start_cell = temp_start
				self.end_cell = temp_end
				return

	def init_partially_blocked_cells(self):
		# see Sakai Assignment PDF for explanation.
		# select 8 random regions:
		if self.suppress_output==False: print("Creating partially blocked cells...")
		self.hard_to_traverse_regions = []
		num_regions = 8
		for _ in range(num_regions):
			random.seed()
			x_rand = random.randint(0,self.num_columns-1)
			y_rand = random.randint(0,self.num_rows-1)
			coord = (x_rand,y_rand)
			self.hard_to_traverse_regions.append(coord)

		# iterate over the 8 regions and make a random 50% of the
		# cells in the region be partially blocked. The size of a
		# region is the 31x31 cells centered at that point (15 away
		# in all directions from the center)
		for region_center in self.hard_to_traverse_regions:

			region_center_x = region_center[0]
			region_center_y = region_center[1]

			# top left corner coordinates...
			region_start_x = region_center_x - 15
			region_start_y = region_center_y - 15

			# iterate over every cell in range and select with 50%
			# probability to mark it as partially blocked
			for y in range(region_start_y,region_start_y+30):
				# check that the y coord is in the grid range
				if y>=0 and y<self.num_rows:
					for x in range(region_start_x,region_start_x+30):
						# check that the x coord is in the grid range
						if x>=0 and x<self.num_columns:
							if random.randint(0,1)==1:
								self.set_cell_state(x,y,"partial",add_adjustment=False)

	def clear(self):
		# clears the current grid
		self.init_cells(leave_empty=True)

	def random(self):
		# same as clear but creates a new random grid after clearing
		self.init_cells(leave_empty=False)

	def save(self,filename):
		# saves the current grid to filename location
		f = open(filename, 'w')

		f.write("s_start:("+str(self.start_cell[0])+","+str(self.start_cell[1])+")\n")
		f.write("s_goal:("+str(self.end_cell[0])+","+str(self.end_cell[1])+")\n")
		for hard_cell in self.hard_to_traverse_regions:
			f.write("hard:("+str(hard_cell[0])+","+str(hard_cell[1])+")\n")

		cell_chars = [] # 2D list
		# create 'grid' of cells, each cell represented by a character
		for row in range(self.num_rows):
			row_chars = []
			for column in range(self.num_columns):
				row_chars.append('0')
			row_chars.append('\n')
			cell_chars.append(row_chars)

		num_highway_coordinates = 0
		for cell in self.cells:
			if self.check_for_highway(cell.x,cell.y):
				num_highway_coordinates+=1

		for cell in self.cells:
			x = cell.x
			y = cell.y

			if cell.state == "full":
				if self.check_for_highway(x,y):
					if self.suppress_output==False: print("WARNING: Blocked cell at: ("+str(x)+","+str(y)+"), is in the path of a highway")
				continue

			if cell.state == "free":
				cell_chars[y][x] = '1' if self.check_for_highway(x,y)==False else 'a'
			if cell.state == "partial":
				cell_chars[y][x] = '2' if self.check_for_highway(x,y)==False else 'b'

		cell_chars_str = ""
		for row in cell_chars:
			for item in row:
				cell_chars_str += item
		f.write(cell_chars_str)
		if self.suppress_output==False: print("Saved a total of "+str(num_highway_coordinates)+" highway coordinates.")

	def is_finished_highway(self,highway,conservative=True):
		# checks if both of the endpoints of the highway
		# are at the boundary of the grid. If conservative
		# is set to True then it will ensure the highway runs
		# until at least one outside the grid size
		if highway==None:
			return False
		start_cell = highway[0]
		end_cell = highway[len(highway)-1]

		if len(highway)<100:
			return False

		if self.check_for_boundary(start_cell[0],start_cell[1],conservative) and self.check_for_boundary(end_cell[0],end_cell[1],conservative):
			return True
		return False

	def reconstruct_highways(self,coordinate_list):
		# takes in an unordered list of coordinates and reconstructs the 4 highways,
		# called from the load function below
		broken = [] # list of highway segments
		last = None
		last_cut = 0
		# iterate over the list of highway coordinates and if any consecutive
		# coordinates are greater than a distance of 1 away then cut the the
		# coordinate_list and push the onto the broken list
		for item in coordinate_list:
			if last == None: # if this is the first item
				last = item
				continue
			dist = self.get_manhattan_distance(item,last)
			if dist>1: # if a coordinate for a different highway
				# push all of the highway segment we found before this iteration onto the broken list
				broken.append(coordinate_list[last_cut:coordinate_list.index(item)])
				# save this location as the start of a new highway segment
				last_cut = coordinate_list.index(item)
			last = item # use this as the previous location on the next iteration
		if self.suppress_output==False: print("Initial hwy reconstruction converted "+str(len(coordinate_list))+" coordinates into "+str(len(broken))+" hwy segments...")

		# now we have the broken list with partially reconstructed highway
		# segments but they are most likely not complete, iterate over the
		# stuff in the broken list and connect any highway endpoints that
		# are only a distance of 1 away from eachother
		iterations = 0
		max_allowed = 1000
		while True:
			iterations+=1
			if iterations>max_allowed:
				if self.suppress_output==False: print("ERROR: Could not load the highways for this .grid file.")
				self.highways = broken # save the current reconstruction state for debuggging
				return

			segment = broken[0] # start,end of highway segment (coordinate form)
			if segment == None:
				if self.suppress_output==False: print("WARNING: Found NoneType object in broken list, removing.")
				del broken[0]
				continue

			segment_start = segment[0] # coordinates of start
			segment_end = segment[len(segment)-1] # coordinates of end

			new_broken = []
			for other_item in broken[1:]:
				other_segment_start = other_item[0] # get coordinate of start of other segment
				other_segment_end = other_item[len(other_item)-1] # get coordinate of end of other segment

				segment_start = segment[0] # get coordinate of start of current segment
				segment_end = segment[len(segment)-1] # get coordinate of end of current segment

				if self.get_manhattan_distance(segment_start,other_segment_start)<=1:
					# reverse the current segment and attach the other_item segment to end
					segment.reverse()
					segment.extend(other_item)
				elif self.get_manhattan_distance(segment_start,other_segment_end)<=1:
					# add the current segment onto the end of the other_item segment
					# and set the current item to be equal to other_item segment
					segment.reverse()
					other_item.reverse()
					segment.extend(other_item)

				elif self.get_manhattan_distance(segment_end,other_segment_start)<=1:
					# add the other_item segment onto the end of the current segment
					segment.extend(other_item)
				elif self.get_manhattan_distance(segment_end,other_segment_end)<=1:
					# reverse the other_item segment and add it onto the end of this segment
					other_item.reverse()
					segment.extend(other_item)
				else:
					# not able to attach other_item to current highway segment
					new_broken.append(other_item)
			# add the current segment (now hopfully larger than before this iteration of
			# the while lop) onto the end of the new_broken list so it wont be used
			# as the current segment until all other segments have been used
			new_broken.append(segment)
			broken = new_broken

			# if we have reconstructed all highways
			if len(broken)==4:
				self.highways = broken
				index = 0
				for h in self.highways:
					if self.is_finished_highway(h,conservative=False)==False:
						if self.suppress_output==False: print("WARNING: A Highway found in this file may be corrupted, attempting repair.")
						self.repair_highway(index)
					index+=1
				return

	def get_closest_edge_and_distance(self,coordinates):
		# get the closest wall and the distance to it
		dist_to_top = coordinates[1]
		dist_to_bottom = self.num_rows-coordinates[1]
		dist_to_left = coordinates[0]
		dist_to_right = self.num_columns-coordinates[0]

		#print("Distance to... top:"+str(dist_to_top)+", bottom:"+str(dist_to_bottom)+", left:"+str(dist_to_left)+", right:"+str(dist_to_right))
		if dist_to_top<dist_to_bottom and dist_to_top<dist_to_right and dist_to_top<dist_to_left:
			return ["top",dist_to_top]

		if dist_to_bottom<dist_to_top and dist_to_bottom<dist_to_right and dist_to_bottom<dist_to_left:
			return ["bottom",dist_to_bottom]

		if dist_to_left<dist_to_bottom and dist_to_left<dist_to_right and dist_to_left<dist_to_top:
			return ["left",dist_to_left]

		if dist_to_right<dist_to_bottom and dist_to_right<dist_to_top and dist_to_right<dist_to_left:
			return ["right",dist_to_right]

		return ["None",-1]

	def repair_highway(self,index):
		# if a highway does not register as a legitimate highway using the is_highway_complete function
		# when it is loaded this function is called to try to fix it. added this because sometimes the
		# last cell or two of a highway is lost in the loading process for some reason. if the amount
		# needed to be added to the highway is greater than 5 then it will alert the user and will
		# refrain from fixing it
		broken_highway = self.highways[index]

		start_cell = broken_highway[0]
		end_cell = broken_highway[len(broken_highway)-1]
		if self.check_for_boundary(start_cell[0],start_cell[1],conservative=False)==False:
			# extending the start of the highway to the wall
			edge,distance = self.get_closest_edge_and_distance(start_cell)
			if distance>5:
				if self.suppress_output==False: print("ERROR: Highway reperation was not possible.")
				return
			#print("Start cell ("+str(start_cell[0])+","+str(start_cell[1])+") detached from "+edge+" by ",str(distance))
			if edge == "None":
				if self.suppress_output==False: print("WARNING: Could not repair highway.")
				return
			if edge == "top":
				const = start_cell[0]
				y_start = start_cell[1]
				new_cells = []
				for i in range(distance):
					new_cells.append([const,i])
				new_cells.extend(self.highways[index])
				self.highways[index] = new_cells

			if edge == "bottom":
				const = start_cell[0]
				y_start = start_cell[1]
				new_cells = []
				for i in range(distance):
					new_cells.append([const,y_start+i])
				new_cells.extend(self.highways[index])
				self.highways[index] = new_cells

			if edge == "left":
				const = start_cell[1]
				new_cells = []
				for i in range(distance):
					new_cells.append([i,const])
				new_cells.extend(self.highways[index])
				self.highways[index] = new_cells

			if edge == "right":
				const = start_cell[1]
				x_start = start_cell[0]
				new_cells = []
				for i in range(distance):
					new_cells.append([x_start+i,const])
				new_cells.extend(self.highways[index])
				self.highways[index] = new_cells

		if self.check_for_boundary(end_cell[0],end_cell[1],conservative=False)==False:
			# extending the end of the highway to the wall
			edge,distance = self.get_closest_edge_and_distance(end_cell)
			if distance>5:
				if self.suppress_output==False: print("ERROR: Highway reperation was not possible.")
				return
			#print("End cell ("+str(end_cell[0])+","+str(end_cell[1])+") detached from "+edge+" by ",distance)
			if edge == "None":
				if self.suppress_output==False: print("WARNING: Could not repair highway.")
				return

			if edge == "top":
				const = end_cell[0]
				y_start = end_cell[1]
				new_cells = []
				for i in range(distance):
					self.highways[index].append([const,i])

			if edge == "bottom":
				const = end_cell[0]
				y_start = end_cell[1]
				new_cells = []
				for i in range(distance):
					self.highways[index].append([const,y_start+i])

			if edge == "left":
				const = end_cell[1]
				new_cells = []
				for i in range(distance):
					self.highways[index].append([i,const])

			if edge == "right":
				const = end_cell[1]
				x_start = end_cell[0]
				new_cells = []
				for i in range(distance):
					self.highways[index].append([x_start+i,const])

		if self.suppress_output==False: print("WARNING: Highway was repaired.")
		return

	def load(self,filename):
		# loads in a new set of cells from a file, see the assignment pdf for
		# details on the file format
		f 			= open(filename,'r') # open the file
		lines 		= f.read().split('\n') # split file into lines
		new_cells 	= [] # to hold the new cells
		start_cell 	= None # string (x,y)
		end_cell 	= None # string (x,y)
		hard_to_traverse_regions = [] # to hold (x,y) locations of hard to traverse cells
		highways 	= [] # list of disparate highway coordinates

		if self.suppress_output==False: print("Loading cell data...")
		y = 0
		i = 0
		for line in lines: # iterate over each line of file

			# parse the start cell
			if line.find("s_start:")!=-1:
				start_cell = line.split(":")[1]

			# parse the end cell
			elif line.find("s_goal:")!=-1:
				end_cell = line.split(":")[1]

			# parse out the list of hard region center (8 total)
			elif line.find("hard:")!=-1:
				hard_to_traverse_regions.append(line.split(":")[1])

			# check if line has any data
			elif line in [""," "]:
				# just an empty line, skip it
				continue

			# parse out the grid data (1 line for 1 row of grid)
			else:
				x = 0
				# iterate over each column (1 char for 1 column)
				for char in line:

					cell_state = None
					in_highway = False
					if char == '0':
						cell_state = "full"
					elif char == '1':
						cell_state = "free"
					elif char == '2':
						cell_state = "partial"
					elif char == 'a':
						cell_state = "free"
						coord = (x,y)
						highways.append(coord)
						in_highway = True
					elif char == 'b':
						cell_state = "partial"
						coord = (x,y)
						highways.append(coord)
						in_highway = True
					else:
						if self.suppress_output==False: print("WARNING: Came across invalid cell at location ("+str(x)+","+str(y)+") while loading file.")
						cell_state = "free"

					neighbor_indices = []
					if y==0 and x==0:
						neighbor_indices.append(i+1)
						neighbor_indices.append(i+self.num_columns)
						neighbor_indices.append(i+1+self.num_columns)
					elif y==self.num_rows-1 and x==self.num_columns-1:
						neighbor_indices.append(i-1)
						neighbor_indices.append(i-self.num_columns)
						neighbor_indices.append(i-1-self.num_columns)
					elif y==0 and x==self.num_columns-1:
						neighbor_indices.append(i-1)
						neighbor_indices.append(i+self.num_columns)
						neighbor_indices.append(i-1+self.num_columns)
					elif y==self.num_rows-1 and x==0:
						neighbor_indices.append(i+1)
						neighbor_indices.append(i-self.num_columns)
						neighbor_indices.append(i+1-self.num_columns)
					elif y==0:
						neighbor_indices.append(i-1)
						neighbor_indices.append(i+1)
						neighbor_indices.append(i-1+self.num_columns)
						neighbor_indices.append(i+self.num_columns)
						neighbor_indices.append(i+1+self.num_columns)
					elif y==self.num_rows-1:
						neighbor_indices.append(i-1)
						neighbor_indices.append(i+1)
						neighbor_indices.append(i-1-self.num_columns)
						neighbor_indices.append(i-self.num_columns)
						neighbor_indices.append(i+1-self.num_columns)
					elif x==0:
						neighbor_indices.append(i+1)
						neighbor_indices.append(i-self.num_columns)
						neighbor_indices.append(i+1-self.num_columns)
						neighbor_indices.append(i+self.num_columns)
						neighbor_indices.append(i+1+self.num_columns)
					elif x==self.num_columns-1:
						neighbor_indices.append(i-1)
						neighbor_indices.append(i-self.num_columns)
						neighbor_indices.append(i+self.num_columns)
						neighbor_indices.append(i-1-self.num_columns)
						neighbor_indices.append(i-1+self.num_columns)
					else:
						neighbor_indices.append(i+1)
						neighbor_indices.append(i-1)
						neighbor_indices.append(i-self.num_columns)
						neighbor_indices.append(i+self.num_columns)
						neighbor_indices.append(i-1-self.num_columns)
						neighbor_indices.append(i+1-self.num_columns)
						neighbor_indices.append(i-1+self.num_columns)
						neighbor_indices.append(i+1+self.num_columns)

					new_cell = cell(x,y,i,in_highway)
					new_cell.state = cell_state
					new_cell.neighbor_indices = neighbor_indices
					new_cells.append(new_cell)
					i+=1
					x+=1
				y+=1

		self.cells 		= new_cells
		self.start_cell = eval(start_cell)
		self.end_cell 	= eval(end_cell)
		self.hard_to_traverse_regions 	= []
		for item in hard_to_traverse_regions:
			self.hard_to_traverse_regions.append(eval(item))
		self.associate_cell_neighbors() # fill in cell neighbors
		# now need to flush the elements from the highways list and reorganize
		# it into individual lists that each represent an individual highway
		self.highways = [] # list of lists of coordinates
		if self.suppress_output==False: print("Reconstructing highways...")
		if len(highways)>0: self.reconstruct_highways(highways)
		#print(self.highways)

	def paintEvent(self, e):
		# called by pyqt when it needs to update the widget (dimensions changed, etc.)
		qp = QPainter()
		qp.begin(self)
		self.drawWidget(qp)
		qp.end()

	def drawWidget(self, qp):
		# draw the grid, let the (0,0) cell be in the top left of the window
		if self.verbose:
			if self.suppress_output==False: print("Re-Drawing Grid...",end="\r")

		start_time = time.time() # to time the draw event
		size = self.size() # current size of widget
		width = size.width() # current width of widget
		height = size.height() # current height of widget

		horizontal_step = int(round(width/self.num_columns)) # per cell width
		vertical_step = int(round(height/self.num_rows)) # per cell height

		self.horizontal_step = horizontal_step
		self.vertical_step = vertical_step

		grid_height = vertical_step*self.num_rows
		grid_width = horizontal_step*self.num_columns

		last_color = None # save the color used for the last cell in case its the same for this one

		index = 0

		qp.setPen(Qt.NoPen)

		for cell in self.cells:
			# iterate over each cell and fill in the grid color, also we need
			# to check several conditions such as whether the cell represents one
			# of the states (free, blocked, partially blocked, highway, start point,
			# end point, current location).

			# calculate the cell coordinates from list index
			#x = index % self.num_columns # x coordinate
			#y = int(index/self.num_columns) # get the y coordinate
			x = cell.x
			y = cell.y

			# check if cell is free, partially blocked, or fully blocked
			if cell.state == "free":
				cell_color = self.free_cell_color
			elif cell.state == "partial":
				cell_color = self.trans_cell_color
			elif cell.state == "full":
				cell_color = self.blocked_cell_color
			else:
				if self.suppress_output==False: print("Need to create brushes for cell status:",cell.state)
				cell_color = self.free_cell_color # for now

			# check if cell is the start or end cell
			if x==self.start_cell[0] and y==self.start_cell[1]:
				cell_color = self.start_cell_color
			if x==self.end_cell[0] and y==self.end_cell[1]:
				cell_color = self.end_cell_color

			# check if the cell_color is the same as last time because, if so, dont need to re-set it
			if cell_color != last_color or last_color==None:
				# set the QPainter brush color
				qp.setBrush(QColor(cell_color[0],cell_color[1],cell_color[2]))

			x_start = x*horizontal_step # left of square
			y_start = y*vertical_step # top of square
			qp.drawRect(x_start,y_start,horizontal_step,vertical_step)

			index += 1
			last_color = cell_color
			cell.render_coordinate = [x_start,y_start,horizontal_step,vertical_step]

		# allow user to decide if grid lines should be rendered
		if self.draw_grid_lines:
			# Drawing in grid lines...
			pen = QPen(QColor(self.grid_line_color[0],self.grid_line_color[1],self.grid_line_color[2]), 1, Qt.SolidLine)
			qp.setPen(pen)
			qp.setBrush(Qt.NoBrush)

			for x in range(self.num_columns):
				qp.drawLine(x*horizontal_step,0,x*horizontal_step,grid_height)

			for y in range(self.num_rows):
				qp.drawLine(0,y*vertical_step,grid_width,y*vertical_step)

		if self.draw_outer_boundary:
			# Drawing in outer boundaries
			qp.drawLine(0,0,0,height-1)
			qp.drawLine(0,0,width-1,0)
			qp.drawLine(0,height-1,width-1,height-1)
			qp.drawLine(width-1,0,width-1,height-1)

		# Drawing in highway lines
		pen = QPen(QColor(self.highway_color[0],self.highway_color[1],self.highway_color[2]),self.highway_render_width,Qt.__dict__[self.highway_line_type])
		qp.setPen(pen)
		qp.setBrush(Qt.NoBrush)
		for highway in self.highways:
			if highway == None:
				if self.suppress_output==False: print("Encountered empty list:",highway)
				continue
			last_location = None
			for location in highway:
				if last_location == None:
					last_location = location
					continue
				x1 = (last_location[0]*horizontal_step)+(horizontal_step/2)
				x2 = (location[0]*horizontal_step)+(horizontal_step/2)
				y1 = (last_location[1]*vertical_step)+(vertical_step/2)
				y2 = (location[1]*vertical_step)+(vertical_step/2)
				qp.drawLine(x1,y1,x2,y2)
				last_location = location

		if self.show_solution_swarm:
			# Drawing in solution swarm
			if self.using_gradient: # swarm color that goes from red to blue
				if len(self.solution_path)>0:
					start_gradient = self.start_gradient
					end_gradient = self.end_gradient

					r_delta = abs(float(start_gradient[0]-end_gradient[0])/float(len(self.solution_path)))
					g_delta = abs(float(start_gradient[1]-end_gradient[1])/float(len(self.solution_path)))
					b_delta = abs(float(start_gradient[2]-end_gradient[2])/float(len(self.solution_path)))

					if start_gradient[0]>end_gradient[0]: r_delta=r_delta*-1
					if start_gradient[1]>end_gradient[1]: g_delta=g_delta*-1
					if start_gradient[2]>end_gradient[2]: b_delta=b_delta*-1

					cur_shade = start_gradient
					last_location = None

					for location in self.solution_path:
						pen = QPen(QColor(int(cur_shade[0]),int(cur_shade[1]),int(cur_shade[2])),self.solution_swarm_render_density,Qt.__dict__[self.solution_swarm_line_type])
						qp.setPen(pen)
						cur_shade = [cur_shade[0]+r_delta,cur_shade[1]+g_delta,cur_shade[2]+b_delta]

						if cur_shade[0]<0: cur_shade[0] = 0
						if cur_shade[0]>255: cur_shade[0] = 255
						if cur_shade[1]<0: cur_shade[1] = 0
						if cur_shade[1]>255: cur_shade[1] = 255
						if cur_shade[2]<0: cur_shade[2] = 0
						if cur_shade[2]>255: cur_shade[2] = 255

						if last_location == None:
							last_location = location
							continue

						shorten_gradient = True
						if shorten_gradient:
							x1 = (last_location.x*horizontal_step)+(horizontal_step/2)
							y1 = (last_location.y*vertical_step)+(vertical_step/2)

							x2 = (last_location.x*horizontal_step)+(horizontal_step/2)+((location.x*horizontal_step)*(0.01))
							y2 = (last_location.y*vertical_step)+(vertical_step/2)+((location.y*vertical_step)*(0.01))

						else:
							x1 = (last_location.x*horizontal_step)+(horizontal_step/2)
							y1 = (last_location.y*vertical_step)+(vertical_step/2)

							x2 = (location.x*horizontal_step)+(horizontal_step/2)
							y2 = (location.y*vertical_step)+(vertical_step/2)

						qp.drawLine(x1,y1,x2,y2)
						last_location = location

			else: # solid color swarm
				pen = QPen(QColor(self.solution_swarm_color[0],self.solution_swarm_color[1],self.solution_swarm_color[2]),self.solution_swarm_render_density,Qt.__dict__[self.solution_swarm_line_type])
				qp.setPen(pen)
				last_location = None
				for location in self.solution_path:
				#for location in self.solution_path:
					if last_location == None:
						last_location = location
						continue

					shorten_gradient = True
					if shorten_gradient:
						x1 = (last_location.x*horizontal_step)+(horizontal_step/2)
						y1 = (last_location.y*vertical_step)+(vertical_step/2)

						x2 = (last_location.x*horizontal_step)+(horizontal_step/2)+((location.x*horizontal_step)*(0.01))
						y2 = (last_location.y*vertical_step)+(vertical_step/2)+((location.y*vertical_step)*(0.01))

					else:
						x1 = (last_location.x*horizontal_step)+(horizontal_step/2)
						y1 = (last_location.y*vertical_step)+(vertical_step/2)

						x2 = (location.x*horizontal_step)+(horizontal_step/2)
						y2 = (location.y*vertical_step)+(vertical_step/2)

					qp.drawLine(x1,y1,x2,y2)
					last_location = location

		# Drawing in the prior solution paths
		if self.show_path_trace:
			pen = QPen(QColor(self.trace_color[0],self.trace_color[1],self.trace_color[2]),self.trace_render_width,Qt.__dict__[self.solution_trace_line_type])
			qp.setPen(pen)
			for path in self.path_traces:
				last_location = None
				for location in path:
					if last_location == None:
						last_location = location
						continue
					x1 = (last_location[0]*horizontal_step)+(horizontal_step/2)
					x2 = (location[0]*horizontal_step)+(horizontal_step/2)
					y1 = (last_location[1]*vertical_step)+(vertical_step/2)
					y2 = (location[1]*vertical_step)+(vertical_step/2)
					qp.drawLine(x1,y1,x2,y2)
					last_location = location

		# Drawing in solution path
		pen = QPen(QColor(self.solution_color[0],self.solution_color[1],self.solution_color[2]),self.solution_render_width,Qt.__dict__[self.solution_line_type])
		qp.setPen(pen)
		last_location = None
		for location in self.shortest_path:
			if last_location == None:
				last_location = location
				continue
			x1 = (last_location[0]*horizontal_step)+(horizontal_step/2)
			x2 = (location[0]*horizontal_step)+(horizontal_step/2)
			y1 = (last_location[1]*vertical_step)+(vertical_step/2)
			y2 = (location[1]*vertical_step)+(vertical_step/2)
			qp.drawLine(x1,y1,x2,y2)
			last_location = location

		if self.render_mouse and self.allow_render_mouse:
			if self.mouse_location!=None:
				qp.setBrush(QColor(self.mouse_color[0],self.mouse_color[1],self.mouse_color[2]))
				pen = QPen(QColor(0,0,0),1,Qt.SolidLine)
				qp.setPen(pen)

				x = self.mouse_location[0] # = (x coordinate of mouse) / self.horizontal_step
				y = self.mouse_location[1] # = (y coordinate of mouse) / self.vertical_step

				if self.mouse_render_location!=None:
					x = self.mouse_render_location[0]
					y = self.mouse_render_location[1]

				for cell in self.cells:
					if cell.x==x and cell.y==y:
						qp.drawRect(cell.render_coordinate[0],cell.render_coordinate[1],horizontal_step,vertical_step)
						break

					#if x>=(cell.render_coordinate[0]) and x<(cell.render_coordinate[0]+horizontal_step):
					#	if y>=(cell.render_coordinate[1]) and y<(cell.render_coordinate[1]+vertical_step):
					#		qp.drawRect(cell.render_coordinate[0],cell.render_coordinate[1],horizontal_step,vertical_step)
					#		break

				if self.trace_highlighting:

					if self.current_path != None:
						pen = QPen(QColor(self.mouse_color[0],self.mouse_color[1],self.mouse_color[2]),self.solution_render_width,Qt.__dict__[self.solution_line_type])
						qp.setPen(pen)

						last_location = None
						for location in self.current_path:
							if last_location==None:
								last_location = location
								continue
							x1 = (last_location[0]*horizontal_step)+(horizontal_step/2)
							x2 = (location[0]*horizontal_step)+(horizontal_step/2)
							y1 = (last_location[1]*vertical_step)+(vertical_step/2)
							y2 = (location[1]*vertical_step)+(vertical_step/2)
							qp.drawLine(x1,y1,x2,y2)
							last_location = location

		if self.verbose:
			if self.suppress_output==False:
				print("                                                                           ",end="\r")
				print("Re-Drawing Grid: "+str(time.time()-start_time)[:5]+" seconds")

	def get_manhattan_distance(self,cell1,cell2):
		# calculates manhattan distance
		x_run = abs(cell1[0]-cell2[0])
		y_run = abs(cell1[1]-cell2[1])
		return x_run+y_run

	def set_cell_state(self,x_coord,y_coord,state,add_adjustment=True):
		# updates a single cell in the grid with a new state then reloads the ui

		# if the coordinates are sent from the UI main_window instance they may
		# not align exactly with the cell coordinates in the grid so we need to adjust
		if add_adjustment:
			# need to iterate over the cells in the self.cells list and check their self.render_coordinate
			# values to match them to the ones provided (x_coord,y_coord)

			x = -1
			y = -1

			for cell in self.cells:
				if x_coord>=cell.render_coordinate[0] and x_coord<(cell.render_coordinate[0]+cell.render_coordinate[2]):
					if y_coord>=cell.render_coordinate[1] and y_coord<(cell.render_coordinate[1]+cell.render_coordinate[3]):
						x = cell.x
						y = cell.y
						break

			if x==-1 and y==-1:
				if self.suppress_output==False: print("ERROR: Could not locate ("+str(x_coord)+","+str(y_coord)+") coordinates in set_cell_state().")

		else:
			x = x_coord
			y = y_coord

		# if the change is to the start or end cell then we don't need to change any cells
		if state == "start":
			self.start_cell = (x,y)
			return
		if state == "end":
			self.end_cell = (x,y)
			return

		index = 0
		for cell in self.cells:
			#cur_x = index % self.num_columns
			#cur_y = int(index/self.num_columns)

			if x==cell.x and y==cell.y:
				#print("Changing cell to "+state)
				self.cells[index].state = state
				return

			index += 1

	def get_cell_state(self,x_coord,y_coord,add_adjustment=False):
		# locates the cell in question and returns the state
		if add_adjustment:
			x = -1
			y = -1
			for cell in self.cells:
				if x_coord>=cell.render_coordinate[0] and x_coord<(cell.render_coordinate[0]+cell.render_coordinate[2]):
					if y_coord>=cell.render_coordinate[1] and y_coord<(cell.render_coordinate[1]+cell.render_coordinate[3]):
						return cell.state
			if x==-1 and y==-1:
				if self.suppress_output==False: print("ERROR: Could not locate cell in question ("+str(x)+","+str(y)+")")
				return "ERROR"
		else:
			for cell in self.cells:
				if x_coord==cell.x and y_coord==cell.y:
					return cell.state

	def set_attrib_color(self,attrib="free",color=[0,0,0]):
		# called by the main_window, sets the color of a certain attribute
		if attrib == "free":
			self.free_cell_color = color
		elif attrib == "highway":
			self.highway_color = color
		elif attrib == "full":
			self.blocked_cell_color = color
		elif attrib == "partial":
			self.trans_cell_color = color
		elif attrib == "start":
			self.start_cell_color = color
		elif attrib == "end":
			self.end_cell_color = color
		elif attrib == "solution_swarm":
			self.solution_swarm_color = color
		elif attrib == "solution":
			self.solution_color = color
		elif attrib == "start_gradient":
			self.start_gradient = color
		elif attrib == "end_gradient":
			self.end_gradient = color
		elif attrib == "path_trace":
			self.trace_color = color
		else:
			if self.suppress_output==False: print("Unknown attribute: "+attrib)

	def set_attrib_value(self,attrib,value):
		if attrib == "Solution Swarm Density":
			self.solution_swarm_render_density = value
		elif attrib == "Solution Trace Width":
			self.trace_render_width = value
		elif attrib == "Solution Path Width":
			self.solution_render_width = value
		elif attrib == "Highway Width":
			self.highway_render_width = value
		else:
			if self.suppress_output==False: print("Unknown attribute: "+attrib)

	def set_line_type(self,attrib,value):
		if attrib == "Highway":
			self.highway_line_type = value
		elif attrib == "Solution Path":
			self.solution_line_type = value
		elif attrib == "Solution Trace":
			self.solution_trace_line_type = value
		elif attrib == "Solution Swarm":
			self.solution_swarm_line_type = value
		else:
			if self.suppress_output==False: print("Unknown attribute: "+attrib)

	def get_update(self,new_attribs):
		# slot called from the ucs_agent thread, updates the ui
		global updating_ui
		global ui_update_time
		#print("\nGot signal")
		if updating_ui:
			#print("Already updating")
			if new_attribs.done==False: return
		start_time = time.time()
		updating_ui = True
		self.solution_path = new_attribs.solution_path
		self.shortest_path = new_attribs.shortest_path
		self.path_traces = new_attribs.path_traces
		self.repaint()
		self.pyqt_app.processEvents()
		QApplication.processEvents()
		if new_attribs.done:
			self.verbose = True
		ui_update_time = time.time()-start_time
		updating_ui = False

	def connect_to_ucs_agent(self,agent_handle):
		QtCore.QObject.connect(agent_handle,QtCore.SIGNAL("send_update_to_ui(PyQt_PyObject)"),self.get_update)

class PriorityQueue:

	def __init__(self,max_len=20000):
		self._queue = []
		self._index = 0
		self.max_len = max_len
		self.cells_in_queue = [False] * max_len

	def push(self, item, cost, parent):
		# Push element onto queue
		item.cost = cost # save the cost to the cell struct
		item.parent = parent
		#heapq.heappush(self._queue, (cost, self._index, item))
		heapq.heappush(self._queue, (cost, self._index, item))
		self.cells_in_queue[item.index] = True
		self._index += 1

	def pop(self):
		# Return the item with the lowest cost
		index,item = heapq.heappop(self._queue)[1:]
		self.cells_in_queue[item.index] = False
		self._index += -1
		return item

	def top(self):
		return self._queue[0][-1]
		return temp

	def length(self):
		# Return the length of the queue
		return len(self._queue)

	def clear(self):
		self._queue = []
		self._index = 0
		self.cells_in_queue = [False] * self.max_len

	def has_cell(self,cell):
		# Returns True if the cell is in the queue, False if not
		return self.cells_in_queue[cell.index]

	def update_or_insert(self,cell,cost,parent):
		# either updates the cell cost or inserts it as a new cell if not yet in queue
		if self.has_cell(cell):
			self.replace_cell(cell,cost,parent)
		else:
			self.push(cell,cost,parent)

	def remove(self,cell):
		i = 0
		for item in self._queue:
			queued_cell = item[-1]
			if cell.index==queued_cell.index:
				del self._queue[i]
				self._index += -1
				return True
			i+=1
		return False

	def replace_cell(self,cell,new_cost,parent):
		i = 0
		for item in self._queue:
			#queued_cell = item[2]
			queued_cell = item[-1]
			#if queued_cell.x==cell.x and queued_cell.y==cell.y:
			if queued_cell.index==cell.index:
				del self._queue[i]
				self._index += -1
				break
			i+=1
		self.push(cell,new_cost,parent)

	def get_cell_cost(self,cell):
		for cost,_,item in self._queue:
			if cell.index==item.index: return cost

	def Minkey(self):
		# returns the value of the smallest cost
		#print(self._queue)
		return self.top().cost

def get_neighbors(current,cells):
	# Returns a list of all 8 neighbor cells to "current"
	return current.neighbors
	'''
	x = current.x
	y = current.y
	neighbors = []
	for cell in cells:
		if cell.x in [x,x-1,x+1] and cell.y in [y,y-1,y+1]:
			neighbors.append(cell)
	return neighbors
	'''
def cell_in_list(current,cells):
	# Returns True if "current" is in the list, False if not
	for cell in cells:
		#if current.x==cell.x and current.y==cell.y:
		if current.index==cell.index:
			return True
	return False

def get_cell_index(current, cells):
 	#Returns the index of where a given cell is in the global cells list
	#used to keep track of the costs of getting to each cell in the grid
	for i in range(len(cells)):
		matching_cell = cells[i]
		if matching_cell.x==current.x and matching_cell.y==current.y:
			return i
	return -1

def get_transition_cost(current_cell,new_cell):
	# Calculates the cost of transitioning from current_cell to new_cell
	# recall: state can be one of: "free", "partial", "full"
	current_state = current_cell.state
	new_state = new_cell.state

	if current_cell.x==new_cell.x or current_cell.y==new_cell.y:
		orientation = "horizontal_or_vertical"
	else:
		orientation = "diagonal"

	# move from free cell to free cell
	if current_state=="free" and new_state=="free":
		if orientation=="diagonal":
			cost = sqrt(2)
		else:
			cost = 1

	# move from "hard to traverse" cell to another "hard to traverse" cell
	elif current_state=="partial" and new_state=="partial":
		if orientation=="diagonal":
			cost = sqrt(8)
		else:
			cost = 2

	# move from free cell to "hard to traverse" cell
	elif current_state=="free" and new_state=="partial":
		if orientation=="diagonal":
			cost = (sqrt(2)+sqrt(8))/2
		else:
			cost = 1.5

	# move from "hard to traverse" cell to free cell
	elif current_state=="partial" and new_state=="free":
		if orientation=="diagonal":
			cost = (sqrt(2)+sqrt(8))/2
		else:
			cost = 1.5

	# trying to traverse to blocked cell
	elif new_state=="full":
		cost = -1
		return cost

	else:
		print("Could not decode cell transition from "+current_state+" to "+new_state)
		cost = -1
		return cost

	# now need to check if both cells are in a highway
	if orientation == "horizontal_or_vertical":
		if current_cell.in_highway and new_cell.in_highway:
			cost *= 0.25
	return cost

def rectify_path(path_end,break_short=False):
	global function_log
	path = []
	cur = path_end
	path.append([cur.x,cur.y])
	while True:
		cur = cur.parent
		if cur==None: 
			break
		path.append([cur.x,cur.y])
	return path

class message: # used as a connnection between eight_neighbor_grid and uniform_cost_search
	def __init__(self):
		self.solution_path = []
		self.shortest_path = []
		self.path_traces = []
		self.done = False

class cell_information: # used as a message between eight_neighbor_grid and main_window for updating cell information
	def __init__(self):
		self.state = ""
		self.h = ""
		self.g = ""
		self.f = ""
		self.coordinates = ""
		self.is_valid = False

class uniform_cost_search(QThread):
	def __init__(self):
		QThread.__init__(self)
		self.ready_to_start = False # if we have the data needed to start
		self.stop_executing = False # if true then will stop the algorithm
		self.app = None

	def load_grid_data(self,cells,start_cell,end_cell,highways):
		self.cells = cells
		self.start_cell = start_cell
		self.end_cell = end_cell
		self.highways = highways
		self.ready_to_start = True

	def run(self):
		# Called when the thread is started
		self.uniform_cost()

	def uniform_cost(self):
		# threaded implementation of the uniform cost search
		self.stop_executing = False # Ctrl+C calls clear which will set this to true

		# indicate the refresh rates here
		refresh_rate = 0.1 # at least every this many seconds refresh
		cost_refresh_rate = 1 # refresh if the algo has increased the current fringe cost by this much
		explored_refresh_rate = 100 # refresh if the algo has increased the explorted count by this much

		self.overall_start = time.time()

		self.path_cost = 0 # overall path cost
		self.tried_paths = [] # to hold all paths shown to user

		self.frontier = PriorityQueue()
		self.frontier.push(self.start_cell,0,parent=None)
		self.path_end = self.start_cell
		self.path_length = 1

		self.explored = [] # empty set

		msg_to_main = message()

		while True:
			done = self.uniform_cost_step(refresh_rate,cost_refresh_rate,explored_refresh_rate)
			msg_to_main.solution_path = self.explored
			msg_to_main.shortest_path = rectify_path(self.path_end)
			self.tried_paths.append(msg_to_main.shortest_path)
			msg_to_main.path_traces = self.tried_paths
			msg_to_main.done = done

			if updating_ui: # allow for time for the ui to update
				for _ in range(4):
					if updating_ui:
						time.sleep(ui_update_time*0.2)
					else:
						break

			if done==True or updating_ui==False:
				# if this is the last update or the ui is ready for another
				self.emit(SIGNAL("send_update_to_ui(PyQt_PyObject)"),msg_to_main)
			if done:
				break

	def uniform_cost_step(self,refresh_rate,cost_refresh_rate,explored_refresh_rate):
		# helper function for uniform_cost search, performs only refresh_rate seconds then returns
		start_time = time.time() # to log the amount of time taken
		last_path_cost = self.path_cost
		initial_explored = len(self.explored)

		while True:

			if self.stop_executing:
				return True

			print("explored: "+str(len(self.explored))+", frontier: "+str(self.frontier.length())+", time: "+str(time.time()-self.overall_start)[:6]+", cost: "+str(self.path_cost)[:6],end="\r")

			if self.frontier.length() == 0:
				print("ERROR: Uniform cost search failed to find a solution path.")
				return True

			cur_node = self.frontier.pop()
			self.path_cost = cur_node.cost # get the path cost so far

			if cur_node.x==self.end_cell[0] and cur_node.y==self.end_cell[1]:
				# if we have reached the goal node
				self.path_end = cur_node
				break

			self.explored.append(cur_node) # add current node to explored list
			node_neigbors = get_neighbors(cur_node,self.cells)

			for neighbor in node_neigbors:
				transition_cost = get_transition_cost(cur_node,neighbor)

				# if not explored yet and not in frontier already
				if cell_in_list(neighbor,self.explored)==False and self.frontier.has_cell(neighbor)==False:
					# if not a blocked cell
					if transition_cost!=-1:
						# add to frontier
						self.frontier.push(neighbor,self.path_cost+transition_cost,parent=cur_node)

				# if in the frontier already
				elif self.frontier.has_cell(neighbor)==True:
					# if version in frontier has higher cost
					if self.frontier.get_cell_cost(neighbor)>(self.path_cost+transition_cost):
						self.frontier.replace_cell(neighbor,self.path_cost+transition_cost,parent=cur_node)

			# refresh the display if the algorithm has checked explored_refresh_rate cells
			if len(self.explored)>(initial_explored+explored_refresh_rate):
				self.path_end = cur_node
				return False # refresh the display

			# refresh the display if the algorithm has increased the current cost by cost_refresh_rate
			if self.path_cost>(last_path_cost+cost_refresh_rate):
				self.path_end = cur_node
				return False # refresh the display

			# at least refresh every "refresh_rate" seconds
			if int(time.time()-start_time)>refresh_rate:
				self.path_end = cur_node
				return False # refresh the display
		print("\nFinished uniform cost search in "+str(time.time()-self.overall_start)[:6]+" seconds, final cost: "+str(self.path_cost)+", checked "+str(len(explored))+" cells\n")
		print("\nFinished uniform cost search in "+str(time.time()-self.overall_start)[:6]+" seconds, final cost: "+str(self.path_cost)+"\n")
		return True

def get_path_cost(node):
	# given an node, this function will traverse up all of the node parents
	# and keep a tally of the cost of traverse up until the last parent
	total_cost = 0
	current_node = node
	next_node = None
	while True:
		next_node = current_node.parent
		if next_node == None:
			return total_cost
		total_cost += get_transition_cost(current_node,next_node)
		current_node = next_node
	print("ERROR: Got to end of get_path_cost without reaching a node w/o a parent")
