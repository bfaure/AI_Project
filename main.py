# python 2.7
from __future__ import print_function
import os
import sys
# Python 2.7
import time
import random

import shutil # for copying helpers.py to helpers.pyx
import filecmp

from math import sqrt

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import heapq # for priority queue implementation

# set to true to disable Cython, if you don't have a Cython
# installation that doesnt mean you need to change this, should
# be used only for debugging and testing purposes.
TURN_OFF_CYTHON = False
USE_UCS_MULTITHREADED = False

try:
	import Cython # test to see if Cython is installed
	using_cython = True # need to compile helpers.pyx and import it
except:
	using_cython = False # need to import lib/helpers.py to take the place of helpers.pyx

if TURN_OFF_CYTHON: using_cython = False

if using_cython:
	print("Found Cython installation, copying helpers.py to helpers.pyx...")

	if os.path.exists("helpers.pyx"):
		if filecmp.cmp("lib/helpers.py","helpers.pyx")==False: # if they are not the same already
			shutil.copyfile("lib/helpers.py","helpers.pyx")
	else:
		shutil.copyfile("lib/helpers.py","helpers.pyx")

	print("Building C code (if error here change python2 to python in main.py)...")
	try:
		os.system("python2 setup.py build_ext --inplace")
		#if ret != 0:
		#	os.system("python setup.py build_ext --inplace")
	except:
		print("here")
		os.system("python setup.py build_ext --inplace")

	from helpers import PriorityQueue,get_neighbors,cell_in_list,cell_in_highway,uniform_cost_search,message
	from helpers import get_transition_cost,rectify_path,eight_neighbor_grid, get_cell_index
else:
	print("Could not find Cython installation, using Python version of helpers.py")
	lib_folder = "lib/"
	sys.path.insert(0, lib_folder)
	from helpers import PriorityQueue,get_neighbors,cell_in_list,cell_in_highway,uniform_cost_search,message
	from helpers import get_transition_cost,rectify_path,eight_neighbor_grid, get_cell_index

pyqt_app = ""

