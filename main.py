# python 2.7
from __future__ import print_function
import os
import sys
# Python 2.7
import time
import random
from copy import deepcopy

from os import listdir
from os.path import isfile,join

import shutil # for copying helpers.py to helpers.pyx
import filecmp # to check if helpers.py == helpers.pyx (if exists)

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

TURN_OFF_DIAGONAL_MULTIPLIER = True
TURN_OFF_HIGHWAY_HEURISTIC = True

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
	from helpers import get_transition_cost,rectify_path,eight_neighbor_grid, get_cell_index, get_path_cost
	from helpers import non_gui_eight_neighbor_grid, cell

else:
	print("Could not find Cython installation, using Python version of helpers.py")
	lib_folder = "lib/"
	sys.path.insert(0, lib_folder)
	from helpers import PriorityQueue,get_neighbors,cell_in_list,cell_in_highway,uniform_cost_search,message
	from helpers import get_transition_cost,rectify_path,eight_neighbor_grid, get_cell_index, get_path_cost
	from helpers import non_gui_eight_neighbor_grid, cell

pyqt_app = ""

#log = open("debug_log.txt","w")

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
		self.values = [1.00,5.00,1.00,2.00]

		if os.name == "nt": # better for windows
			self.values[0] = 2.0

		self.lines = ["Highway","Solution Path","Solution Trace","Solution Swarm"]
		self.current_line_types = ["SolidLine","SolidLine","DotLine","DashLine"]
		self.all_line_types = ["SolidLine","DashLine","DotLine","DashDotLine","DashDotDotLine"]

		self.is_valid = True # if false, user closed out of window

	def init_ui(self):
		# set up ui elements
		self.layout = QVBoxLayout(self)

		first_row = QHBoxLayout()
		second_row = QHBoxLayout()
		save_row = QHBoxLayout()

		row_divider = QFrame(self) # dividing line between save button an top row
		row_divider.setFrameShape(QFrame.HLine)

		divider = QHBoxLayout()
		divider.addSpacing(40)
		divider.addWidget(row_divider)
		divider.addSpacing(40)

		self.layout.addLayout(first_row)
		self.layout.addLayout(second_row)
		self.layout.addSpacing(10)
		self.layout.addLayout(divider) # add dividing line
		self.layout.addSpacing(10)
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
		self.value_input.setDecimals(1)
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

		self.value_input.setValue(self.values[0])
		self.selection_box.setCurrentIndex(0)

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
		self.is_valid = True
		self.show()

	def hide_window(self):
		# called from the main_window
		self.hide()

	def closeEvent(self,e):
		self.is_valid = False
		self.emit(SIGNAL("return_value_prefs()"))

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

		self.is_valid = True # if false, user closed out of window instead of accepting changes

	def init_ui(self):
		# set up ui elements
		self.layout = QVBoxLayout(self)

		first_row = QHBoxLayout()
		second_row = QHBoxLayout()

		row_divider = QFrame(self) # dividing line between save button an top row
		row_divider.setFrameShape(QFrame.HLine)

		divider = QHBoxLayout()
		divider.addSpacing(40)
		divider.addWidget(row_divider)
		divider.addSpacing(40)

		self.layout.addLayout(first_row) # add color selection line
		self.layout.addSpacing(10)
		self.layout.addLayout(divider) # add dividing line
		self.layout.addSpacing(10)
		self.layout.addLayout(second_row) # add save button row

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
		self.is_valid = True
		self.show()

	def hide_window(self):
		# called from the main_window
		self.hide()

	def closeEvent(self,e):
		self.is_valid = False
		self.emit(SIGNAL("return_color_prefs()"))

