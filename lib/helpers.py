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

# class to hold the image on the grid that represents the current location
class character_image(QLabel):

	def __init__(self, img, parent=None):
		# constructor, pass the path to the image that will be used
		super(character_image, self).__init__()
		self.setFrameStyle(QtGui.QFrame.StyledPanel)
		self.pixmap = QtGui.QPixmap(img)

	def paintEvent(self, event):
		# called whenever the image needs to be drawn
		size = self.size()
		painter = QtGui.QPainter(self)
		point = QtCore.QPoint(0,0)
		scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
		# start painting the label from left upper corner
		point.setX((size.width() - scaledPix.width())/2)
		point.setY((size.height() - scaledPix.height())/2)
		print (point.x(), ' ', point.y())
		painter.drawPixmap(point, scaledPix)

	def changePixmap(self, img):
    	# can change the image used
		self.pixmap = QtGui.QPixmap(img)
		self.repaint()

# class to hold details for a single cell
class cell:

	def __init__(self,x_coordinate=None,y_coordinate=None):
		self.state = "free"
		self.x = x_coordinate # not using anymore
		self.y = y_coordinate # not using anymore
		self.cost = 0 # used for Priority Queue to remember cost
		self.parent = None

# UI element (widget) that represents the interface with the grid
class eight_neighbor_grid(QWidget):

	def __init__(self,num_columns=160,num_rows=120,use_character=False):
		# constructor, pass the number of cols and rows
		super(eight_neighbor_grid,self).__init__()		
		self.num_columns = num_columns # width of the board
		self.num_rows = num_rows # height of the board
		self.using_game_character = use_character # leave as false, see init_ui line
		self.init_ui() # initialize a bunch of class instance variables

	def init_ui(self):
		# initialize ui elements
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
		
		self.solution_swarm_render_density = 0.1 # width of the solution swarm lines (from ~0.1 to ~2.0 probably)
		self.highway_render_width = 2.0 # width of the highways shown in window (2.0 is default)
		self.solution_render_width = 5.0 # width of the solution path (5.0 is good default)


		if self.using_game_character:
			# trying to allow user to select an image to use as the current location on the grid
			self.pic = character_image(os.getcwd()+"/resources/character.png",self)

		self.draw_outer_boundary = False # if true, an outer boundary is drawn in bottom right
		self.draw_grid_lines = False # set to false by default
		self.show_solution_swarm = True # set to true by default
		self.show_path_trace = True # if true then show the prior tried paths
		self.using_gradient = False # if true then solution swarm will be gradient
		self.init_cells(leave_empty=True) # more instance variables that can be reset more easily from within instance

	def init_cells(self,leave_empty=False):
		# creates the list of cells in the grid (all default to free), if leave_empty
		# is False then we will fill in the grid following the instructions in the
		# assignment pdf 
		self.cells = []
		self.verbose = True # if true then the time to paint the grid will be printed to terminal
		for y in range(self.num_rows):
			for x in range(self.num_columns):
				new_cell = cell(x,y)
				self.cells.append(new_cell)

		self.start_cell = (0,0) # default start cell
		self.end_cell = (self.num_columns-1,self.num_rows-1) # default end cell
		self.hard_to_traverse_regions = [] # empty by default
		self.highways = [] # empty by default
		self.solution_path = [] # the path eventually filled by one of the search algos
		self.shortest_path = []
		self.path_traces = [] # list of all paths tried (shown to user)			
		if leave_empty: return 

		print("\nGenerating a random grid...")
		start_time = time.time()
		self.init_partially_blocked_cells() # init the partially blocked
		self.init_highways() # initialize the 4 highways
		self.init_blocked_cells() # initialize the completely blocked cells
		self.init_start_end_cells() # initialize the start/end locations
		self.solution_path = [] # the path eventually filled by one of the search algos
		print("Finished generating random grid, "+str(time.time()-start_time)+" seconds\n")

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
					if self.check_for_highway(cur_x,cur_y,highway_path)==False:
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

		print("                                                                             ",end='\r')
		print("Exhausted "+str(num_attempts)+" attempts, "+str(total_attempts)+" total.",end='\r')
		return num_attempts

	def init_highways(self):
		print("Placing highways...")
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
		print("\n",end='\r') # save the last entry output from the get_highway() function
			
	def init_blocked_cells(self):
		# choose 20% of the remaining cells to mark as fully blocked, Sakai PDF
		print("Creating fully blocked cells...")
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

	def get_euclidean_distance(self,cell1,cell2):
		# calculates the length of the straight line distance between two cells
		x_run = abs(cell1[0]-cell2[0]) 
		y_run = abs(cell1[1]-cell2[1])
		return sqrt((x_run**2)+(y_run**2))

	def get_manhattan_distance(self,cell1,cell2):
		# calculates manhattan distance
		x_run = abs(cell1[0]-cell2[0]) 
		y_run = abs(cell1[1]-cell2[1])
		return x_run+y_run

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
		print("Creating start/end cells...")
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
		print("Creating partially blocked cells...")
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

		for cell in self.cells:		
			x = cell.x 
			y = cell.y 

			if cell.state == "full":
				if self.check_for_highway(x,y):
					print("WARNING: Blocked cell at: ("+str(x)+","+str(y)+"), is in the path of a highway")
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

		print("Initial hwy reconstruction converted "+str(len(coordinate_list))+" coordinates into "+str(len(broken))+" hwy segments...")

		# now we have the broken list with partially reconstructed highway
		# segments but they are most likely not complete, iterate over the 
		# stuff in the broken list and connect any highway endpoints that
		# are only a distance of 1 away from eachother
		iterations = 0
		max_allowed = 10000
		while True:
			iterations+=1
			if iterations>max_allowed:
				print("ERROR: Could not load the highways for this .grid file.")
				self.highways = broken # save the current reconstruction state for debuggging
				return

			segment = broken[0] # start,end of highway segment (coordinate form)
			if segment == None:
				print("WARNING: Found NoneType object in broken list, removing.")
				del broken[0]
				continue

			segment_start = segment[0] # coordinates of start
			segment_end = segment[len(segment)-1] # coordinates of end

			new_broken = []
			for other_item in broken:
				if broken.index(other_item)!=0:
					other_segment_start = other_item[0]
					other_segment_end = other_item[len(other_item)-1]

					segment_start = segment[0]
					segment_end = segment[len(segment)-1]

					if self.get_manhattan_distance(segment_start,other_segment_start)<=1:
						# reverse the current segment and attach the other_item segment to end
						segment.reverse()
						segment.extend(other_item)
					elif self.get_manhattan_distance(segment_start,other_segment_end)<=1:
						# add the current segment onto the end of the other_item segment
						# and set the current item to be equal to other_item segment
						segment.reverse()
						other_segment.reverse()
						segment.extend(other_segment)
						
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
				for h in self.highways:
					if self.is_finished_highway(h,False)==False:
						print("WARNING: A Highway found in this file may be corrupted.")
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

		print("Loading cell data...")
		y = 0
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
					elif char == 'b':
						cell_state = "partial"
						coord = (x,y)
						highways.append(coord)
					new_cell = cell(x,y)
					new_cell.state = cell_state
					new_cells.append(new_cell)
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
		print("Reconstructing highways...")
		self.reconstruct_highways(highways)
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
			print("Re-Drawing Grid...",end="\r")

		start_time = time.time() # to time the draw event
		size = self.size() # current size of widget
		width = size.width() # current width of widget
		height = size.height() # current height of widget

		horizontal_step = int(round(width/self.num_columns)) # per cell width
		vertical_step = int(round(height/self.num_rows)) # per cell height

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
				print("Need to create brushes for cell status:",cell.state)
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
		pen = QPen(QColor(self.highway_color[0],self.highway_color[1],self.highway_color[2]),self.highway_render_width,Qt.SolidLine)
		qp.setPen(pen)
		qp.setBrush(Qt.NoBrush)
		for highway in self.highways:
			if highway == None:
				print("Encountered empty list:",highway)
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
						pen = QPen(QColor(int(cur_shade[0]),int(cur_shade[1]),int(cur_shade[2])),self.solution_swarm_render_density,Qt.DashLine)
						qp.setPen(pen)
						cur_shade = [cur_shade[0]+r_delta,cur_shade[1]+g_delta,cur_shade[2]+b_delta]
						
						if last_location == None:
							last_location = location
							continue
						x1 = (last_location.x*horizontal_step)+(horizontal_step/2)
						x2 = (location.x*horizontal_step)+(horizontal_step/2)
						y1 = (last_location.y*vertical_step)+(vertical_step/2)
						y2 = (location.y*vertical_step)+(vertical_step/2)
						qp.drawLine(x1,y1,x2,y2)
						last_location = location
			
			else: # solid color swarm
				pen = QPen(QColor(self.solution_swarm_color[0],self.solution_swarm_color[1],self.solution_swarm_color[2]),self.solution_swarm_render_density,Qt.DashLine)
				qp.setPen(pen)
				last_location = None
				for location in self.solution_path:
				#for location in self.solution_path:
					if last_location == None:
						last_location = location
						continue
					x1 = (last_location.x*horizontal_step)+(horizontal_step/2)
					x2 = (location.x*horizontal_step)+(horizontal_step/2)
					y1 = (last_location.y*vertical_step)+(vertical_step/2)
					y2 = (location.y*vertical_step)+(vertical_step/2)
					qp.drawLine(x1,y1,x2,y2)
					last_location = location

		# Drawing in the prior solution paths
		if self.show_path_trace:
			pen = QPen(QColor(self.trace_color[0],self.trace_color[1],self.trace_color[2]),0.1,Qt.DashLine)
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
		pen = QPen(QColor(self.solution_color[0],self.solution_color[1],self.solution_color[2]),self.solution_render_width,Qt.SolidLine)
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

		if self.verbose:
			print("                                                                           ",end="\r")
			print("Re-Drawing Grid: "+str(time.time()-start_time)[:5]+" seconds")

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
			
	def toggle_grid_lines(self,grid_lines):
		self.draw_grid_lines = grid_lines 

	def toggle_solution_swarm(self,show_swarm):
		self.show_solution_swarm = show_swarm

	def toggle_gradient(self,use_gradient):
		self.using_gradient = use_gradient

	def toggle_trace(self,use_trace):
		self.show_path_trace = use_trace

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
			print("Unknown attribute: "+attrib)