class attrib_value_window(QWidget):
	# small window that opens if the user wants to change an attribute value
	def __init__(self):
		# constructor
		super(attrib_value_window,self).__init__()
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		# initialize to default settings
		self.attribs = ["Solution Swarm Density","Solution Path Width","Solution Trace Width","Highway Width"]
		# default widths
		self.values = [1.0,5.0,1.0,2.0]

		self.lines = ["Highway","Solution Path","Solution Trace","Solution Swarm"]
		self.current_line_types = ["SolidLine","SolidLine","DotLine","DashLine"]
		self.all_line_types = ["SolidLine","DashLine","DotLine","DashDotLine","DashDotDotLine"]

	def init_ui(self):
		# set up ui elements
		self.layout = QVBoxLayout(self)

		first_row = QHBoxLayout()
		second_row = QHBoxLayout()
		save_row = QHBoxLayout()

		self.layout.addLayout(first_row)
		self.layout.addLayout(second_row)
		self.layout.addLayout(save_row)

		self.setWindowTitle("Set Value Preferences")
		# selection box
		self.selection_box = QComboBox(self)
		self.selection_box.addItems(self.attribs)
		self.selection_box.currentIndexChanged.connect(self.attrib_changed)
		first_row.addStretch()
		selection_box_layout = QVBoxLayout()
		first_row.addLayout(selection_box_layout)
		#selection_box_layout.addSpacing(5)
		selection_box_layout.addWidget(self.selection_box)

		# color elements
		self.value_input = QDoubleSpinBox(self)
		self.value_input.setDecimals(2)
		self.value_input.setSingleStep(0.1)
		self.value_input.setMaximum(10.0)
		self.value_input.setMinimum(0.1)
		self.value_input.valueChanged.connect(self.value_changed)

		first_row.addSpacing(10)
		first_row.addWidget(self.value_input)
		first_row.addSpacing(37)
		first_row.addStretch(1)

		# line selection box
		self.line_selection_box = QComboBox(self)
		self.line_selection_box.addItems(self.lines)
		self.line_selection_box.currentIndexChanged.connect(self.line_changed)
		second_row.addStretch()
		line_selection_layout = QVBoxLayout()
		second_row.addLayout(line_selection_layout)
		#line_selection_layout.addSpacing(5)
		line_selection_layout.addWidget(self.line_selection_box)

		self.line_type_input = QComboBox(self)
		self.line_type_input.addItems(self.all_line_types)
		self.line_type_input.currentIndexChanged.connect(self.line_type_changed)

		second_row.addSpacing(48)
		second_row.addWidget(self.line_type_input)
		second_row.addSpacing(37)
		second_row.addStretch(1)

		# save prefs and return button
		self.return_button = QPushButton("Save",self)
		self.return_button.clicked.connect(self.save)

		save_row.addStretch()
		save_row.addWidget(self.return_button)
		save_row.addStretch()

	def line_changed(self):
		# called when the user changes the current line in the second row
		self.line_type_input.setCurrentIndex(self.line_selection_box.currentIndex())

	def line_type_changed(self):
		# called when the user changes the current line type
		self.current_line_types[self.line_selection_box.currentIndex()] = str(self.line_type_input.currentText())

	def save(self):
		# fetches the current colors and sends a signal back to the main_window
		self.emit(SIGNAL("return_value_prefs()"))
		self.hide()

	def attrib_changed(self):
		# function called by pyqt when user changes the selection box attribute
		self.value_input.setValue(self.values[self.selection_box.currentIndex()])

	def value_changed(self):
		# called by pyqt when one of the rgb boxes is changed
		self.values[self.selection_box.currentIndex()] = self.value_input.value()

	def open_window(self):
		# called from the main_window
		self.show()

	def hide_window(self):
		# called from the main_window
		self.hide()

