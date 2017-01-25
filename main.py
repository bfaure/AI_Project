# python 2.7
from __future__ import print_function
import os
import sys

import time
import random

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

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
		self.line_color = [0,0,0] # black for cell lines
		self.free_cell_color = [255,255,255] # white for free cell
		#self.free_cell_color = [1,166,17] # green for free cell
		self.trans_cell_color = [128,128,128] # gray cell for partially blocked
		self.blocked_cell_color = [0,0,0] # black cell for blocked
		self.end_cell_color = [255,0,0] # red cell for end location
		self.start_cell_color = [0,255,0] # green cell for start location
		self.current_location_color = [0,0,255] # blue for current location
		self.highway_color = [0,0,255] # blue for highway lines
		if self.using_game_character:
			# trying to allow user to select an image to use as the current location on the grid
			self.pic = character_image(os.getcwd()+"/resources/character.png",self)

		self.draw_grid_lines = True # set to true by default
		self.init_cells(leave_empty=True) # more instance variables that can be reset more easily from within instance

	def init_cells(self,leave_empty=False):
		# creates the list of cells in the grid (all default to free), if leave_empty
		# is False then we will fill in the grid following the instructions in the
		# assignment pdf 
		self.cells = []
		for x in range(self.num_columns):
			for y in range(self.num_rows):
				new_cell = cell(x,y)
				self.cells.append(new_cell)

		self.start_cell = (0,0) # default start cell
		self.end_cell = (self.num_columns-1,self.num_rows-1) # default end cell
		self.hard_to_traverse_regions = [] # empty by default
		self.highways = [] # empty by default
		self.current_location = self.start_cell				
		if leave_empty: return 

		print("Generating a random grid...")
		self.init_partially_blocked_cells() # init the partially blocked
		self.init_highways() # initialize the 4 highways
		self.init_blocked_cells() # initialize the completely blocked cells
		self.init_start_end_cells() # initialize the start/end locations
		print("Finished generating random grid.")

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

	def check_for_boundary(self,x,y):
		# checks to see if the coordinates are along one of the grid boundaries
		if x>=self.num_columns or x<0:
			return True
		if y>=self.num_rows or y<0:
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
				self.set_cell_state(x_coord,y_coord,"full",False)
				cur_blocked_cells+=1

	def get_cell_distance(self,cell1,cell2):
		# calculates the distance between the two cell inputs
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
			if self.get_cell_distance(temp_start,temp_end) >= 100:
				self.start_cell = temp_start
				self.end_cell = temp_end
				self.current_location = self.start_cell
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

		row_ct = 0
		index = 0
		line_buf = ""
		for cell in self.cells:
			row_ct += 1			

			cur_x = index % self.num_columns
			cur_y = int(index/self.num_columns)

			if cell.state == "full":
				line_buf+='0'
			if cell.state == "free":
				line_buf+='1' if self.check_for_highway(cur_x,cur_y)==False else 'a'
			if cell.state == "partial":
				line_buf+='2' if self.check_for_highway(cur_x,cur_y)==False else 'b'

			if row_ct == self.num_columns:
				line_buf+="\n"
				f.write(line_buf)
				line_buf = ""
				row_ct = 0
			index+=1

	def is_finished_highway(self,highway):
		# checks if both of the endpoints of the highway
		# are at the boundary of the grid
		if highway==None:
			return False
		start_cell = highway[0]
		end_cell = highway[len(highway)-1]

		if len(highway)<100:
			return False

		if self.check_for_boundary(start_cell[0],start_cell[1]) and self.check_for_boundary(end_cell[0],end_cell[1]):
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
			dist = self.get_cell_distance(item,last)
			if dist>1:
				broken.append(coordinate_list[last_cut:coordinate_list.index(item)])
				last_cut = coordinate_list.index(item)
			last = item
		print(len(broken))

		# now we have the broken list with partially reconstructed highway
		# segments but they are most likely not complete, iterate over the 
		# stuff in the broken list and connect any highway endpoints that
		# are only a distance of 1 away from eachother
		i = 0
		while True:
			segment = broken[i]
			segment_start = segment[0]
			segment_end = segment[len(segment)-1]

			new_broken = []
			for other_item in broken:
				if broken.index(other_item)!=i:
					other_segment_start = other_item[0]
					other_segment_end = other_item[len(other_item)-1]

					segment_start = segment[0]
					segment_end = segment[len(segment)-1]

					if self.get_cell_distance(segment_start,other_segment_start)==1:
						segment.reverse()
						segment.extend(other_item)
					elif self.get_cell_distance(segment_start,other_segment_end)==1:
						segment = other_item.extend(segment)
					elif self.get_cell_distance(segment_end,other_segment_start)==1:
						segment.extend(other_item)
					elif self.get_cell_distance(segment_end,other_segment_end)==1:
						other_item.reverse()
						segment.extend(other_item)
					else:	
						new_broken.append(other_item)
			new_broken.append(segment)
			broken = new_broken

			if len(broken)==4:
				self.highways = broken
				return

			#i+=1
			if i>len(broken):
				break

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
					new_cell = cell()
					new_cell.state = cell_state
					new_cells.append(new_cell)
					x+=1
				y+=1

		self.cells 		= new_cells
		self.start_cell = eval(start_cell)
		self.end_cell 	= eval(end_cell)
		self.current_location = self.start_cell
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
		print("Re-Drawing Grid...",end="\r")
		start_time = time.time() # to time the draw event
		size = self.size() # current size of widget
		width = size.width() # current width of widget
		height = size.height() # current height of widget

		horizontal_step = int(round(width/self.num_columns)) # per cell width
		vertical_step = int(round(height/self.num_rows)) # per cell height

		last_color = None # save the color used for the last cell in case its the same for this one

		index = 0
		for cell in self.cells:
			# iterate over each cell and fill in the grid color, also we need
			# to check several conditions such as whether the cell represents one
			# of the states (free, blocked, partially blocked, highway, start point,
			# end point, current location).

			# calculate the cell coordinates from list index
			x = index % self.num_columns # x coordinate
			y = int(index/self.num_columns) # get the y coordinate

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

			# check if the current cell is the current location
			if x==self.current_location[0] and y==self.current_location[1]:
				if self.using_game_character:
					# represent the current location with an image
					self.pic.move(x,y)
					self.pic.show()
				else:
					# represent the current location with a blue circle
					cell_color = self.current_location_color
					qp.setBrush(QColor(cell_color[0],cell_color[1],cell_color[2]))

					# calculating the center of the cell...
					x_center = x_start+(horizontal_step/2)
					y_center = y_start+(vertical_step/2)
					center = QPoint(x_center,y_center)
					radius_x = horizontal_step/4
					radius_y = vertical_step/4 
					qp.drawEllipse(center,radius_x,radius_y) # draw the blue circle

			index += 1
			last_color = cell_color

		# Drawing in grid lines...
		pen = QPen(QColor(self.line_color[0],self.line_color[1],self.line_color[2]), 1, Qt.SolidLine)
		qp.setPen(pen)
		qp.setBrush(Qt.NoBrush)

		# allow user to decide if grid lines should be rendered
		if self.draw_grid_lines:
		
			for x in range(self.num_columns):
				qp.drawLine(x*horizontal_step,0,x*horizontal_step,height)

			for y in range(self.num_rows):
				qp.drawLine(0,y*vertical_step,width,y*vertical_step)
		
		# Drawing in outer boundaries
		qp.drawLine(0,0,0,height-1)
		qp.drawLine(0,0,width-1,0)
		qp.drawLine(0,height-1,width-1,height-1)
		qp.drawLine(width-1,0,width-1,height-1)

		# Drawing in highway lines
		pen = QPen(QColor(self.highway_color[0],self.highway_color[1],self.highway_color[2]),2.0,Qt.SolidLine)
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
				y1 = (last_location[1]*horizontal_step)+(vertical_step/2)
				y2 = (location[1]*horizontal_step)+(vertical_step/2)
				qp.drawLine(x1,y1,x2,y2)
				last_location = location

		print("                                                     ",end="\r")
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
			cur_x = index % self.num_columns
			cur_y = int(index/self.num_columns)

			if cur_x==x and cur_y==y:
				#print("Changing cell to "+state)
				self.cells[index].state = state 
				break
			index += 1

	def get_cell_state(self,x_coord,y_coord):
		# locates the cell in question and returns the state
		index = 0
		for cell in self.cells:
			cur_x = index % self.num_columns
			cur_y = int(index/self.num_columns)
			if cur_x==x and cur_y==y:
				#print("Changing cell to "+state)
				return self.cells[index].state
				self.cells[index].state = state 
				break
			index += 1

	def toggle_grid_lines(self,grid_lines):
		self.draw_grid_lines = grid_lines 

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
		elif attrib == "current_location":
			self.current_location_color = color 
		else:
			print("Unknown attribute: "+attrib)

