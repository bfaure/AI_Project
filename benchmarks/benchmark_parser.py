import os
import sys

GET_SOURCES 			= True
GET_TIMES 				= True
GET_COSTS 				= True
GET_FRONTIERS 			= False
GET_EXPLORED 			= False
GET_MEMORY_FOOTPRINT 	= True
GET_EFFICIENCY 			= False
GET_SPEED 				= False


def main():
	data_dir = "data/"
	files = os.listdir(data_dir)
	data_files = []
	for i in range(len(files)):
		if files[i].find(".txt")!=-1:
			data_files.append(data_dir+files[i])
	
	algo_names = ["a_star","integrated_a_star","sequential_a_star","ucs"]

	for algo in algo_names:
		print("Parsing data for "+algo+"...")
		target = "[algo="+algo+"]"
		cur_algo_files = []
		for file in data_files:
			if file.find(target)!=-1:
				cur_algo_files.append(file)

		if len(cur_algo_files)>0:

			headers = [] # list containing first line of all files
			sources = []
			times = []
			costs = []
			frontiers = [] # length of frontier
			explored = []  # number explored cells
			memory_footprint = [] # explored+frontier
			efficiency = [] # time * cost 
			speed = [] # explored / time

			for filename in cur_algo_files:
				f = open(filename,"r")
				lines = f.read().split("\n")
				file_index = cur_algo_files.index(filename)

				trim_title = False
				if trim_title:
					# making the header shorter so it fits in to the MATLAB file importer title
					info = lines[0]
					info = info[info.find("algo=")+5:]
					info = info.replace("_","")
					info = info.replace("weight","w")
					info = info.replace("=","")
					info = info.replace("]-[",".")
					info = info.replace("]",".")
					info = info.replace(".","_")
					
					info = info.replace("integratedastar","intastar")
					info = info.replace("sequentialastar","seqastar")

					info = info.replace("approxdistance","appdist")
					info = info.replace("approxeuclidean","appeuc")
					info = info.replace("diagonaldistance","diagdist")
					info = info.replace("euclidean","euc")
					info = info.replace("manhattan","man")
				else:
					info = lines[0]

				headers.append(info)

				for line in lines[1:]:
					if line not in [""," "] and line.find("Average")==-1 and line.find("Total Time:")==-1:
						if line.find("sources:")!=-1:
							text = line[line.find("[")+1:line.find("]")]
							text = text.split(",")
							sources.append(text)
						elif line.find("times:")!=-1:
							text = line[line.find("[")+1:line.find("]")]
							text = text.split(",")
							times.append(text)							
						elif line.find("costs:")!=-1:
							text = line[line.find("[")+1:line.find("]")]
							text = text.split(",")
							costs.append(text)
						elif line.find("frontiers:")!=-1:
							text = line[line.find("[")+1:line.find("]")]
							text = text.split(",")
							frontiers.append(text)
						elif line.find("explored:")!=-1:
							text = line[line.find("[")+1:line.find("]")]
							text = text.split(",")
							explored.append(text)
				f.close()

				# calculate time * cost for the various data members
				cur_efficiencies = []
				for c,t in list(zip(costs[file_index],times[file_index])):
					cur_efficiencies.append(str(float(t)*float(c)))
				efficiency.append(cur_efficiencies)

				cur_speed = []
				for e,t in list(zip(explored[file_index],times[file_index])):
					if e=="": 
						cur_speed.append(1) # if there was an error reading 
						print("ERROR while reading "+filename+" explored data")

					else: cur_speed.append(str(float(e)/float(t)))
				speed.append(cur_speed)

				cur_memory = []
				for explored_size,frontier_size in list(zip(explored[file_index],frontiers[file_index])):
					try:
						e = int(explored_size)
					except:
						e = -1
						print("ERROR while reading "+filename+" explored data")
					try:
						f = int(frontier_size)
					except:
						f = -1
						print("ERROR while reading "+filename+" frontier data")

					cur_memory.append(str(int(e)+int(f)))
				memory_footprint.append(cur_memory)

			f = open(algo+".txt","w")

			# write out the first line of the file
			for header in headers:

				if GET_SOURCES: 	f.write(header+"_sources\t")
				if GET_TIMES: 		f.write(header+"_times\t")
				if GET_COSTS: 		f.write(header+"_costs\t")
				if GET_MEMORY_FOOTPRINT: f.write(header+"_memory")
				if GET_FRONTIERS: 	f.write(header+"_front\t")
				if GET_EFFICIENCY:	f.write(header+"_eff\t")
				if GET_SPEED: 		f.write(header+"_speed\t")
				if GET_EXPLORED: 	f.write(header+"_expl")

				if headers.index(header)!=len(headers)-1:
					f.write("\t")
			f.write("\n")

			data_index = 0
			while data_index<len(sources[0]):
				for header in headers:
					if GET_SOURCES: 		f.write(sources[headers.index(header)][data_index]+"\t")
					if GET_TIMES: 			f.write(times[headers.index(header)][data_index]+"\t")
					if GET_COSTS: 			f.write(costs[headers.index(header)][data_index]+"\t")
					if GET_MEMORY_FOOTPRINT:f.write(memory_footprint[headers.index(header)][data_index]+"\t")
					if GET_FRONTIERS: 		f.write(frontiers[headers.index(header)][data_index]+"\t")
					if GET_EFFICIENCY: 		f.write(efficiency[headers.index(header)][data_index]+"\t")
					if GET_SPEED: 			f.write(speed[headers.index(header)][data_index]+"\t")
					if GET_EXPLORED: 		f.write(explored[headers.index(header)][data_index])
					if headers.index(header)!=len(headers)-1:
						f.write("\t")
				f.write("\n")
				data_index+=1

if __name__ == '__main__':
	main()