class attrib_color_window(QWidget):
	# small window that opens if the user wants to change an attribute color
	def __init__(self):
		# constructor
		super(attrib_color_window,self).__init__()
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		# initialize to default settings
		self.attribs = ["free","highway","fully blocked","partially blocked","start","end","solution_swarm","solution","start_gradient","end_gradient","path_trace"]
		# default colors
		self.colors = [[255,255,255],[0,0,255],[0,0,0],[128,128,128],[0,255,0],[255,0,0],[0,255,255],[0,255,0],[255,0,0],[0,255,50],[128,128,128]]
		# default element being shown
		self.attrib_index = 0
		# current attribute value
		self.attrib_value = self.colors[self.attrib_index]
		self.backend = False # if we are changing something backend, dont record it as user changed value

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
		self.host_os = os.name # "nt" for windows distrubitions
		print("Running Host OS: "+str(self.host_os))
		self.show_grid_lines = False # true by default
		self.show_solution_swarm = True # true by default
		self.use_gradient = False # False by default
		self.show_trace = True # true by default
		self.updating_already = False

		self.child_windows = [] # to hold any extra windows opened by user
		self.color_preferences_window = attrib_color_window()
		self.value_preferences_window = attrib_value_window()

		self.ucs_agent = uniform_cost_search() # separate thread for ucs execution

	def init_ui(self):
		# initialize ui elements here
		self.layout = QVBoxLayout(self) # layout for window
		self.setWindowTitle("AI Project 1")

		# if windows, need to make room for menubar, on OSX the menubar
		# is kept in the top OS menu bar instead
		if os.name == "nt":
			self.layout.addSpacing(25)

		self.grid = eight_neighbor_grid(160,120,pyqt_app)
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
		clear_path_action = self.file_menu.addAction("Clear Search Path", self.clear_path,"Ctrl+P")
		create_action = self.file_menu.addAction("Create New Grid",self.create,QKeySequence("Ctrl+N"))
		self.file_menu.addSeparator()
		new_window_action = self.file_menu.addAction("Open New Window...",self.open_new_window,QKeySequence("Ctrl+Shift+N"))
		self.file_menu.addSeparator()
		quit_action = self.file_menu.addAction("Quit", self.quit, QKeySequence("Ctrl+Q"))
		a_star_action = self.algo_menu.addAction("Run A*",self.a_star,QKeySequence("Ctrl+1"))
		weighted_a_action = self.algo_menu.addAction("Run Weighted A",self.weighted_a,QKeySequence("Ctrl+2"))
		uniform_cost_action = self.algo_menu.addAction("Run Uniform-cost Search",self.uniform_cost,QKeySequence("Ctrl+3"))
		self.toggle_grid_lines_action = self.tools_menu.addAction("Turn On Grid Lines",self.toggle_grid_lines,QKeySequence("Ctrl+G"))
		self.toggle_solution_swarm_action = self.tools_menu.addAction("Turn Off Solution Swarm",self.toggle_solution_swarm,QKeySequence("Ctrl+T"))
		self.toggle_gradient_action = self.tools_menu.addAction("Turn Off Swarm Gradient",self.toggle_gradient)
		self.toggle_trace_action = self.tools_menu.addAction("Turn On Path Trace",self.toggle_trace)
		self.tools_menu.addSeparator()
		change_attrib_color_action = self.tools_menu.addAction("Set Attribute Color...",self.change_attrib_color,QKeySequence("Ctrl+M"))
		change_attrib_value_action = self.tools_menu.addAction("Set Attribute Value...",self.change_attrib_value,QKeySequence("Ctrl+V"))
		self.tools_menu.addSeparator()
		regenerate_start_end_action = self.tools_menu.addAction("New Start/End Cells...",self.regenerate_start_end)

		if os.name == "nt":
			self.resize(1623,1249) # large monitor size
		else:
			self.resize(1323,764) # fits my macbook well

		QtCore.QObject.connect(self.color_preferences_window, QtCore.SIGNAL("return_color_prefs()"), self.finished_changing_colors)
		QtCore.QObject.connect(self.value_preferences_window, QtCore.SIGNAL("return_value_prefs()"), self.finished_changing_values)
		self.show()

	def clear_path(self):
		# function called by pyqt when user selects "Clear Search Path" File menu item
		self.stop_executing = True # tell search algo to stop
		self.ucs_agent.stop_executing = True # if using multithreading, tell search ucs agent to stop
		pyqt_app.processEvents() # force process events in event queue
		time.sleep(0.1) # give time for execution thread to stop
		self.grid.clear_path() # clear the path attributes
		self.grid.repaint() # render the ui

	def change_attrib_value(self):
		# function called by pyqt when user chooses change_attrib_value_action menu item
		self.value_preferences_window.open_window()

	def finished_changing_values(self):
		# called by the value preferences window when the user is done
		self.value_preferences_window.hide_window()
		new_value_prefs = self.value_preferences_window.values
		new_value_attribs = self.value_preferences_window.attribs
		for attrib,value in list(zip(new_value_attribs,new_value_prefs)):
			self.grid.set_attrib_value(attrib,value)

		new_line_types = self.value_preferences_window.current_line_types
		line_names = self.value_preferences_window.lines
		for attrib,value in list(zip(line_names,new_line_types)):
			self.grid.set_line_type(attrib,value)

		self.grid.repaint()

	def open_new_window(self):
		# function called by pyqt when user chooses "Open New Window...", opens
		# a new instance of main_window and adds it to the self.child_list
		new_window = main_window()
		self.child_windows.append(new_window)

	def toggle_solution_swarm(self):
		# function called by pyqt when user chooses the appropriate menu item
		if self.show_solution_swarm == True:
			self.show_solution_swarm = False
			self.toggle_solution_swarm_action.setText("Turn On Solution Swarm")
		else:
			self.show_solution_swarm = True
			self.toggle_solution_swarm_action.setText("Turn Off Solution Swarm")

		self.grid.toggle_solution_swarm(show_swarm=self.show_solution_swarm)
		self.grid.repaint()
		pyqt_app.processEvents()

	def toggle_gradient(self):
		# function called by pyqt when user chooses the appropriate menu item
		if self.use_gradient == True:
			self.use_gradient = False
			self.toggle_gradient_action.setText("Turn On Swarm Gradient")
		else:
			self.use_gradient = True
			self.toggle_gradient_action.setText("Turn Off Swarm Gradient")

		self.grid.toggle_gradient(use_gradient=self.use_gradient)
		self.grid.repaint()
		pyqt_app.processEvents()

	def toggle_trace(self):
		# function called by pyqt when user chooses the appropriate menu item
		if self.show_trace == True:
			self.show_trace = False
			self.toggle_trace_action.setText("Turn On Swarm Gradient")
		else:
			self.show_trace = True
			self.toggle_trace_action.setText("Turn Off Swarm Gradient")

		self.grid.toggle_trace(use_trace=self.show_trace)
		self.grid.repaint()
		pyqt_app.processEvents()

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
		self.cells = self.grid.cells #current state of grid cells
		self.start_cell = self.grid.start_cell #current start cell

		for item in self.cells:
			if item.x==self.start_cell[0] and item.y==self.start_cell[1]:
				self.start_cell = item
				break

		self.end_cell = self.grid.end_cell # current end cell
		self.highways = self.grid.highways # current highways on grid
		cost_list = {}; #initialize set that contains the cost to visit coordinates

		self.frontier = PriorityQueue()
		self.explored = [] # empty set

		cost_root = self.grid.get_euclidean_distance(self.grid.start_cell, self.grid.end_cell);
		self.frontier.push(self.start_cell,cost_root,parent=None)

		rootIndex = get_cell_index(self.start_cell, self.cells)
		cost_list[rootIndex] = 0

		while (self.frontier.length() != 0):
			cur_node = self.frontier.pop()
			print("\n")
			self.explored.append(cur_node)

			#If we're at the goal
			if cur_node.x == self.end_cell[0] and cur_node.y == self.end_cell[1]:
				self.path_end = cur_node
				break

			#get all the neighbors of the current node
			neighbor_list = get_neighbors(cur_node,self.cells)

			current_node_index = get_cell_index(cur_node, self.cells)
			for neighbor in neighbor_list:
				transition_cost = get_transition_cost(cur_node,neighbor,self.highways)
				updated_cost = cost_list[current_node_index] + transition_cost
				neighborIndex = get_cell_index(neighbor, self.cells)
				if (neighborIndex not in cost_list or updated_cost < cost_list[neighborIndex]) and neighbor.state != "full":
					cost_list[neighborIndex] = updated_cost
					priority = updated_cost + self.grid.euclidean_heuristic(neighbor, self.grid.end_cell)
					self.frontier.push(neighbor, priority, parent=cur_node)

		self.grid.solution_path = self.explored
		self.grid.shortest_path = rectify_path(self.path_end)
		self.grid.update() # render grid with new solution path
		pyqt_app.processEvents()


	def weighted_a(self):
		# put weighted a implementation here
		pass

	def uniform_cost(self):
		print("\nPerforming uniform_cost search...")
		self.stop_executing = False # Ctrl+C calls clear which will set this to true
		self.grid.verbose = False # Don't output all the render details

		# indicate the refresh rate here
		refresh_rate = 0.1 # at least every this many seconds refresh
		cost_refresh_rate = 1 # refresh if the algo has increased the current fringe cost by this much
		explored_refresh_rate = 100 # refresh if the algo has increased the explorted count by this much

		self.overall_start = time.time()

		self.cells = self.grid.cells # current state of cells in grid
		self.start_cell = self.grid.start_cell  # current start cell

		for item in self.cells:
			if item.x==self.start_cell[0] and item.y==self.start_cell[1]:
				self.start_cell = item
				break

		self.end_cell = self.grid.end_cell # current end cell
		self.highways = self.grid.highways # current highways on grid

		if USE_UCS_MULTITHREADED:
			self.ucs_agent = uniform_cost_search()
			self.ucs_agent.load_grid_data(self.cells,self.start_cell,self.end_cell,self.highways)
			self.grid.connect_to_ucs_agent(self.ucs_agent)
			self.ucs_agent.app = pyqt_app
			self.ucs_agent.start() # start the thread
			return

		self.path_cost = 0 # overall path cost
		self.tried_paths = [] # to hold all paths shown to user

		self.frontier = PriorityQueue()
		self.frontier.push(self.start_cell,0,parent=None)
		self.path_end = self.start_cell
		self.path_length = 1

		self.explored = [] # empty set

		while True:
			done = self.uniform_cost_step(refresh_rate,cost_refresh_rate,explored_refresh_rate)
			self.grid.solution_path = self.explored
			self.grid.shortest_path = rectify_path(self.path_end)
			self.tried_paths.append(self.grid.shortest_path)
			self.grid.path_traces = self.tried_paths
			self.grid.update() # render grid with new solution path
			pyqt_app.processEvents()
			if done:
				break

		self.grid.verbose = True

	def uniform_cost_step(self,refresh_rate,cost_refresh_rate,explored_refresh_rate):
		# helper function for uniform_cost search, performs only refresh_rate seconds then returns
		start_time = time.time() # to log the amount of time taken
		last_path_cost = self.path_cost
		initial_explored = len(self.explored)

		while True:

			if self.stop_executing:
				return True

			print("explored: "+str(len(self.explored))+", frontier: "+str(self.frontier.length())+", time: "+str(time.time()-self.overall_start)[:4]+", cost: "+str(self.path_cost)[:5],end="\r")

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
				transition_cost = get_transition_cost(cur_node,neighbor,self.highways)

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

		print("\nFinished uniform cost search in "+str(time.time()-self.overall_start)[:5]+" seconds, final cost: "+str(self.path_cost)+"\n")
		return True

	def create(self):
		# clears the current grid and creates a new random one
		self.stop_executing = True # if performing ucs w/o multhithreading, tell it to stop
		self.ucs_agent.stop_executing = True # if using multithreading, tell usc_agent to stop executing
		pyqt_app.processEvents()
		self.grid.clear()
		self.grid.random()
		self.grid.repaint()

	def clear(self):
		# clears the current grid
		self.stop_executing = True
		self.ucs_agent.stop_executing = True
		pyqt_app.processEvents()
		self.grid.clear()
		self.grid.repaint()

	def save_as(self):
		# allow user to save the current grid
		current_location = os.getcwd()
		filename = QFileDialog.getSaveFileName(self,"Save As", current_location+"/grids", "Grid Files (*.grid)")
		if filename != "":
			self.grid.save(filename)
		print("Finished saving "+filename)

	def load(self):
		# load a new grid from file
		current_location = os.getcwd()
		filename = QFileDialog.getOpenFileName(self, "Select Grid File", current_location+"/grids", "Grid Files (*.grid)")
		if filename != "":
			print("Loading grid...")
			self.grid.load(filename)
			self.grid.repaint()
			print("Finished loading "+filename)
		else:
			print("Loading canceled.")

	def quit(self):
		# quits the application
		sys.exit()

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

		self.end_cell = [int(self.click.x()),int(self.click.y())]
		if USE_UCS_MULTITHREADED:
			self.ucs_agent.end_cell = self.end_cell

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
		sys.exit()

def main():
	global pyqt_app

	pyqt_app = QtGui.QApplication(sys.argv)
	_ = main_window()
	sys.exit(pyqt_app.exec_())


if __name__ == '__main__':
	main()
