# [AI_Project](https://content.sakai.rutgers.edu/access/content/attachment/1975a4df-41ed-4746-ac06-a13a9cc7cf4b/Assignments/26768e78-7ed1-4bd5-8d6a-5fd98a16fe6f/project1.pdf)
## Search Efficiency Comparison
#### A\* Search Algorithm
![Alt text](https://github.com/bfaure/AI_Project/blob/master/screenshots/windows_astar.PNG)
#### Uniform Cost Search Algorithm
![Alt text](https://github.com/bfaure/AI_Project/blob/master/screenshots/windows_ucs.PNG)
## Controls
#### File Menu
`Ctrl+L`: Load grid from file <br>
`Ctrl+S`: Save current grid <br>
`Ctrl+Shit+S`: Save screenshot of current window<br>
`Ctrl+C`: Clear grid (stop search execution also)<br>
`Ctrl+P`: Clear the current search path<br>
`Ctrl+N`: Create new, random grid <br>
`Ctrl+Shift+N`: Open new UI window <br>
`Ctrl+Q`: Quit application <br><br>
#### Algorithm Menu
`Ctrl+1`: Run A\* Algorithm<br>
`Ctrl+2`: Run Weighted A\* Algorithm<br>
`Ctrl+3`: Run Uniform-Cost Search Algorithm<br><br>
#### Tools Menu
`Ctrl+G`: Toggle grid lines<br>
`Ctrl+T`: Toggle solution swarm<br>
`Ctrl+M`: Open color settings menu <br>
`Ctrl+V`: Open value settings menu<br><br>

## Customizability
#### Color Settings
![Alt text](https://github.com/bfaure/AI_Project/blob/master/screenshots/color_selection_window_alt.PNG)
![Alt text](https://github.com/bfaure/AI_Project/blob/master/screenshots/color_selection_window.PNG)
#### Line Type Settings
![Alt text](https://github.com/bfaure/AI_Project/blob/master/screenshots/value_selection_window.PNG)

## Instructions
`python main.py`: Open main GUI window.<br>
`python main.py -g XXX`: Generate XXX random grids, saved in the /grids directory.<br>

## Compilation Details
At the top of the main.py file there are two global variables...<br>
`TURN_OFF_CYTHON`: If true, this will disable the Cython feature. Note: the program will figure out if you have a Cython installation automatically and set this to False programmmatically so only use this feature if you HAVE Cython and wish to avoid using it.<br>
`USE_UCE_MULTITHREADED`: False by default, if set to True this will use an experimental version of the uniform cost search algorithm running on a thread separate from the UI thread.

## Dependencies
Python 2.7, PyQt4
