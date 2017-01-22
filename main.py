# python 2.7

import os
import sys

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# class to hold details for a single cell
class cell:
	def __init__(self,x_coordinate=None,y_coordinate=None):
		self.state = "free"
		self.x = x_coordinate
		self.y = y_coordinate

# UI element (widget) that represents the interface with the grid
class eight_neighbor_grid(QWidget):

	def __init__(self,num_columns=160,num_rows=120):
		# constructor, pass the number of cols and rows
		super(eight_neighbor_grid,self).__init__()		
		self.num_columns = num_columns
		self.num_rows = num_rows
		self.init_ui()

	def init_ui(self):
		# initialize ui elements
		self.setMinimumSize(800,600) # grid dimensions
		self.line_color = [0,0,0] # black for cell lines
		self.free_cell_color = [255,255,255] # white for free cell
		self.trans_cell_color = [128,128,128] # gray cell for partially blocked
		self.blocked_cell_color = [0,0,0] # black cell for blocked
		self.end_cell_color = [255,0,0] # red cell for end location
		self.start_cell_color = [0,255,0] # green cell for start location
		self.init_cells()

	def init_cells(self):
		# creates the list of cells in the grid (all default to free)
		self.cells = []
		for x in range(self.num_columns):
			for y in range(self.num_rows):
				new_cell = cell(x,y)
				self.cells.append(new_cell)
		self.start_cell = (0,0) # default start cell
		self.end_cell = (self.num_columns-1,self.num_rows-1) # default end cell
		self.hard_to_traverse_cells = [] # empty by default


	def save(self,filename):
		# saves the current grid to filename location
		f = open(filename, 'w')

		f.write("s_start:("+str(self.start_cell[0])+","+str(self.start_cell[1])+")\n")
		f.write("s_goal:("+str(self.end_cell[0])+","+str(self.end_cell[1])+")\n")
		for hard_cell in self.hard_to_traverse_cells:
			f.write("hard:("+str(hard_cell[0])+","+str(hard_cell[1])+")\n")

		row_ct = 0
		line_buf = ""
		for cell in self.cells:
			row_ct += 1			
			if cell.state == "full":
				line_buf+='0'
			if cell.state == "free":
				line_buf+='1'
			if cell.state == "partial":
				line_buf+='2'
			if cell.state == "free_highway":
				line_buf+='a'
			if cell.state == "partial_highway":
				line_buf+='b'

			if row_ct == self.num_columns:
				line_buf+="\n"
				f.write(line_buf)
				line_buf = ""
				row_ct = 0

	def load(self,filename):
		# loads in a new set of cells from a file, see the assignment pdf for
		# details on the file format
		f 			= open(filename,'r') # open the file
		lines 		= f.read().split('\n') # split file into lines
		new_cells 	= [] # to hold the new cells
		start_cell 	= None # string (x,y) 
		end_cell 	= None # string (x,y)
		hard_to_traverse_cells = [] # to hold (x,y) locations of hard to traverse cells

		for line in lines:
			if line.find("s_start:")!=-1:
				start_cell = line.split(":")[1]
			elif line.find("s_goal:")!=-1:
				end_cell = line.split(":")[1]
			elif line.find("hard:")!=-1:
				hard_to_traverse_cells.append(line.split(":")[1])
			elif line in [""," "]:
				# just an empty line, skip it
				continue
			else:
				for char in line:

					cell_state = None
					if char == '0':
						cell_state = "full"
					elif char == '1':
						cell_state = "free"
					elif char == '2':
						cell_state = "partial"
					elif char == 'a':
						cell_state = "free_highway"
					elif char == 'b':
						cell_state = "partial_highway"

					new_cell = cell()
					new_cell.state = cell_state
					new_cells.append(new_cell)

		self.cells = new_cells
		self.start_cell = eval(start_cell)
		self.end_cell = eval(end_cell)

		self.hard_to_traverse_cells = []
		for item in hard_to_traverse_cells:
			self.hard_to_traverse_cells.append(eval(item))
		print("Finished loading "+filename)


	def paintEvent(self, e):
		# called by pyqt when it needs to update the widget (dimensions changed, etc.)
		qp = QPainter()
		qp.begin(self)
		self.drawWidget(qp)
		qp.end()

	def drawWidget(self, qp):
		# draw the grid, let the (0,0) cell be in the top left of the window
		print("Re-Drawing Grid")
		size = self.size() # current size of widget
		width = size.width() # current width of widget
		height = size.height() # current height of widget

		horizontal_step = int(round(width/self.num_columns)) # per cell width
		vertical_step = int(round(height/self.num_rows)) # per cell height

		index = 0
		for cell in self.cells:

			x = index % self.num_columns # x coordinate
			y = int(index/self.num_columns) # get the y coordinate

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

			qp.setPen(QColor(cell_color[0],cell_color[1],cell_color[2]))
			qp.setBrush(QColor(cell_color[0],cell_color[1],cell_color[2])) 

			x_start = x*horizontal_step
			y_start = y*vertical_step

			qp.drawRect(x_start,y_start,x_start+horizontal_step,y_start+vertical_step)

			index += 1

		pen = QPen(QColor(self.line_color[0],self.line_color[1],self.line_color[2]), 1, Qt.SolidLine)
		qp.setPen(pen)
		qp.setBrush(Qt.NoBrush)

		for x in range(self.num_columns):
			qp.drawLine(x*horizontal_step,0,x*horizontal_step,height)

		for y in range(self.num_rows):
			qp.drawLine(0,y*vertical_step,width,y*vertical_step)
		
		qp.drawLine(0,0,0,height-1)
		qp.drawLine(0,0,width-1,0)
		qp.drawLine(0,height-1,width-1,height-1)
		qp.drawLine(width-1,0,width-1,height-1)

	def set_cell_state(self,x_coord,y_coord,state):
		# updates a single cell in the grid with a new state then reloads the ui
		size = self.size()
		width = size.width()
		height = size.height()

		x_coord = x_coord - 1.0
		y_coord = y_coord - 1.0

		if x_coord<0: x_coord = 0
		if y_coord<0: y_coord = 0

		x = int(round(float((float(x_coord)/float(width))*float(self.num_columns))))
		y = int(round(float((float(y_coord)/float(height))*float(self.num_rows))))

		print("changing cell at x="+str(x)+", y="+str(y))

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
				print("Changing cell to "+state)
				self.cells[index].state = state 
				break
			index += 1

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
		self.file_menu = self.menu_bar.addMenu("File")

		# menubar actions
		load_action = self.file_menu.addAction("Load...",self.load,QKeySequence("Ctrl+L"))
		save_action = self.file_menu.addAction("Save As...",self.save_as,QKeySequence("Ctrl+S"))
		self.file_menu.addSeparator()
		quit_action = self.file_menu.addAction("Quit", self.quit, QKeySequence("Ctrl+Q"))

		self.resize(1627,1252) # ratio for a single grid is 4:3 (160,120)
		self.show()

	def save_as(self):
		# allow user to save the current grid
		filename = QFileDialog.getSaveFileName(self,"Save As")
		if filename != "":
			self.grid.save(filename)

	def load(self):
		# load a new grid from file
		filename = QFileDialog.getOpenFileName(self, "Select File")
		if filename != "":
			self.grid.load(filename)
		self.grid.repaint()

	def quit(self):
		# quits the application
		self.close()

	def on_context_menu_request(self,point):
		# function called when user right clicks on grid
		print(point)
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
		print(self.size().width(),self.size().height())

	def mousePressEvent(self,e):
		# called when user clicks somewhere in window
		x = e.x()
		y = e.y()
		print(x,y)

def main():
	pyqt_app = QtGui.QApplication(sys.argv)
	_ = main_window()
	sys.exit(pyqt_app.exec_())	


if __name__ == '__main__':
	main()