class attrib_color_window(QWidget):
	# small window that opens if the user wants to change an attribute color
	def __init__(self):
		# constructor
		super(attrib_color_window,self).__init__()
		self.init_vars()
		self.init_ui()	

	def init_vars(self):
		# initialize to default settings
		self.attribs = ["free","highway","fully blocked","partially blocked","start","end","current location"]
		# default colors
		self.colors = [[255,255,255],[0,0,255],[0,0,0],[128,128,128],[0,255,0],[255,0,0],[0,0,255]]
		# default element being shown
		self.attrib_index = 0
		# current attribute value
		self.attrib_value = self.colors[self.attrib_index]
		self.backend = False

	def init_ui(self):
		# set up ui elements

		self.layout = QVBoxLayout(self)

		first_row = QHBoxLayout()
		second_row = QHBoxLayout()

		self.layout.addLayout(first_row)
		self.layout.addLayout(second_row)

		self.setWindowTitle("Set Color Preferences")
		# selection box
		self.selection_box = QComboBox(self)
		self.selection_box.addItems(self.attribs)
		self.selection_box.currentIndexChanged.connect(self.attrib_changed)
		first_row.addStretch()
		selection_box_layout = QVBoxLayout()
		first_row.addLayout(selection_box_layout)
		selection_box_layout.addSpacing(5)
		selection_box_layout.addWidget(self.selection_box)

		# color elements
		self.red = QLineEdit("",self)
		self.red.textChanged.connect(self.value_changed)
		validator = QIntValidator(0,255)
		self.red.setValidator(validator)
		self.red.setFixedWidth(30)
		self.red_label = QLabel("   R",self)
		red_layout = QVBoxLayout()
		red_layout.addWidget(self.red_label)
		red_layout.addWidget(self.red)
		self.green = QLineEdit("",self)
		self.green.textChanged.connect(self.value_changed)
		validator = QIntValidator(0,255)
		self.green.setValidator(validator)		
		self.green.setFixedWidth(30)
		self.green_label = QLabel("   G",self)
		green_layout = QVBoxLayout()
		green_layout.addWidget(self.green_label)
		green_layout.addWidget(self.green)
		self.blue = QLineEdit("",self)
		self.blue.textChanged.connect(self.value_changed)
		validator = QIntValidator(0,255)
		self.blue.setValidator(validator)
		self.blue.setFixedWidth(30)
		self.blue_label = QLabel("   B",self)
		blue_layout = QVBoxLayout()
		blue_layout.addWidget(self.blue_label)
		blue_layout.addWidget(self.blue)
		
		first_row.addSpacing(10)
		first_row.addLayout(red_layout)
		first_row.addLayout(green_layout)
		first_row.addLayout(blue_layout)
		first_row.addSpacing(37)
		first_row.addStretch(1)

		# save prefs and return button
		self.return_button = QPushButton("Save",self)
		self.return_button.clicked.connect(self.save)

		second_row.addStretch()
		second_row.addWidget(self.return_button)
		second_row.addStretch()

		self.set_color_boxes(self.colors[0])

		if os.name == "nt": # these dimensions fit Windows better
			self.sample_square_top_left = (240,25) # (x,y) coordinates of top left
			self.sample_square_bottom_right = (267,52) # (x,y) coordinates of bottom right
			self.sample_square_size = 27 # width and height of sample square
		else: # and these are better for osx
			self.sample_square_top_left = (315,35)
			self.sample_square_bottom_right = (342,62)
			self.sample_square_size = 27

	def mousePressEvent(self,e):
		# catch when the user clicks and see if its in the sample area, if so, 
		# open up the default PyQt color picker
		x = e.x() # get x coordinate of click
		y = e.y() # get y coordinate of click

		if x <=self.sample_square_bottom_right[0] and x>= self.sample_square_top_left[0]:
			if y>= self.sample_square_top_left[1] and y<= self.sample_square_bottom_right[1]:
				# click was within the sample area
				color = QColorDialog.getColor() # open QColor dialog
				if color.isValid(): # if a value was returned
					color = color.getRgb() # conver to rgb
					color = list(color) # convert 3 length tuple to list
					self.set_color_boxes(color) # set the color 
					self.value_changed() # record the change

	def draw_sample_event(self,qp,color):
		# function called when the sample color window needs to be redrawn, colors
		# in the square with the current color
		qp.setPen(QColor(0,0,0))
		qp.setBrush(QColor(color[0],color[1],color[2])) 
		qp.drawRect( # draw the square
			self.sample_square_top_left[0],
			self.sample_square_top_left[1],
			self.sample_square_size,
			self.sample_square_size)

	def paintEvent(self,e):
		# calls the draw_sample_event function to re-color the sample square
		cur_color = self.get_current_color()
		qp = QPainter()
		qp.begin(self)
		self.draw_sample_event(qp,cur_color)
		qp.end()

	def save(self):
		# fetches the current colors and sends a signal back to the main_window
		self.emit(SIGNAL("return_color_prefs()"))
		self.hide()

	def attrib_changed(self):
		# function called by pyqt when user changes the selection box attribute
		self.set_color_boxes(self.colors[self.selection_box.currentIndex()])

	def set_color_boxes(self,color):
		# sets the rgb boxes to the input color
		self.backend = True
		try:
			self.red.setText(str(color[0]))
			self.green.setText(str(color[1]))
			self.blue.setText(str(color[2]))
			self.attrib_value = color
		except:
			pass
		self.backend = False

	def get_current_color(self):
		# parse the current color from the ui boxes
		current = []
		try:
			current.append(int(self.red.text()))
			current.append(int(self.green.text()))
			current.append(int(self.blue.text()))
			return current
		except:
			return [-1,-1,-1]

	def value_changed(self):
		# called by pyqt when one of the rgb boxes is changed
		if self.backend==False: 
			color = self.get_current_color()
			if color!=[-1,-1,-1]:
				self.colors[self.selection_box.currentIndex()] = color 
		self.repaint()

	def open_window(self):
		# called from the main_window
		self.show()

	def hide_window(self):
		# called from the main_window
		self.hide()

