import os
import sys
import numpy as np
import matplotlib.pyplot as plt
sys.path.append(os.path.relpath("."))
from tools import parse_json_output, check_results
import warnings
warnings.simplefilter("ignore")

nb_runs = 100
algos = ["ucb_ds2", "ucb_ds", "ucb_d", "ucb"]
algos_names = ["UCB-DS2", "UCB-DS", "UCB-D", "UCB"]

scenarios = ["Jester-small", "Jester-large", "MovieLens"]
DIR_OUT = "real-world-data-output/"
os.system("mkdir -p " + DIR_OUT)

N = 100000

aggregates_time = dict()
for algo in algos:
	aggregates_time[algo] = list()

for scenario in scenarios:
	input_file = "real-world-data/" + scenario + ".txt"
	aggregates_all = dict()
	R_list = dict()
	for algo in algos:
		print ("*" * 10 + " Scenario=", scenario, "N=", N, "algo=", algo)
		output_file = DIR_OUT + "scenario" + scenario + "_N_" + str(N) + "_" + algo + ".txt"
		#os.system("python3 " + algo + ".py " + str(nb_runs) + " " + str(N) + " " + input_file + " " + output_file + " 0")
		R_list[algo], aggregate_time, aggregates_all[algo] = parse_json_output(output_file)
		aggregates_time[algo].append(aggregate_time)		
	# check that all algorithms give the same cumulative reward
	check_results(R_list, algos)


# plot bars
plt.figure(figsize=(14, 2.5))
plt.rcParams.update({'font.size':14})
x = np.arange(len(scenarios))  # the label locations
plt.xticks(x, scenarios)
width = 0.5  # the width of the bars
plt.bar(x + 2*width/3, aggregates_time["ucb_ds2"], width/3, label='UCB-DS2', color='none', edgecolor='blue', hatch="--")
plt.bar(x + width/3, aggregates_time["ucb_ds"], width/3, label='UCB-DS', color='none', edgecolor='red', hatch="//")
plt.bar(x , aggregates_time["ucb_d"], width/3, label='UCB-D', color='none', edgecolor='green', hatch="||")
plt.bar(x - width/3, aggregates_time["ucb"], width/3, label='UCB', color='none', edgecolor='black')
plt.yscale('log')
plt.ylabel('Time (seconds)')
plt.legend(algos_names, bbox_to_anchor=(0.8,1.1), ncol=4)
plt.savefig(DIR_OUT + "plot_real_world_data.pdf")
