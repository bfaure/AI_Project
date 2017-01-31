# [AI_Project](https://content.sakai.rutgers.edu/access/content/attachment/1975a4df-41ed-4746-ac06-a13a9cc7cf4b/Assignments/26768e78-7ed1-4bd5-8d6a-5fd98a16fe6f/project1.pdf)
## Uniform-Cost Search
#### With `solution_swarm`
![Alt text](https://github.com/bfaure/AI_Project/blob/master/screenshots/ucs_windows_2.png)<br>
#### Without `solution_swarm`
![Alt text](https://github.com/bfaure/AI_Project/blob/master/screenshots/ucs_windows_3.png)<br>
## Custom Colors
![Alt text](https://github.com/bfaure/AI_Project/blob/master/screenshots/screenshot_windows.png)

## Controls
`Ctrl+L`: Load grid from file <br>
`Ctrl+S`: Save current grid <br>
`Ctrl+C`: Clear grid <br>
`Ctrl+N`: Create new, random grid <br>
`Ctrl+Q`: Quit application <br>
`Ctrl+M`: Change colors <br><br>
`Ctrl+1`: Run A\* Algorithm<br>
`Ctrl+2`: Run Weighted A\* Algorithm<br>
`Ctrl+3`: Run Uniform-Cost Search Algorithm<br>

## Instructions
Run `python main.py` (normal execution of Python 2.7) to open the UI. If you have Cython installed the lib/helpers.py file will automatically be copied to helpers.pyx and Cython will build this up to helpers.c. If Cython is not installed, the original helpers.py file will be used.

## Dependencies
Python 2.7, PyQt4