class main_window(QWidget):

	# Initializations...
	def __init__(self,parent=None):
		# constructor
		super(main_window,self).__init__()
		self.parent = parent
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
		self.stop_executing = False
		self.mouse_tracking = True
		self.trace_highlighting = False
		self.is_benchmark = False # true if benchmarking right now

		self.child_windows = [] # to hold any extra windows opened by user
		self.color_preferences_window = attrib_color_window()
		self.value_preferences_window = attrib_value_window()

		if USE_UCS_MULTITHREADED: self.ucs_agent = uniform_cost_search() # separate thread for ucs execution

	def init_ui(self):
		# initialize ui elements here
		self.layout = QVBoxLayout(self) # layout for window
		self.setWindowTitle("AI Project 1")

		# if windows, need to make room for menubar, on OSX the menubar
		# is kept in the top OS menu bar instead
		if os.name == "nt":
			self.layout.addSpacing(25)

		# creating UI elements to show current cell state
		top_row_layout = QHBoxLayout() # layout to hold top row
		self.layout.addLayout(top_row_layout) # add layout to overall layout
		title_label = QLabel("Cell Information",self)
		top_row_layout.addWidget(title_label)
		top_row_layout.addSpacing(40)

		coordinates_label = QLabel("Coordinate:",self)
		top_row_layout.addWidget(coordinates_label)
		self.coordinates_value = QLineEdit("(0,0)",self)
		self.coordinates_value.setEnabled(False)
		self.coordinates_value.setFixedWidth(100)
		top_row_layout.addWidget(self.coordinates_value)
		top_row_layout.addSpacing(20)

		state_label = QLabel("State:",self)
		top_row_layout.addWidget(state_label)
		self.state_value = QLineEdit("FREE",self)
		self.state_value.setEnabled(False)
		self.state_value.setFixedWidth(100)
		top_row_layout.addWidget(self.state_value)
		top_row_layout.addSpacing(20)

		f_label = QLabel("f:",self)
		top_row_layout.addWidget(f_label)
		self.f_value = QLineEdit("0",self)
		self.f_value.setEnabled(False)
		self.f_value.setFixedWidth(100)
		top_row_layout.addWidget(self.f_value)
		top_row_layout.addSpacing(20)

		g_label = QLabel("g:",self)
		top_row_layout.addWidget(g_label)
		self.g_value = QLineEdit("0",self)
		self.g_value.setEnabled(False)
		self.g_value.setFixedWidth(100)
		top_row_layout.addWidget(self.g_value)
		top_row_layout.addSpacing(20)

		h_label = QLabel("h:",self)
		top_row_layout.addWidget(h_label)
		self.h_value = QLineEdit("0",self)
		self.h_value.setEnabled(False)
		self.h_value.setFixedWidth(100)
		top_row_layout.addWidget(self.h_value)
		top_row_layout.addSpacing(20)
		top_row_layout.addStretch()

		self.grid = eight_neighbor_grid(160,120,pyqt_app)
		self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
		self.grid.customContextMenuRequested.connect(self.on_context_menu_request)
		self.layout.addWidget(self.grid,2)

		# context menu stuff, opens on right click
		self.context_menu = QMenu(self)
		self.context_menu.addAction("Set as Starting Point",self.set_start)
		self.context_menu.addAction("Set as Ending Point",self.set_end)
		self.context_menu.addSeparator()
		self.context_menu.addAction("Set Cell as Free",self.set_free)
		self.context_menu.addAction("Set Cell as Partially Blocked",self.set_partial)
		self.context_menu.addAction("Set Cell as Fully Blocked",self.set_full)

		# Creating menubar and menu items
		self.menu_bar = QMenuBar(self)
		self.menu_bar.setMinimumWidth(250)
		self.file_menu = self.menu_bar.addMenu("File")
		self.algo_menu = self.menu_bar.addMenu("Algorithm")
		self.tools_menu = self.menu_bar.addMenu("Tools")
		self.benchmark_menu = self.menu_bar.addMenu("Benchmark")

		# Benchmark menu actions
		astar_benchmark_action = self.benchmark_menu.addAction("Benchmark A* Search",self.a_star_benchmark)
		astar_benchmark_action.setEnabled(False)
		weighted_benchmark_action = self.benchmark_menu.addAction("Benchmark Weighted A* Search",self.weighted_a_star_benchmark_wrapper)
		weighted_benchmark_action.setEnabled(False)
		self.benchmark_menu.addAction("Benchmark Uniform-Cost Search",self.uniform_cost_benchmark)
		self.benchmark_menu.addSeparator()
		astar_weighted_benchmark_action = self.benchmark_menu.addAction("Benchmark A*, All Heuristics",self.astar_heuristic_wrapper)
		astar_weighted_benchmark_action.setEnabled(False)
		self.benchmark_menu.addAction("Benchmark A*, All Heuristics, Multiple Weights",self.astar_heuristic_weight_wrapper)
		self.benchmark_menu.addSeparator()
		self.benchmark_menu.addAction("Benchmark Sequential A*, Multiple Weights",self.sequential_astar_benchmark_wrapper)
		self.benchmark_menu.addAction("Benchmark Integrated A*, Multiple Weights",self.integrated_astar_benchmark_wrapper)
		self.benchmark_menu.addSeparator()
		self.benchmark_menu.addAction("Benchmark All",self.all_benchmark)

		# File menu actions
		self.file_menu.addAction("Load...",self.load,QKeySequence("Ctrl+L"))
		self.file_menu.addAction("Save As...",self.save_as,QKeySequence("Ctrl+S"))
		self.file_menu.addSeparator()
		self.file_menu.addAction("Save Screenshot...",self.save_screenshot,QKeySequence("Ctrl+Shift+S"))
		self.file_menu.addSeparator()
		self.file_menu.addAction("Clear Grid",self.clear,QKeySequence("Ctrl+C"))
		self.file_menu.addAction("Clear Search Path", self.clear_path,"Ctrl+P")
		self.file_menu.addAction("Generate New Grid",self.create,QKeySequence("Ctrl+N"))
		self.file_menu.addSeparator()
		self.file_menu.addAction("Open New Window...",self.open_new_window,QKeySequence("Ctrl+Shift+N"))
		self.file_menu.addSeparator()
		self.file_menu.addAction("Quit", self.quit, QKeySequence("Ctrl+Q"))

		# Tools menu actions
		self.toggle_grid_lines_action = self.tools_menu.addAction("Turn On Grid Lines",self.toggle_grid_lines,QKeySequence("Ctrl+G"))
		self.toggle_solution_swarm_action = self.tools_menu.addAction("Turn Off Solution Swarm",self.toggle_solution_swarm,QKeySequence("Ctrl+T"))
		self.toggle_gradient_action = self.tools_menu.addAction("Turn Off Swarm Gradient",self.toggle_gradient)
		self.tools_menu.addSeparator()
		self.toggle_trace_action = self.tools_menu.addAction("Turn On Path Trace",self.toggle_trace)
		self.toggle_trace_highlighting_action = self.tools_menu.addAction("Turn On Trace Highlighting",self.toggle_trace_highlighting)
		self.tools_menu.addSeparator()
		self.toggle_mouse_tracking_action = self.tools_menu.addAction("Turn Off Mouse Tracking",self.toggle_mouse_tracking)
		self.tools_menu.addSeparator()
		self.tools_menu.addAction("Color Preferences...",self.change_attrib_color,QKeySequence("Ctrl+M"))
		self.tools_menu.addAction("Value Preferences...",self.change_attrib_value,QKeySequence("Ctrl+V"))
		self.tools_menu.addSeparator()
		self.tools_menu.addAction("New Start/End Cells...",self.regenerate_start_end)

		# Algorithm menu actions
		self.algo_menu.addAction("Run A*",self.a_star,QKeySequence("Ctrl+1"))
		self.algo_menu.addAction("Run Weighted A*",self.weighted_astar_wrapper_default_heuristic,QKeySequence("Ctrl+2"))
		self.algo_menu.addAction("Run Uniform-Cost Search",self.uniform_cost,QKeySequence("Ctrl+3"))
		self.algo_menu.addSeparator()
		self.algo_menu.addAction("Run A*, Custom Heuristic",self.astar_wrapper)
		self.algo_menu.addAction("Run Weighted A*, Custom Heuristic",self.weighted_astar_wrapper)
		self.algo_menu.addSeparator()
		self.algo_menu.addAction("Run Sequential Heuristic A*",self.sequential_astar,QKeySequence("Ctrl+8"))
		self.algo_menu.addAction("Run Integrated Heuristic A*",self.integrated_astar,QKeySequence("Ctrl+9"))
		self.algo_menu.addSeparator()
		self.algo_menu.addAction("Run Sequential Heuristic A*, Custom Parameters",self.sequential_astar_wrapper)
		self.algo_menu.addAction("Run Integrated Heuristic A*, Custom Parameters",self.integrated_astar_wrapper)
		self.algo_menu.addSeparator()
		self.algo_menu.addAction("Stop Algorithm",self.stop_algorithm,QKeySequence("Ctrl+0"))

		if os.name == "nt":
			#self.resize(1623,1249) # large monitor size
			self.resize(1623,1278) # large monitor size
		else:
			self.resize(1323,793) # fits my macbook well

		QtCore.QObject.connect(self.color_preferences_window, QtCore.SIGNAL("return_color_prefs()"), self.finished_changing_colors)
		QtCore.QObject.connect(self.value_preferences_window, QtCore.SIGNAL("return_value_prefs()"), self.finished_changing_values)
		QtCore.QObject.connect(self.grid, QtCore.SIGNAL("return_current_cell_attributes(PyQt_PyObject)"), self.update_current_cell_info)
		self.show()

	# Algorithms...
	def sequential_astar_wrapper(self):
		self.w1_w2_input_dialog("sequential_astar")

	def integrated_astar_wrapper(self):
		self.w1_w2_input_dialog("integrated_astar")

	def w1_w2_input_dialog(self,target):
		inputw1, ok = QInputDialog.getText(self, "Input Dialog", "Enter W1 value (>=1.0): ")
		if ok:
			try:
				inputw1 = float(inputw1)
				if inputw1>=1.0:

					inputw2, ok = QInputDialog.getText(self, "Input Dialog",  "Enter W2 value (>=1.0): ")

					if ok:
						try:
							inputw2 = float(inputw2)

							if inputw2>=1.0:
								if target=="integrated_astar":
									self.integrated_astar(inputw1,inputw2)
								elif target=="sequential_astar":
									self.sequential_astar(inputw1,inputw2)
								else:
									print("ERROR: W1, W2 input dialog function.")
								#self.integrated_astar(w1,w2)

							else:
								print("ERROR: W2 input must be whole number greater than or equal to 1.0")

						except:
							print("ERROR: W2 input must be whole number greater than or equal to 1.0")

				else:
					print("ERROR: W1 input must be whole number greater than or equal to 1.0")

			except:
				print("ERROR: W1 input must be whole number greater than or equal to 1.0")

	def sequential_astar(self,w1=1.25,w2=1.25):
		global log 
		num_heuristics = 5
		if self.is_benchmark==False: print("Performing Sequential A* Search with "+str(num_heuristics)+" heuristics...")

		self.fetch_current_grid_state()
		self.set_ui_interaction(enabled=False)

		inf = sys.maxint

		#get start index
		start_index = get_cell_index(self.start_cell, self.cells)

		#get goal index
		goal_index = get_cell_index(self.end_cell_t, self.cells)

		#initialize 5 explored sets for each heuristics
		self.explored_set_list = [[] for i in range(num_heuristics)]

		#initialize 5 empty cost sets for each heuristics
		self.cost_set_list = [{} for i in range(num_heuristics)]

		#initialize closed lists
		self.closed_set_lists = [ [] for i in range(num_heuristics)]

		#initialize visited arrays for each heuristics
		self.visited_lists = [[False] * len(self.cells) for i in range(num_heuristics)]

		#Mark the start nodes as visited (NOTE: might need to fuse loops later)
		for i in range(num_heuristics):
			self.visited_lists[i][start_index] = True

		#populate the sets with values for start and end node_neigbors
		for i in range(num_heuristics):
			self.cost_set_list[i][start_index] = 0
			self.cost_set_list[i][goal_index] = inf

		#initialize 5 frontiers for each of the 5 heuristics
		self.frontier_list = []
		for i in range(num_heuristics):
			temp = PriorityQueue()
			temp.push(item=self.start_cell, cost=self.sequential_astar_key(i, w1, self.start_cell, start_index), parent=None)
			self.frontier_list.append(temp)

		done = False #boolean used to break out of while loop

		result_code = 0
		print("Finished initializing everything")

		last_cell = None # to hold the last node expanded (for updating ui)
		start_time = time.time()
		step_time = time.time()
		refresh_rate = 0.1 # refresh the display after this many seconds
		self.explored = [] # to hold all cells visited
		num_iterations = 0 # number of times while loop is run
		self.stop_executing = False
		last_heuristic = 0

		while self.frontier_list[0].Minkey() < inf and done==False:
			#log.write("\n----- While Loop Iteration #"+str(num_iterations)+"-----\n")

			#for i in range(num_heuristics):
			#	log.write("Length of Heuristic #"+str(i)+" explored = "+str(len(self.explored_set_list[i]))+"\n")
			#	log.write("Length of Heuristic #"+str(i)+" cost_set_list = "+str(len(self.cost_set_list[i]))+"\n")
			#	log.write("Length of Heuristic #"+str(i)+" closed_set_lists = "+str(len(self.closed_set_lists[i]))+"\n")
			#	log.write("Length of Heuristic #"+str(i)+" frontier = "+str(self.frontier_list[i].length())+"\n\n")

			if (self.stop_executing):
				self.set_ui_interaction(enabled=True)
				return

			# update the ui window
			if ((time.time()-step_time) > refresh_rate) and last_cell!=None:
				#log.write("Updating UI\n")
				self.grid.solution_path = self.explored
				self.grid.shortest_path = rectify_path(last_cell)
				self.grid.update()
				pyqt_app.processEvents()
				step_time = time.time()
			

			print("                                                                           ",end="\r")
			print("explored: "+str(len(self.explored_set_list[last_heuristic]))+", num_iterations: "+str(num_iterations)+", time: "+str(time.time()-start_time)[:5], end="\r")
			num_iterations += 1

			#log.write("explored: "+str(len(self.explored))+"\n")

			#print("Inside While loop")
			for i in range(1, num_heuristics):
				#log.write("\n\n---Inside For Loop, Iteration#"+str(i)+"---\n")
				#log.write("self.frontier_list[i].Minkey() == "+str(self.frontier_list[i].Minkey())+"\n")
				if self.frontier_list[i].Minkey() <= ( w2 * self.frontier_list[0].Minkey() ):
					if self.cost_set_list[i][goal_index] <= self.frontier_list[i].Minkey():
						#log.write("1A\n")
						if self.cost_set_list[i][goal_index] < inf:
							#log.write(" 1AA\n")
							done = True #exit out of the loop
							result_code = i
							break
					else:
						#log.write("1B\n")
						#print("Inside else for i")
						s = self.frontier_list[i].top()
						#log.write("Expanding: "+s.to_string()+"\n")

						last_cell = s
						last_heuristic = i
						if cell_in_list(s,self.explored)==False: self.explored.append(s)
						
						self.sequential_astar_expand(i, w1, s)
						self.explored_set_list[i].append(s)
						self.closed_set_lists[i].append(s)
				else:
					if self.cost_set_list[0][goal_index] <= self.frontier_list[0].Minkey():
						if self.cost_set_list[0][goal_index] < sys.maxint:
							#log.write("2A\n")
							done = True
							result_code = 0
							#print("About to exit")
							break
					else:
						#log.write("2B\n")
						#print("Inside else for i=0")
						s = self.frontier_list[0].top()

						#log.write("Expanding: "+s.to_string()+"\n")
						last_cell = s
						last_heuristic = 0
						if cell_in_list(s,self.explored)==False: self.explored.append(s)

						self.sequential_astar_expand(0, w1, s)
						self.explored_set_list[0].append(s)
						self.closed_set_lists[0].append(s)
		#log.write("\nDone\n")

		#render solution
		self.grid.solution_path = self.explored
		#self.grid.solution_path = self.explored_set_list[result_code]
		final_solution_cost = self.cost_set_list[result_code][goal_index]
		self.path_end = None
		for cell in self.frontier_list[result_code]._queue:
			cell = cell[1]
			if cell.x == self.end_cell[0] and cell.y == self.end_cell[1]:
				#if cell.cost == final_solution_cost:
				self.path_end = cell
				break

		print("\nFinished Sequential A* search in "+str(time.time()-start_time)[:6]+" seconds, final cost: "+str(final_solution_cost)+", checked "+str(len(self.explored_set_list[result_code]))+" cells\n")

		self.grid.shortest_path = rectify_path(self.path_end)
		self.grid.update()
		pyqt_app.processEvents()
		self.set_ui_interaction(enabled=True)

	def sequential_astar_key(self, h_index, w1, cell_obj, cell_index):
		#log.write("Inside sequential_astar_key, h_index="+str(h_index)+"\n")
		return self.cost_set_list[h_index][cell_index] + (w1 * float(self.grid.heuristic_manager(cell_obj, self.end_cell_t, h_index)) / 4.0)

	def sequential_astar_expand(self, h_index, w1, cell_obj):
		#log.write("Inside sequential_astar_expand h_index:"+str(h_index)+", cell_obj.x="+str(cell_obj.x)+", cell_obj.y="+str(cell_obj.y)+"...\n")
		#Remove s from frontier
		self.frontier_list[h_index].remove(cell_obj)
		#if removed==False:
		#	log.write("Could not remove cell from frontier_list\n")
		#get neighbors
		neighbors = get_neighbors(cell_obj, self.cells)

		c_index = get_cell_index(cell_obj, self.cells)
		self.visited_lists[h_index][c_index] = True

		for neighbor in neighbors:
			neighbor = deepcopy(neighbor)

			neighbor_index = get_cell_index(neighbor, self.cells)
			if neighbor_index==c_index:
				continue

			#log.write("Iterating over neighbors, neighbor_index="+neighbor.to_string()+"...\n")

			if self.visited_lists[h_index][neighbor_index] == False:
				#log.write("3A\n")
				self.cost_set_list[h_index][neighbor_index] = sys.maxint
				neighbor.parent = None

				if neighbor.state == "full":
					#log.write("3AA\n")
					continue

			if self.cost_set_list[h_index][neighbor_index] > (self.cost_set_list[h_index][c_index] + get_transition_cost(cell_obj, neighbor, self.highways)):
				#log.write("3B\n")
				self.cost_set_list[h_index][neighbor_index] = self.cost_set_list[h_index][c_index] + get_transition_cost(cell_obj, neighbor, self.highways)

				if cell_in_list(neighbor, self.closed_set_lists[h_index]) == False:
					#log.write("3BB\n")
					self.frontier_list[h_index].update_or_insert(neighbor, self.sequential_astar_key(h_index, w1, neighbor, neighbor_index),  parent=cell_obj)

			#log.write("Finished neighbor\n")

	def integrated_astar(self,w1=1.25,w2=1.25):
		# f = g + h
		# g = cost from current to start
		# h = heuristic, cost from current to goal

		# w1 >= 1.0 , to weight the heuristic ( return g(s) + w1*hi(s) )
		# w2 >= 1.0 , weights the comparison ( OPENi.Minkey() <= w2*OPEN0.Minkey() )

		# w1 --> used to inflate heuristic values for each of the search procedures
		# w2 --> used as a factor to prioritize the inadmissible search processes over the anchor, admissible one

		num_heuristics = 6
		if TURN_OFF_HIGHWAY_HEURISTIC: num_heuristics = 5

		if self.is_benchmark==False: print("Performing Integrated A* Search with "+str(num_heuristics)+" heuristics using w1="+str(w1)+", w2="+str(w2))

		self.set_ui_interaction(enabled=False) # turn off ui interaction
		self.stop_executing = False # prevent from quitting search

		self.fetch_current_grid_state() # set: self.cells, self.start_cell, self.end_cell, self.highways

		self.closed_anchor = [] # all cells closed by anchor heuristic
		self.closed_inad = [] # all cells closed by inadmissible heuristic

		inf = sys.maxint # pseudo infinity value

		self.g = {}
		s_start = get_cell_index(self.start_cell,self.cells) # get the index of the start_cell
		self.g[s_start] = 0

		s_goal = get_cell_index(self.end_cell_t,self.cells) # get the index of the end_cell
		self.g[s_goal] = inf

		self.expanded = [False] * len(self.cells)
		self.expanded[s_start] = True

		self.open_t = [] # list of CellQueue structs, open[0] is all open cells for anchor
		for i in range(num_heuristics):
			temp = PriorityQueue()
			temp.push(item=self.start_cell, cost=self.Key(self.start_cell,i,s_start,w1), parent=None)
			self.open_t.append(temp)

		done = False # if true, the while loop will be broken
		self.explored = []

		start_time = time.time()
		step_time = time.time()

		refresh_rate = 0.1
		last_cell = None


		heuristics_used = [0] * num_heuristics
		heuristic_queue_emptied = [0] * num_heuristics

		result_code = 0

		num_iterations = 0
		while self.open_t[0].Minkey() < inf and done==False:

			if (self.stop_executing):
				self.set_ui_interaction(enabled=True)
				return

			# update the ui window
			if (time.time()-step_time > refresh_rate) and last_cell!=None:
				self.grid.solution_path = self.explored
				self.grid.shortest_path = rectify_path(last_cell)
				self.grid.update()
				pyqt_app.processEvents()
				step_time = time.time()

			#print("---------------------\n")
			#f.write("\n-----------------------------------------------\n")
			print("                                                                           ",end="\r")
			print("explored: "+str(len(self.g))+", num_iterations: "+str(num_iterations)+", time: "+str(time.time()-start_time)[:5], end="\r")
			num_iterations += 1
			#print("g[s_goal]: "+str(self.g[s_goal])+", g[s_start]: "+str(self.g[s_start])+", explored: "+str(len(self.g)),end="\r")

			#f.write("\nopen_t[anchor]: ")
			#for elem in self.open_t[0]._queue:
			#	f.write("[ "+elem[2].to_string()+" ], ")
			#f.write("\n")

			for i in range(1,num_heuristics):
				#f.write("\nopen_t["+str(i)+"]: ")
				#for elem in self.open_t[i]._queue:
				#	f.write("[ "+elem[2].to_string()+" ], ")
				#f.write("\n")
				#print(self.open_t[i]._queue)
				if len(self.open_t[i]._queue)==0:
					heuristic_queue_emptied[i]+=1
					#print("WARNING: Heuristic at i="+str(i)+" has an empty PriorityQueue.")
					continue

				if self.open_t[i].Minkey() <= ( w2 * self.open_t[0].Minkey() ):
					heuristics_used[i]+=1

					if self.g[s_goal] <= self.open_t[i].Minkey():
						#f.write("\nhere 1a")
						#print("\nhere 1a")
						if self.g[s_goal] < inf:
							#print("\nFinished 1.")
							result_code = i
							done = True
							break
					else:
						#f.write("\nhere 1b")
						#print("\nhere 1b")
						s = self.open_t[i].top()
						last_cell = s
						self.explored.append(s)
						self.ExpandState(s,w1,w2)
						self.closed_inad.append(s)
				else:
					heuristics_used[0]+=1
					if self.g[s_goal] <= self.open_t[0].Minkey():
						#print("\nhere 2a")
						#f.write("\nhere 2a")
						if self.g[s_goal] < inf:
							#print("\nFinished 2.")
							result_code = 0
							done = True
							break
					else:
						#f.write("\nhere 2b")
						#print("\nhere 2b")
						s = self.open_t[0].top()
						last_cell = s
						self.explored.append(s)
						self.ExpandState(s,w1,w2)
						self.closed_anchor.append(s)

		#print("\n")
		#if self.is_benchmark==False: print("Heuristic Usage Counts: ",heuristics_used)
		#if self.is_benchmark==False: print("Heuristic Queue Emptied: ",heuristic_queue_emptied)

		self.last_cost_list = self.g
		final_solution_cost = self.g[s_goal]
		self.grid.solution_path = self.explored

		self.path_end = None

		for cell in self.open_t[result_code]._queue:
			#cell = cell[2]
			cell = cell[1]
			if cell.x==self.end_cell[0] and cell.y==self.end_cell[1]:
				if cell.cost == final_solution_cost:
					self.path_end = cell
					break

		self.grid.shortest_path = rectify_path(self.path_end)
		self.grid.update() # render grid with new solution path
		pyqt_app.processEvents()
		#final_solution_cost = get_path_cost(self.path_end,self.highways)
		print("\nFinished Integrated A* search in "+str(time.time()-start_time)[:6]+" seconds, final cost: "+str(final_solution_cost)+", checked "+str(len(self.explored))+" cells\n")

		if self.is_benchmark:
			self.latest_search_cost = final_solution_cost
			self.latest_num_explored = len(self.explored)
			self.latest_frontier_length = 0
			for queue in self.open_t:
				self.latest_frontier_length += queue.length()

		self.set_ui_interaction(enabled=True) # turn on ui interaction

	def ExpandState(self,s,w1,w2):
		#print("Inside expand state")
		#f.write("\ninside ExpandState")
		# remove s from all OPENi
		for i in range(len(self.open_t)):
			self.open_t[i].remove(s)

		s_index = get_cell_index(s,self.cells)
		successors = get_neighbors(s,self.cells)
		#print(successors)
		self.expanded[s_index] = True

		for succ in successors: # foreach s' in Succ(s)
			succ_index = get_cell_index(succ,self.cells)
			#f.write("\nsucc_index: "+str(succ_index))
			#print("\n")

			if self.expanded[succ_index]==False: # if s' was never generated
				#f.write("\n here 3a")
				#print("here 3a")
				#self.expanded[succ_index] = True
				self.g[succ_index] = sys.maxint # g(s') = infinity

				if succ.state == "full":
					continue

			if self.g[succ_index] > (self.g[s_index] + get_transition_cost(s,succ,self.highways)): # if g(s') > g(s)+c(s,s')
				self.g[succ_index] = self.g[s_index] + get_transition_cost(s,succ,self.highways) # g(s') = g(s) + c(s,s')

				#f.write("\n here 4a")
				#f.write("\n g[succ_index]: "+str(self.g[succ_index]))
				#print("here 4a")

				if cell_in_list(succ,self.closed_anchor)==False: # if s' not in CLOSEDanchor
					#print("here 5a")
					#f.write("\n  here 5a")
					anchor_cost = self.Key(succ,0,succ_index,w1)
					#f.write("\n  anchor_cost: "+str(anchor_cost))
					self.open_t[0].update_or_insert(succ,anchor_cost,parent=s)

					if cell_in_list(succ,self.closed_inad)==False:
						#print("here 6a")
						#f.write("\n   here 6a")
						for i in range(1, len(self.open_t)):
							#print("here 7a")
							#f.write("\n    here 7a")
							inad_cost = self.Key(succ,i,succ_index,w1)
							#f.write("\n    inad_cost: "+str(inad_cost))

							if inad_cost <= ( w2 * anchor_cost ):
								#print("here 7b")
								#f.write("\n     here 7b")
								self.open_t[i].update_or_insert(succ,inad_cost,parent=s)

	def Key(self,s,i,s_index,w1):
		return self.g[s_index] + w1*(float(self.grid.heuristic_manager(s,self.end_cell_t,i,True if TURN_OFF_DIAGONAL_MULTIPLIER==False else False))/4.0)

	def weighted_astar_wrapper_default_heuristic(self):
		self.grid.allow_render_mouse = False
		weight,ok = QInputDialog.getText(self, "Input Dialog", "Enter Weight: ")
		if ok:
			self.a_star(weight=weight)
		self.allow_render_mouse = True

	def weighted_astar_wrapper(self):
		self.grid.allow_render_mouse = False
		inputweight, ok = QInputDialog.getText(self, "Input Dialog", "Enter Weight: ")
		if ok:
			inputcode, ok2 = QInputDialog.getText(self, "Input Dialog", "Enter Heuristic Code (0 for Euclidean, 1 for Diagonal, 2 for Approx. Euclidean, 3 for Manhattan, 4 for approx): ")
			if ok2:
				inputcode = int(inputcode)
				if inputcode not in [0,1,2,3,4]:
					print("ERROR: Heuristic can be 0, 1, 2, 3 or 4 only.")
					return
				self.a_star(weight=inputweight, code=inputcode)
		self.grid.allow_render_mouse = True

	def astar_wrapper(self):
		self.grid.allow_render_mouse = False
		inputcode, ok = QInputDialog.getText(self, "Input Dialog", "Enter Heuristic Code (0 for Euclidean, 1 for Diagonal, 2 for Approx. Euclidean, 3 for Manhattan, 4 for approx): ")
		if ok:
			inputcode = int(inputcode)
			if inputcode not in [0,1,2,3,4]:
				print("ERROR: Heuristic can be 0, 1, 2, 3 or 4 only.")
				return
			self.a_star(weight=1, code=inputcode)
		self.allow_render_mouse = True

	def a_star(self, weight=1.0, code=0):
		if self.is_benchmark==False: print("Performing A* Seach with weight: "+str(weight)+", and heuristic: "+str(code)+"...")

		self.set_ui_interaction(False) # turn off ui interaction
		self.stop_executing = False
		self.fetch_current_grid_state() # set: self.cells, self.start_cell, self.end_cell, self.highways

		cost_list = {}; #initialize set that contains the cost to visit coordinates

		self.frontier = PriorityQueue()
		self.explored = [] # empty set
		visited = [False] * len(self.cells)

		cost_root = float(self.grid.heuristic_manager(self.start_cell, self.end_cell, code))
		self.frontier.push(self.start_cell,cost_root,parent=None)

		rootIndex = get_cell_index(self.start_cell, self.cells)
		cost_list[rootIndex] = 0
		visited[rootIndex] = rootIndex

		refresh_rate = 0.1 # update the ui window after this many seconds
		start_time = time.time() # used for updating the ui
		overall_start = time.time() # used for saving execution time

		while (self.frontier.length() != 0):

			if self.stop_executing:
				self.grid.render_mouse = True
				self.grid.allow_render_mouse = True
				return # return if user cancelled execution

			# printing current state information to terminal
			print("explored: "+str(len(self.explored))+", frontier: "+str(self.frontier.length())+", time: "+str(time.time()-overall_start)[:6],end="\r")

			cur_node = self.frontier.pop()
			self.explored.append(cur_node)

			# update the ui window
			if time.time()-start_time > refresh_rate:
				start_time = time.time()
				self.grid.solution_path = self.explored
				self.grid.shortest_path = rectify_path(cur_node)
				self.grid.update()
				pyqt_app.processEvents()

			#If we're at the goal
			if cur_node.x == self.end_cell[0] and cur_node.y == self.end_cell[1]:
				self.path_end = cur_node
				break

			#get all the neighbors of the current node
			neighbor_list = get_neighbors(cur_node,self.cells)
			#index_list = neighbor_index_list(neighbor_list, self.cells)
			#pruned_list = prune_neighbors(neighbor_list, visited, index_list)
			current_node_index = get_cell_index(cur_node, self.cells)
			visited[current_node_index] = True
			#self.frontier.clear()
			for neighbor in neighbor_list:
				transition_cost = get_transition_cost(cur_node,neighbor,self.highways)
				updated_cost = cost_list[current_node_index] + transition_cost
				neighborIndex = get_cell_index(neighbor, self.cells)

				if (neighborIndex not in cost_list or updated_cost < cost_list[neighborIndex]) and (neighbor.state != "full") and visited[neighborIndex] == False:
					cost_list[neighborIndex] = updated_cost
					priority = updated_cost + (float(weight) * float(self.grid.heuristic_manager(neighbor, self.end_cell, code))/4.0)
					self.frontier.push(neighbor, priority, parent=cur_node)

		self.last_cost_list = cost_list
		self.grid.solution_path = self.explored
		self.grid.shortest_path = rectify_path(self.path_end)
		self.grid.update() # render grid with new solution path
		pyqt_app.processEvents()
		final_solution_cost = get_path_cost(self.path_end,self.highways)
		print("\nFinished a* search in "+str(time.time()-overall_start)[:6]+" seconds, final cost: "+str(final_solution_cost)+", checked "+str(len(self.explored))+" cells\n")

		if self.is_benchmark:
			self.latest_search_cost = final_solution_cost
			self.latest_num_explored = len(self.explored)
			self.latest_frontier_length = self.frontier.length()

		self.set_ui_interaction(True) # turn on ui interaction

	def uniform_cost(self):
		if self.is_benchmark==False: print("\nPerforming uniform_cost search...")
		self.set_ui_interaction(False) # turn off ui interaction
		self.stop_executing = False # Ctrl+C calls clear which will set this to true

		# indicate the refresh rate here
		refresh_rate = 0.1 # at least every this many seconds refresh
		cost_refresh_rate = 1 # refresh if the algo has increased the current fringe cost by this much
		explored_refresh_rate = 100 # refresh if the algo has increased the explorted count by this much

		self.overall_start = time.time()
		self.fetch_current_grid_state() # set: self.cells, self.start_cell, self.end_cell, self.highways

		if USE_UCS_MULTITHREADED:
			self.ucs_agent = uniform_cost_search()
			self.ucs_agent.load_grid_data(self.cells,self.start_cell,self.end_cell,self.highways)
			self.grid.connect_to_ucs_agent(self.ucs_agent)
			self.ucs_agent.app = pyqt_app
			self.ucs_agent.start() # start the thread
			self.grid.render_mouse = True
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

		# used for benchmarking
		if self.is_benchmark:
			self.latest_search_cost = self.path_cost
			self.latest_num_explored = len(self.explored)
			self.latest_frontier_length = self.frontier.length()

		self.set_ui_interaction(True) # turn on ui interaction

	def uniform_cost_step(self,refresh_rate,cost_refresh_rate,explored_refresh_rate):
		# helper function for uniform_cost search, performs only refresh_rate seconds then returns
		start_time = time.time() # to log the amount of time taken
		last_path_cost = self.path_cost
		initial_explored = len(self.explored)

		while True:

			if self.stop_executing:
				return True

			print("explored: "+str(len(self.explored))+", frontier: "+str(self.frontier.length())+", time: "+str(time.time()-self.overall_start)[:6]+", cost: "+str(self.path_cost)[:5],end="\r")

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

		print("\nFinished uniform cost search in "+str(time.time()-self.overall_start)[:6]+" seconds, final cost: "+str(self.path_cost)+", checked "+str(len(self.explored))+" cells\n")
		return True

	# Benchmarks...
	def sequential_astar_benchmark_wrapper(self):
		# benchmark sequential A* with multiple weights
		print(">Benchmarking Sequential A* Search on several weights...")
		for w1 in [1.0,1.25,1.75,2.0]:
			for w2 in [1.0,1.25,1.75,2.0]:
				self.sequential_astar_benchmark(w1,w2)

	def integrated_astar_benchmark_wrapper(self):
		# benchmark integrated A* with mutiple weights
		# benchmark sequential A* with multiple weights
		print(">Benchmarking Integrated A* Search on several weights...")
		for w1 in [1.0,1.25,1.75,2.0]:
			for w2 in [1.0,1.25,1.75,2.0]:
				self.integrated_astar_benchmark(w1,w2)

	def sequential_astar_benchmark(self,w1,w2):
		pass

	def integrated_astar_benchmark(self,w1,w2):
		# benchmark the efficiency of the A* algorithm on all files in /grids
		self.is_benchmark = True
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - BENCHMARKING")

		data_dir = "benchmarks/data/"
		filename = data_dir+"integrated_a_star-[w1="+str(w1).replace(".","_")+"]-[w2="+str(w2).replace(".","_")+"].txt"
		f = open(filename,"w")
		print(">Writing results to "+filename+"...")

		grids,short = self.get_all_grids()
		f.write("Integrated A* Benchmark on "+str(len(grids))+" .grid files [w1="+str(w1)+"], [w2="+str(w2)+"]:\n\n")
		print(">Integrated A* Benchmark on "+str(len(grids))+" .grid files [w1="+str(w1)+"], [w2="+str(w2)+"]...")

		# turning off all UI interaction
		self.grid.allow_render_mouse = False
		self.grid.suppress_output = True
		self.grid.verbose = False
		self.grid.draw_grid_lines = False
		self.grid.draw_outer_boundary = False
		self.grid.show_path_trace = False

		overall_start = time.time()
		total_execution_time = 0

		total_explored = 0
		total_cost = 0
		total_frontier = 0

		current_location = os.getcwd()

		for grid,short_name in list(zip(grids,short)):
			print(">Running Integrated A* on "+grid+" with  [w1="+str(w1)+"], [w2="+str(w2)+"]...")
			self.grid.load(grid)
			start_time = time.time()
			self.integrated_astar(w1,w2)
			end_time = time.time()
			total_execution_time += (end_time-start_time)

			last_cost = self.latest_search_cost
			total_cost += last_cost

			frontier_length = self.latest_frontier_length
			total_frontier += frontier_length

			explored_length = self.latest_num_explored
			total_explored += explored_length

			f.write("\n"+grid+":\t time: "+str(end_time-start_time)+", cost: "+str(last_cost)+", frontier: "+str(frontier_length)+", explored: "+str(explored_length))

			# save screenshot
			ext = short_name[:short_name.find(".grid")]
			filename = current_location+"/benchmarks/screenshots/integrated_a_star-[w1="+str(w1).replace(".","_")+"]-[w2="+str(w2).replace(".","_")+"]-["+ext+"].png"
			QPixmap.grabWindow(self.winId()).save(filename,'png')

		f.write("\n\nTotal algorithm time: "+str(total_execution_time))
		f.write("\nTotal cells explored: "+str(total_explored))
		f.write("\nTotal cost: "+str(total_cost))
		f.write("\nTotal frontier length: "+str(total_frontier))

		f.write("\n\nAverage algorithm time: "+str(total_execution_time/len(grids)))
		f.write("\nAverage cells explored: "+str(total_explored/len(grids)))
		f.write("\nAverage cost: "+str(total_cost/len(grids)))
		f.write("\nAverage frontier length: "+str(total_frontier/len(grids)))

		f.write("\n\nTotal benchmark time: "+str(time.time()-overall_start))

		self.grid.allow_render_mouse = True
		self.is_benchmark = False
		self.grid.suppress_output = False
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")
		print(">Integrated A* Search Benchmark [w1="+str(w1)+"], [w2="+str(w2)+"] Complete")

	def all_benchmark(self):
		# run benchmark on all algorithms
		print(">Running benchmark on all three algorithms...")
		self.weighted_a_star_benchmark_wrapper()
		self.astar_heuristic_wrapper()
		self.uniform_cost_benchmark()
		print(">Entire benchmark complete")

	def astar_heuristic_weight_wrapper(self):
		# run a star on all different heuristic types and several weights
		print(">Benchmarking A* Search on several weights and all heuristics...")
		for weight in [1.0,1.25,1.75,2.0]:
			for heuristic in range(6):
				self.a_star_benchmark(weight,heuristic)

	def astar_heuristic_wrapper(self):
		# run a_star on all different heuristic types
		for i in range(6):
			self.a_star_benchmark(weight=1,code=i)

	def a_star_benchmark(self,weight=1,code=0):
		# benchmark the efficiency of the A* algorithm on all files in /grids
		self.is_benchmark = True
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - BENCHMARKING")

		data_dir = "benchmarks/data/"

		if code==0: filename = data_dir+"a_star-[weight="+str(weight).replace(".","_")+"]-[euclidean].txt"
		elif code==1: filename = data_dir+"a_star-[weight="+str(weight).replace(".","_")+"]-[diagonal_distance].txt"
		elif code==2: filename = data_dir+"a_star-[weight="+str(weight).replace(".","_")+"]-[approx_euclidean].txt"
		elif code==3: filename = data_dir+"a_star-[weight="+str(weight).replace(".","_")+"]-[manhattan].txt"
		elif code==4: filename = data_dir+"a_star-[weight="+str(weight).replace(".","_")+"]-[approx_distance].txt"
		elif code==5: filename = data_dir+"a_star-[weight="+str(weight).replace(".","_")+"]-[highway].txt"
		else:
			print("Could not recognize a_star_benchmark input code.")
			return

		f = open(filename,"w")
		print(">Writing results to "+filename+"...")

		grids,short = self.get_all_grids()
		f.write("A* Benchmark on "+str(len(grids))+" .grid files [weight="+str(weight)+"], [heuristic="+str(code)+"]:\n\n")

		# turning off all UI interaction
		self.grid.allow_render_mouse = False
		self.grid.suppress_output = True
		self.grid.verbose = False
		self.grid.draw_grid_lines = False
		self.grid.draw_outer_boundary = False
		self.grid.show_path_trace = False

		overall_start = time.time()
		total_execution_time = 0

		total_explored = 0
		total_cost = 0
		total_frontier = 0

		current_location = os.getcwd()

		for grid,short_name in list(zip(grids,short)):
			print(">Running A* on "+grid+"...")
			self.grid.load(grid)
			start_time = time.time()
			self.a_star(weight,code)
			end_time = time.time()
			total_execution_time += (end_time-start_time)

			last_cost = self.latest_search_cost
			total_cost += last_cost

			frontier_length = self.latest_frontier_length
			total_frontier += frontier_length

			explored_length = self.latest_num_explored
			total_explored += explored_length

			f.write("\n"+grid+":\t time: "+str(end_time-start_time)+", cost: "+str(last_cost)+", frontier: "+str(frontier_length)+", explored: "+str(explored_length))

			# save screenshot
			ext = short_name[:short_name.find(".grid")]
			filename = current_location+"/benchmarks/screenshots/a_star-[weight="+str(weight).replace(".","_")+"]-[euclidean]-["+ext+"].png"
			QPixmap.grabWindow(self.winId()).save(filename,'png')

		f.write("\n\nTotal algorithm time: "+str(total_execution_time))
		f.write("\nTotal cells explored: "+str(total_explored))
		f.write("\nTotal cost: "+str(total_cost))
		f.write("\nTotal frontier length: "+str(total_frontier))

		f.write("\n\nAverage algorithm time: "+str(total_execution_time/len(grids)))
		f.write("\nAverage cells explored: "+str(total_explored/len(grids)))
		f.write("\nAverage cost: "+str(total_cost/len(grids)))
		f.write("\nAverage frontier length: "+str(total_frontier/len(grids)))

		f.write("\n\nTotal benchmark time: "+str(time.time()-overall_start))

		self.grid.allow_render_mouse = True
		self.is_benchmark = False
		self.grid.suppress_output = False
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")
		print(">A* Search Benchmark Complete")

	def weighted_a_star_benchmark_wrapper(self):
		# benchmark on multiple weight values for Weighted A*
		benchmark_weights = [1.25,2.0]
		print(">Benchmarking Weighted A* on "+str(len(benchmark_weights))+" weights: ",benchmark_weights)
		i = 0
		for weight in benchmark_weights:
			self.weighted_a_star_benchmark(weight,i)
			i+=1
		print(">Weighted A* Search Benchmark Complete")

	def weighted_a_star_benchmark(self,weight,benchmark_index):
		# benchmark the efficiency of the Weighted A* algorithm on all files in /grids
		self.is_benchmark = True
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - BENCHMARKING")

		data_dir = "benchmarks/data/"

		f = open(data_dir+"weighted_a_star-benchmark"+str(benchmark_index)+".txt","w")
		grids,short = self.get_all_grids()
		print(">Benchmarking Weighted A* on "+str(len(grids))+" .grid files with weight: "+str(weight)+"...")
		print(">Writing results to "+data_dir+"weighted_a_star-benchmark"+str(benchmark_index)+".txt...")
		f.write("Weighted A* Benchmark on "+str(len(grids))+" .grid files with weight: "+str(weight)+":\n\n")

		# turning off all UI interaction
		self.set_ui_interaction(False) # turn off ui interaction
		self.grid.suppress_output = True # turn off warning signals
		self.grid.draw_grid_lines = False
		self.grid.draw_outer_boundary = False
		self.grid.show_path_trace = False

		overall_start = time.time()
		total_execution_time = 0

		total_explored = 0
		total_cost = 0
		total_frontier = 0

		current_location = os.getcwd()

		for grid,short_name in list(zip(grids,short)):
			print(">Running Weighted A* on "+grid+" with weight: "+str(weight)+"...")
			self.grid.load(grid)
			start_time = time.time()
			self.a_star(weight)
			end_time = time.time()
			total_execution_time += (end_time-start_time)

			last_cost = self.latest_search_cost
			total_cost += last_cost

			frontier_length = self.latest_frontier_length
			total_frontier += frontier_length

			explored_length = self.latest_num_explored
			total_explored += explored_length

			f.write("\n"+grid+":\t time: "+str(end_time-start_time)+", cost: "+str(last_cost)+", frontier: "+str(frontier_length)+", explored: "+str(explored_length))

			# save screenshot
			ext = short_name[:short_name.find(".grid")]
			filename = current_location+"/benchmarks/screenshots/weighted_a_star-"+str(benchmark_index)+"-"+ext+".png"
			QPixmap.grabWindow(self.winId()).save(filename,'png')

		f.write("\n\nTotal algorithm time: "+str(total_execution_time))
		f.write("\nTotal cells explored: "+str(total_explored))
		f.write("\nTotal cost: "+str(total_cost))
		f.write("\nTotal frontier length: "+str(total_frontier))

		f.write("\n\nAverage algorithm time: "+str(total_execution_time/len(grids)))
		f.write("\nAverage cells explored: "+str(total_explored/len(grids)))
		f.write("\nAverage cost: "+str(total_cost/len(grids)))
		f.write("\nAverage frontier length: "+str(total_frontier/len(grids)))

		f.write("\n\nTotal benchmark time: "+str(time.time()-overall_start))

		self.set_ui_interaction(True) # turn ui interaction back on
		self.is_benchmark = False
		self.grid.suppress_output = False
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")

	def uniform_cost_benchmark(self):
		# benchmark the efficiency of the Uniform Cost Search algorithm on all files in /grids
		self.is_benchmark = True
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - BENCHMARKING")

		data_dir = "benchmarks/data/"

		filename = data_dir+"ucs.txt"
		f = open(filename,"w")

		grids,short = self.get_all_grids()
		print(">Benchmarking UCS on "+str(len(grids))+" .grid files...")
		print(">Writing results to "+filename+"...")
		f.write("Uniform-Cost Search Benchmark on "+str(len(grids))+" .grid files:\n\n")

		# turning off all UI interaction
		self.grid.allow_render_mouse = False
		self.grid.verbose = False

		self.grid.draw_grid_lines = False
		self.grid.draw_outer_boundary = False

		self.grid.suppress_output = True
		self.grid.draw_grid_lines = False
		self.grid.draw_outer_boundary = False

		self.grid.show_path_trace = False

		overall_start = time.time()
		total_execution_time = 0

		total_explored = 0
		total_cost = 0
		total_frontier = 0

		current_location = os.getcwd()

		for grid,short_name in list(zip(grids,short)):
			print(">Running Uniform-Cost Search on "+grid+"...")
			self.grid.load(grid)
			start_time = time.time()
			self.uniform_cost()
			end_time = time.time()
			total_execution_time += (end_time-start_time)

			last_cost = self.latest_search_cost
			total_cost += last_cost

			frontier_length = self.latest_frontier_length
			total_frontier += frontier_length

			explored_length = self.latest_num_explored
			total_explored += explored_length

			f.write("\n"+grid+":\t time: "+str(end_time-start_time)+", cost: "+str(last_cost)+", frontier: "+str(frontier_length)+", explored: "+str(explored_length))

			# save screenshot
			ext = short_name[:short_name.find(".grid")]
			filename = current_location+"/benchmarks/screenshots/ucs-"+ext+".png"
			QPixmap.grabWindow(self.winId()).save(filename,'png')

		f.write("\n\nTotal algorithm time: "+str(total_execution_time))
		f.write("\nTotal cells explored: "+str(total_explored))
		f.write("\nTotal cost: "+str(total_cost))
		f.write("\nTotal frontier length: "+str(total_frontier))
		f.write("\n\nAverage algorithm time: "+str(total_execution_time/len(grids)))
		f.write("\nAverage cells explored: "+str(total_explored/len(grids)))
		f.write("\nAverage cost: "+str(total_cost/len(grids)))
		f.write("\nAverage frontier length: "+str(total_frontier/len(grids)))
		f.write("\n\nTotal benchmark time: "+str(time.time()-overall_start))

		self.grid.allow_render_mouse = True
		self.grid.suppress_output = False
		self.is_benchmark = False
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")
		print(">Uniform-Cost Search Benchmark Complete")

	# State-changing utilities...
	def get_all_grids(self):
		# gets all grid filenames in /grids directory
		grids = [f for f in listdir("grids") if isfile(join("grids",f))]
		grid_filenames = []
		for g in grids:
			grid_filenames.append("grids/"+g)
		return grid_filenames,grids

	def fetch_current_grid_state(self):
		self.cells = self.grid.cells # all cells
		self.start_cell = self.grid.start_cell # start cell
		for item in self.cells:
			if item.x==self.start_cell[0] and item.y==self.start_cell[1]:
				self.start_cell = item # get cell version of start cell
				break
		self.end_cell = self.grid.end_cell # current end cell
		for item in self.cells:
			if item.x==self.end_cell[0] and item.y==self.end_cell[1]:
				self.end_cell_t = item
				break
		self.highways = self.grid.highways # current highways on grid

	def set_ui_interaction(self,enabled):
		# either turns off or on the user interaction with the grid widget
		self.grid.verbose = enabled # render timing info
		self.grid.render_mouse = enabled # current location information
		self.grid.allow_render_mouse = enabled # current location information

	def toggle_trace_highlighting(self):
		# function called by pyqt when user chooses the appropriate menu item
		if self.trace_highlighting == True:
			self.trace_highlighting = False
			self.toggle_trace_highlighting_action.setText("Turn On Trace Highlighting")
		else:
			self.trace_highlighting = True
			self.toggle_trace_highlighting_action.setText("Turn Off Trace Highlighting")

		self.grid.trace_highlighting = self.trace_highlighting # set the correct tracking state in grid
		self.grid.repaint()
		pyqt_app.processEvents()

	def toggle_mouse_tracking(self):
		# function called by pyqt when user chooses the appropriate menu item
		if self.mouse_tracking == True:
			self.mouse_tracking = False
			self.toggle_mouse_tracking_action.setText("Turn On Mouse Tracking")
		else:
			self.mouse_tracking = True
			self.toggle_mouse_tracking_action.setText("Turn Off Mouse Tracking")

		self.grid.allow_render_mouse = self.mouse_tracking # set the correct tracking state in grid
		self.grid.repaint()
		pyqt_app.processEvents()

	def update_current_cell_info(self,cell_attributes):
		# automatically called when the grid sends info, updates
		# the current cell HUD with the appropriate information
		self.cells = self.grid.cells
		if cell_attributes.is_valid:
			self.coordinates_value.setText("("+str(cell_attributes.coordinates[0])+","+str(cell_attributes.coordinates[1])+")")

			if cell_attributes.state == "full":
				self.state_value.setText("Fully Blocked")
			elif cell_attributes.state == "free":
				self.state_value.setText("Free")
			elif cell_attributes.state == "partial":
				self.state_value.setText("Partially Blocked")
			else:
				self.state_value.setText("None")

			temp = cell(cell_attributes.coordinates[0],cell_attributes.coordinates[1])
			i = get_cell_index(temp,self.cells)

			heuristic_value = self.grid.diagonal_distance_heuristic(temp,self.grid.end_cell)/4
			self.h_value.setText(str(heuristic_value))

			if cell_attributes.state=="full":
				self.g_value.setText("inf.")
				self.f_value.setText("inf.")
				self.h_value.setText("inf.")
				return

			if hasattr(self,"last_cost_list"):
				# if we have run an a* algorithm
				temp = cell(cell_attributes.coordinates[0],cell_attributes.coordinates[1])
				i = get_cell_index(temp,self.cells)
				try:
					cost = self.last_cost_list[i]
				except:
					cost = "None"

				if cost != "None":
					self.f_value.setText(str(cost+heuristic_value))
					self.g_value.setText(str(cost))
				else:
					self.f_value.setText("None")
					self.g_value.setText("None")
			else:
				self.f_value.setText("None")
				self.g_value.setText("None")

	def stop_algorithm(self):
		# called from menu item
		self.stop_executing = True

	def save_screenshot(self):
		# takes a screenshot of the current grid and saves as png
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - SAVING SCREENSHOT")
		current_location = os.getcwd()
		filename = QFileDialog.getSaveFileName(self, "Save Picture As",current_location+"/screenshots","Picture (*.png)")
		if filename != "":
			QPixmap.grabWindow(self.winId()).save(filename, 'png')
			print("Saved screenshot to"+filename)
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")

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
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - Changing Attribute Values...")
		self.setEnabled(False)
		self.value_preferences_window.open_window()

	def finished_changing_values(self):
		# called by the value preferences window when the user is done
		if self.value_preferences_window.is_valid:
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

		self.setEnabled(True)
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")

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

		self.grid.show_solution_swarm = self.show_solution_swarm
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

		self.grid.using_gradient = self.use_gradient
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

		self.grid.show_path_trace = self.show_trace
		self.grid.repaint()
		pyqt_app.processEvents()

	def regenerate_start_end(self):
		# called when the user selects the "New Start/End Cells..." menu item in tools menu
		self.grid.init_start_end_cells()
		self.grid.repaint()

	def finished_changing_colors(self):
		# called by the color preferences window when the user is done
		if self.color_preferences_window.is_valid:
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
		self.setEnabled(True)
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")

	def change_attrib_color(self):
		# function called by pyqt when user chooses change_attrib_color_action menu item
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - Changing Attribute Colors...")
		self.setEnabled(False)
		self.color_preferences_window.open_window()

	def toggle_grid_lines(self):
		# function called by pyqt when user chooses the appropriate menu item
		if self.show_grid_lines == True:
			self.show_grid_lines = False
			self.toggle_grid_lines_action.setText("Turn On Grid Lines")
		else:
			self.show_grid_lines = True
			self.toggle_grid_lines_action.setText("Turn Off Grid Lines")

		self.grid.draw_grid_lines = self.show_grid_lines
		self.grid.repaint()

	def create(self):
		# clears the current grid and creates a new random one
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - GENERATING NEW GRID")
		self.setEnabled(False)
		self.allow_render_mouse = False
		self.stop_executing = True # if performing ucs w/o multhithreading, tell it to stop
		self.ucs_agent.stop_executing = True # if using multithreading, tell usc_agent to stop executing
		pyqt_app.processEvents()
		self.grid.clear()
		self.grid.random()
		self.grid.repaint()
		self.allow_render_mouse = True
		self.setEnabled(True)
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")

	def clear(self):
		# clears the current grid
		self.stop_executing = True
		self.ucs_agent.stop_executing = True
		pyqt_app.processEvents()
		self.grid.clear()
		self.grid.repaint()

	def save_as(self):
		# allow user to save the current grid
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - SAVING")
		current_location = os.getcwd()
		filename = QFileDialog.getSaveFileName(self,"Save As", current_location+"/grids", "Grid Files (*.grid)")
		if filename != "":
			self.grid.save(filename)
			print("Finished saving "+filename)
		else:
			print("Saving canceled")
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")

	def load(self):
		# load a new grid from file
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - LOADING")
		current_location = os.getcwd()
		filename = QFileDialog.getOpenFileName(self, "Select Grid File", current_location+"/grids", "Grid Files (*.grid)")
		if filename != "":
			print("Loading grid...")
			self.grid.load(filename)
			self.grid.repaint()
			print("Finished loading "+filename)
		else:
			print("Loading canceled.")
		self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")

	def quit(self):
		# quits the application
		self.close()

	# Context Menu...
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

	# Event handlers...
	def resizeEvent(self,e):
		# called when user resizes the window
		if self.is_benchmark:
			self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+") - BENCHMARKING")
		else:
			self.setWindowTitle("AI Project 1 - (Width:"+str(self.size().width())+", Height:"+str(self.size().height())+")")
		#print(self.size().width(),self.size().height())

	def mousePressEvent(self,e):
		# called when user clicks somewhere in window
		x = e.x()
		y = e.y()
		#print(x,y)

	def closeEvent(self,e):
		if self.parent!=None:
			self.parent.close()
		sys.exit()

