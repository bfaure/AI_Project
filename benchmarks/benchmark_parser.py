import os
import sys

def main():
	data_dir = "data/"
	files = os.listdir(data_dir)
	data_files = []
	for i in range(len(files)):
		if files[i].find(".txt")!=-1:
			data_files.append(data_dir+files[i])
	
	algo_names = ["a_star","integrated_a_star","sequential_a_star"]

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
			frontiers = []
			explored = []

			for filename in cur_algo_files:
				f = open(filename,"r")
				lines = f.read().split("\n")

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

				#info = info.replace("[","|")
				#info = info.replace("]","|")
				#info = info.replace("-","")
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

			f = open(algo+".txt","w")

			# write out the first line of the file
			for header in headers:

				f.write(header+"src\t")
				f.write(header+"time\t")
				f.write(header+"cost\t")
				f.write(header+"front\t")
				f.write(header+"expl")

				if headers.index(header)!=len(headers)-1:
					f.write("\t")
			f.write("\n")


			data_index = 0
			while data_index<len(sources[0]):
				for header in headers:
					f.write(sources[headers.index(header)][data_index]+"\t")
					f.write(times[headers.index(header)][data_index]+"\t")
					f.write(costs[headers.index(header)][data_index]+"\t")
					f.write(frontiers[headers.index(header)][data_index]+"\t")
					f.write(explored[headers.index(header)][data_index])
					if headers.index(header)!=len(headers)-1:
						f.write("\t")
				f.write("\n")
				data_index+=1

if __name__ == '__main__':
	main()