class main_window(QWidget):

	def __init__(self):
		# constructor
		super(main_window,self).__init__()
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		# initialize all class variables here
		self.grids = [] # list of all grid elements
		self.click = None # save click info
		self.host_os = os.name 
		self.show_grid_lines = True # true by default
		self.color_preferences_window = attrib_color_window()

	def init_ui(self):
		# initialize ui elements here
		self.layout = QVBoxLayout(self) # layout for window
		self.setWindowTitle("AI Project 1")

		# if windows, need to make room for menubar, on OSX the menubar
		# is kept in the top OS menu bar instead
		if os.name == "nt":
			self.layout.addSpacing(25)

		self.grid = eight_neighbor_grid() 
		self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
		self.grid.customContextMenuRequested.connect(self.on_context_menu_request)
		self.layout.addWidget(self.grid)

		# context menu stuff, opens on right click
		self.context_menu = QMenu(self)
		context_set_start_action = self.context_menu.addAction("Set as Starting Point",self.set_start)
		context_set_end_action = self.context_menu.addAction("Set as Ending Point",self.set_end)
		self.context_menu.addSeparator()
		context_menu_free_action = self.context_menu.addAction("Set Cell as Free",self.set_free)
		context_menu_partial_action = self.context_menu.addAction("Set Cell as Partially Blocked",self.set_partial)
		context_menu_full_action = self.context_menu.addAction("Set Cell as Fully Blocked",self.set_full)

		# menubar
		self.menu_bar = QMenuBar(self)
		self.menu_bar.setMinimumWidth(170)
		self.file_menu = self.menu_bar.addMenu("File")
		self.algo_menu = self.menu_bar.addMenu("Algorithm")
		self.tools_menu = self.menu_bar.addMenu("Tools")

		# menubar actions
		load_action = self.file_menu.addAction("Load...",self.load,QKeySequence("Ctrl+L"))
		save_action = self.file_menu.addAction("Save As...",self.save_as,QKeySequence("Ctrl+S"))
		self.file_menu.addSeparator()
		clear_action = self.file_menu.addAction("Clear Grid",self.clear,QKeySequence("Ctrl+C"))
		create_action = self.file_menu.addAction("Create New Grid",self.create,QKeySequence("Ctrl+N"))
		self.file_menu.addSeparator()
		quit_action = self.file_menu.addAction("Quit", self.quit, QKeySequence("Ctrl+Q"))
		a_star_action = self.algo_menu.addAction("Run A*",self.a_star)
		weighted_a_action = self.algo_menu.addAction("Run Weighted A",self.weighted_a)
		uniform_cost_action = self.algo_menu.addAction("Run Uniform-cost Search",self.uniform_cost)
		self.toggle_grid_lines_action = self.tools_menu.addAction("Turn Off Grid Lines",self.toggle_grid_lines,QKeySequence("Ctrl+G"))
		self.tools_menu.addSeparator()
		change_attrib_color_action = self.tools_menu.addAction("Set Attribute Color...",self.change_attrib_color,QKeySequence("Ctrl+M"))
		self.tools_menu.addSeparator()
		regenerate_start_end_action = self.tools_menu.addAction("New Start/End Cells...",self.regenerate_start_end)

		if os.name == "nt":
			self.resize(1623,1249) # large monitor size
		else:
			self.resize(1323,764) # fits my macbook well

		QtCore.QObject.connect(self.color_preferences_window, QtCore.SIGNAL("return_color_prefs()"), self.finished_changing_colors)
		self.show()

	def regenerate_start_end(self):
		# called when the user selects the "New Start/End Cells..." menu item in tools menu
		self.grid.init_start_end_cells()
		self.grid.repaint()

	def finished_changing_colors(self):
		# called by the color preferences window when the user is done
		self.color_preferences_window.hide_window()
		new_color_prefs = self.color_preferences_window.colors 
		new_color_attribs = self.color_preferences_window.attribs 
		for attrib,color in list(zip(new_color_attribs,new_color_prefs)):
			if attrib == "fully blocked":
				attrib = "full"
			if attrib == "partially blocked":
				attrib = "partial"
			if attrib == "current location":
				attrib = "current_location"
			self.grid.set_attrib_color(attrib,color)
		self.grid.repaint()

	def change_attrib_color(self):
		# function called by pyqt when user chooses change_attrib_color_action menu item
		self.color_preferences_window.open_window()

	def toggle_grid_lines(self):
		# function called by pyqt when user chooses the appropriate menu item
		if self.show_grid_lines == True:
			self.show_grid_lines = False
			self.toggle_grid_lines_action.setText("Turn On Grid Lines")
		else:
			self.show_grid_lines = True
			self.toggle_grid_lines_action.setText("Turn Off Grid Lines")

		self.grid.toggle_grid_lines(grid_lines=self.show_grid_lines)
		self.grid.repaint()

	def a_star(self):
		# put a* implementation here
		pass

	def weighted_a(self):
		# put weighted a implementation here
		pass

	def uniform_cost(self):
		# put uniform cost search implementation here
		pass

	def create(self):
		# clears the current grid and creates a new random one
		self.grid.random()
		self.grid.repaint()

	def clear(self):
		# clears the current grid
		self.grid.clear()
		self.grid.repaint()

	def save_as(self):
		# allow user to save the current grid
		filename = QFileDialog.getSaveFileName(self,"Save As")
		if filename != "":
			self.grid.save(filename)
		print("Finished saving "+filename)

	def load(self):
		# load a new grid from file
		filename = QFileDialog.getOpenFileName(self, "Select File")
		if filename != "":
			print("Loading grid...")
			self.grid.load(filename)
		self.grid.repaint()
		print("Finished loading "+filename)

	def quit(self):
		# quits the application
		self.close()

	def on_context_menu_request(self,point):
		# function called when user right clicks on grid
		self.click = point
		self.context_menu.exec_(self.grid.mapToGlobal(point))
		self.grid.repaint()

	def set_start(self):
		# called when user chooses item in right click menu
		self.grid.set_cell_state(self.click.x(),self.click.y(),"start")

	def set_end(self):
		# called when user chooses item in right click menu
		self.grid.set_cell_state(self.click.x(),self.click.y(),"end")

	def set_free(self):
		# called when user chooses item in right click menu
		self.grid.set_cell_state(self.click.x(),self.click.y(),"free")

	def set_partial(self):
		# called when user chooses item in right click menu
		self.grid.set_cell_state(self.click.x(),self.click.y(),"partial")

	def set_full(self):
		# called when user chooses item in right click menu
		self.grid.set_cell_state(self.click.x(),self.click.y(),"full")

	def resizeEvent(self,e):
		# called when user resizes the window
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")
		return # skip printing information
		print(self.size().width(),self.size().height())

	def mousePressEvent(self,e):
		# called when user clicks somewhere in window
		x = e.x()
		y = e.y()
		#print(x,y)

	def closeEvent(self,e):
		self.color_preferences_window.close()

def main():
	pyqt_app = QtGui.QApplication(sys.argv)
	_ = main_window()
	sys.exit(pyqt_app.exec_())	


if __name__ == '__main__':
	main()