def main():
	global pyqt_app

	# if no command line arguments, regular operation
	if len(sys.argv)==1:
		pyqt_app = QtGui.QApplication(sys.argv)
		_ = main_window()
		sys.exit(pyqt_app.exec_())

	# if provided two arguments
	elif len(sys.argv)==3:
		action = sys.argv[1] # first input
		parameter = sys.argv[2] # second input

		if action in ["-g","--grid","--g","-grid"]:
			# user wants to create a certain number of random .grid files
			try:
				count = int(parameter)
			except:
				print("Did not recognize grid count input ("+str(parameter)+"), should be a >0 integer.")
				return

			if count <=0:
				print("Please provide a >0 integer for count paramter.")
				return

			print("Generating "+str(parameter)+" randomized grids...")
			temp_grid = non_gui_eight_neighbor_grid() # default size
			current_location = os.getcwd()
			for i in range(count):
				print("Building grid "+str(i+1)+"...",end="\r")
				filename = current_location+"/grids/"+str(i)+".grid"
				temp_grid.clear()
				temp_grid.random()
				temp_grid.save(filename)
			print("\nFinished saving "+str(count)+" randomized grids.")
			return

		else:
			print("Did not recognize command line paramters.")

	# if provided a single argument
	elif len(sys.argv)==2:
		action = sys.argv[1] # first input

		if action in ["-b","--b","-benchmark","--benchmark"]:
			# create 5 benchmark grids and a 10 start/end locations for each
			# user wants to create a certain number of random .grid files
			count = 5
			print("Generating "+str(count)+" randomized grids and 10 start/end locations.")
			temp_grid = non_gui_eight_neighbor_grid() # default size
			current_location = os.getcwd()
			for i in range(count):
				print("Building grid "+str(i+1)+"...",end="\r")
				temp_grid.clear()
				temp_grid.random() # create new grid
				for j in range(10):
					temp_grid.init_start_end_cells() # generate new start/end cells
					filename = current_location+"/grids/"+str(i)+"-"+str(j)+".grid"
					temp_grid.save(filename)
			print("\nFinished saving "+str(count)+" randomized grids.")
			return

		else:
			print("Did not recognize command line parameters.")

	else:
		print("Did not recognize command line parameters.")

if __name__ == '__main__':
	main()
