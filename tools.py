import random
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
rng = np.random.RandomState(100)


# Function that returns a random number (0 or 1) according to the Bernoulli probability distribution defined by p
def pull(p):
	return int(random.uniform(0, 1) < p)


# Function that returns the key of the dict that corresponds to the largest value
def argmax(B, sigma):
	B_m = -1
	i_m = -1
	for i in B.keys():
		if B[i] > B_m or B[i] == B_m and sigma[i] < sigma[i_m]:
			B_m = B[i]
			i_m = i
	return i_m


# Function that returns a pseudo-random permutation of 1,...,K
def generate_permutation(K):
	sigma = {}
	for element in range(1, K+1):
		sigma[element] = rng.randint(0, sys.maxsize)
	vals_sorted = sorted(sigma.values())
	for element in sigma.keys():
		sigma[element] = vals_sorted.index(sigma[element]) + 1
	return sigma


# Function that regurns sigma^{-1}(i) for a pseudo-random permutation sigma
def get_inverse(sigma, i):
	for k in sigma.keys():
		if sigma[k] == i:
			return k
	return None


# Function that returns K and mu read from a file
def get_K_mu_from_file(file_name):
	f = open(file_name, "r")
	K = int(f.readline())
	mu = dict()
	for i in range(1, K+1):
		mu[i] = float(f.readline())
	f.close()
	return (K, mu)


# Function that returns list of rewards and averages for all measured time
def parse_json_output(file_name):
	with open(file_name, 'r') as f:
		result = json.load(f)
	nb_runs = len(result)
	R_list = []
	aggregate_time = 0
	aggregates = dict()
	for run in range(nb_runs):
		run = str(run)
		R_list.append(result[run]["R"])
		aggregate_time += result[run]["time"]
		if run == '0':	
			for key, values in result[run].items():
				if key != "R" and key != "time":
					aggregates[key] = result[run][key]
		else:
			for key, values in result[run].items():
				if key != "R" and key != "time":
					aggregates[key] += result[run][key]

	aggregate_time /= nb_runs
	for key in aggregates.keys():
		aggregates[key] /= nb_runs
		
	return (R_list, aggregate_time, aggregates)


# Run algorithm "algo", with command line arguments: 1. nb_runs, 2. N, 3. file for K and mu, 4. output_file, and 5. random seed
def run_experiment1(algo):
	nb_runs = int(sys.argv[1])
	N =  int(sys.argv[2])
	K, mu = get_K_mu_from_file(sys.argv[3])
	output_file = sys.argv[4]
	random.seed(int(sys.argv[5]))

	result = dict()
	for run in range(nb_runs):
		result[run] = algo(N, K, mu)
		print (run, result[run]["time"])

	with open(output_file, 'w') as fp:
	    json.dump(result, fp)



# Test if all lists in R_list are identical; Useful to check if all algorithms return exactly the same cumulative reward
def check_results(R_list, algos):
	for j in range(len(R_list) - 1):
		l1 = R_list[algos[j]]
		l2 = R_list[algos[j+1]]
		for e in range(len(l1)):
			assert(l1[e]==l2[e])


# Plot one line for each algorithm + pie chart only for some point
def plot_lines_and_pie(scenario, algos, algos_names, left_xlabel, left_xlog, left_x, left_data, right_aggregates_all, right_message, OUTPUT_DIR):
	plt.figure(figsize=(12, 3))
	plt.rcParams.update({'font.size':14})

	# left : plot one line for each algorithm
	ax = plt.subplot(121)
	markers = ('x', 'o', '*', '.')
	for algo in algos:
		plt.plot(left_x, left_data[algo], marker=markers[algos.index(algo)])
	plt.legend(algos_names, bbox_to_anchor=(1.5, 0.8))
	#plt.subplots_adjust(left=-0.15)
	if left_xlog:
		plt.xscale('log')
	else:
		plt.xticks(left_x, left_x)
	plt.yscale('log')
	plt.xlabel(left_xlabel)
	plt.ylabel('Time (seconds)')
	plt.subplots_adjust(top=0.9, bottom=0.2)

	# right : pie chart only for some point
	plt.subplot(144)		
	plt.title("Zoom on UCB-DS for " + right_message)
	K = len(right_aggregates_all["ucb_ds"].keys()) - 3
	components = ["time U", "time AS"] + ["time R" + str(i) for i in range(1, K+1)]
	time_per_component = [right_aggregates_all["ucb_ds"][component] for component in components]
	components = list(map (lambda x: x[5:], components)) # remove "time " from the left of each key
	#if not left_xlog:
	#	plt.rcParams.update({'font.size':10})

	colors = ["#FF0033","#2D5DF5","#B75F31","#22792E","#413DE7","#19DBAD","#7653C2","#F3AE32","#1B9978","#5A82F1","#E9953F","#EBD86D","#3BECA4","#1E0968","#2952B0","#2E01A6","#2613DF","#5AC0AB","#1FD9EF","#441A71","#AA64AC","#960DC9","#BF6434","#21C13D","#1A8990","#B75EC4","#CFDE9F","#04350E","#B3CF0A","#E26F5D","#2EFD6E","#BEA469","#3F4696","#F46962","#162FE9","#E26CD6","#6433F1"]

	plt.pie(time_per_component, labels=components, colors=colors)

	plt.savefig(OUTPUT_DIR + "plot_scenario" + scenario + ".pdf")
	plt.clf()