class PriorityQueue:
	def __init__(self):
		self._queue = []
		self._index = 0

	def push(self, item, cost, parent):
		# Push element onto queue
		item.cost = cost # save the cost to the cell struct
		item.parent = parent
		heapq.heappush(self._queue, (cost, self._index, item))
		self._index += 1

	def pop(self):
		# Return the item with the lowest cost
		return heapq.heappop(self._queue)[-1]

	def length(self):
		# Return the length of the queue
		return len(self._queue)

	def has_cell(self,cell):
		# Returns True if the cell is in the queue, False if not
		for item in self._queue:
			queued_cell = item[2]
			if cell.x==queued_cell.x and cell.y==queued_cell.y:
				return True 
		return False

	def replace_cell(self,cell,new_cost,parent):
		i = 0
		for item in self._queue:
			queued_cell = item[2]
			if queued_cell.x==cell.x and queued_cell.y==cell.y:
				del self._queue[i]
				break
			i+=1
		self.push(queued_cell,new_cost,parent)

	def get_cell_cost(self,cell):
		for item in self._queue:
			if cell.x==item[2].x and cell.y==item[2].y:
				return item[2].cost

def get_neighbors(current,cells):
	# Returns a list of all 8 neighbor cells to "current"
	x = current.x 
	y = current.y 
	neighbors = []
	for cell in cells:
		if cell.x in [x,x-1,x+1] and cell.y in [y,y-1,y+1]:
			neighbors.append(cell)
	return neighbors

