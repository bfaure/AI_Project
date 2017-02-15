import os
import sys

# target can be one of: time, cost, frontier, explored
# file is the name of the benchmark file

def parse_benchmark(file,target):
	f = open(file,"r")
	text = f.read()
	lines = text.split("\n")

	target = target+": "

	for line in lines:
		if line.find("grids/")!=-1:
			start = line.find(target)
			end = line.find(", ",start+len(target))
			value = line[start+len(target):end]
			print value

def main():

	


	'''
	if len(sys.argv)==2:
		# the file to parse is argv[1]
		filename = sys.argv[1]
		attribute = "time" # default
	elif len(sys.argv)==3:
		filename = sys.argv[1]
		attribute = sys.argv[2]
	else:
		filename = "a_star-benchmark.txt"
		attribute = "time"

	parse_benchmark(filename,attribute)
	'''

if __name__ == '__main__':
	main()