def cell_in_list(current,cells):
	# Returns True if "current" is in the list, False if not
	for cell in cells:
		if current.x==cell.x and current.y==cell.y:
			return True 
	return False

def cell_in_highway(current,highways):
	for h in highways:
		for item in h:
			if item[0]==current.x and item[1]==current.y:
				return True 
	return False

def get_transition_cost(current_cell,new_cell,highways):
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

	else:
		print("Could not decode cell transition from "+current_state+" to "+new_state)
		cost = -1

	# now need to check if both cells are in a highway
	if orientation == "horizontal_or_vertical":
		if cell_in_highway(current_cell,highways)==True and cell_in_highway(new_cell,highways)==True:
			cost = cost*0.25

	return cost

def rectify_path(path_end):
	path = []
	cur = path_end
	path.append([cur.x,cur.y])
	while True:
		cur = cur.parent
		if cur == None:
			break
		path.append([cur.x,cur.y])
	return path


class PriorityQueue:
	def __init__(self):
		self._queue = []
		self._index = 0

	def push(self, item, cost, parent):
		# Push element onto queue
		item.cost = cost # save the cost to the cell struct
		item.parent = parent
		heapq.heappush(self._queue, (cost, self._index, item))
		self._index += 1

	def pop(self):
		# Return the item with the lowest cost
		return heapq.heappop(self._queue)[-1]

	def length(self):
		# Return the length of the queue
		return len(self._queue)

	def has_cell(self,cell):
		# Returns True if the cell is in the queue, False if not
		for item in self._queue:
			queued_cell = item[2]
			if cell.x==queued_cell.x and cell.y==queued_cell.y:
				return True 
		return False

	def replace_cell(self,cell,new_cost,parent):
		i = 0
		for item in self._queue:
			queued_cell = item[2]
			if queued_cell.x==cell.x and queued_cell.y==cell.y:
				del self._queue[i]
				break
			i+=1
		self.push(queued_cell,new_cost,parent)

	def get_cell_cost(self,cell):
		for item in self._queue:
			if cell.x==item[2].x and cell.y==item[2].y:
				return item[2].cost

def get_neighbors(current,cells):
	# Returns a list of all 8 neighbor cells to "current"
	x = current.x 
	y = current.y 
	neighbors = []
	for cell in cells:
		if cell.x in [x,x-1,x+1] and cell.y in [y,y-1,y+1]:
			neighbors.append(cell)
	return neighbors

def cell_in_list(current,cells):
	# Returns True if "current" is in the list, False if not
	for cell in cells:
		if current.x==cell.x and current.y==cell.y:
			return True 
	return False

def cell_in_highway(current,highways):
	for h in highways:
		for item in h:
			if item[0]==current.x and item[1]==current.y:
				return True 
	return False

def get_transition_cost(current_cell,new_cell,highways):
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

	else:
		print("Could not decode cell transition from "+current_state+" to "+new_state)
		cost = -1

	# now need to check if both cells are in a highway
	if orientation == "horizontal_or_vertical":
		if cell_in_highway(current_cell,highways)==True and cell_in_highway(new_cell,highways)==True:
			cost = cost*0.25

	return cost

def rectify_path(path_end):
	path = []
	cur = path_end
	path.append([cur.x,cur.y])
	while True:
		cur = cur.parent
		if cur == None:
			break
		path.append([cur.x,cur.y])
	return path