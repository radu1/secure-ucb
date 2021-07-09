import os
import sys
sys.path.append(os.path.relpath("."))
from tools import parse_json_output, check_results, plot_lines_and_pie
import warnings
warnings.simplefilter("ignore")

nb_runs = 100
algos = ["ucb_ds2", "ucb_ds", "ucb_d", "ucb"]
algos_names = ["UCB-DS2", "UCB-DS", "UCB-D", "UCB"]


######### Experiment 1: Vary N for fixed K
scenarios_experiment1 = ["1", "2", "3", "4", "5", "6"]
N_vals = [100, 1000, 10000, 100000]
DIR_EXP1_IN = "input_experiment1/"
DIR_EXP1_OUT = "output_experiment1/"

for scenario in scenarios_experiment1:
	input_file = DIR_EXP1_IN + "scenario" + scenario + ".txt"
	aggregates_time = dict()
	for algo in algos:
		aggregates_time[algo] = list()
	aggregates_all = dict()
	for N in N_vals:
		R_list = dict()
		for algo in algos:
			print ("*" * 10 + " Scenario=", scenario, "N=", N, "algo=", algo)
			output_file = DIR_EXP1_OUT + "scenario" + scenario + "_N_" + str(N) + "_" + algo + ".txt"
			#os.system("python3 " + algo + ".py " + str(nb_runs) + " " + str(N) + " " + input_file + " " + output_file + " 0")
			R_list[algo], aggregate_time, aggregates_all[algo] = parse_json_output(output_file)
			aggregates_time[algo].append(aggregate_time)		
		# check that all algorithms give the same cumulative reward
		check_results(R_list, algos)
	# generate plot
	plot_lines_and_pie(scenario, algos, algos_names, "Budget N", True, N_vals, aggregates_time, aggregates_all, "N=" + str(N), DIR_EXP1_OUT)


######### Experiment 2: Vary K for fixed N
'''K_vals = [5, 10, 15, 20]
N = 100000
DIR_EXP2 = "experiment2/"
os.system("mkdir -p " + DIR_EXP2)

aggregates_time = dict()
for algo in algos:
	aggregates_time[algo] = list()
aggregates_all = dict()
for K in K_vals:
	scenario = "_K_" + str(K)
	input_file = DIR_EXP2 + "scenario" + scenario + ".txt"
	f = open(input_file, "w")
	f.write(str(K) + "\n0.9" + "\n0.8" * (K-1))
	f.close()
	R_list = dict()
	for algo in algos:
		print ("*" * 10 + " Scenario", scenario, "N=", N, "algo=", algo)
		output_file = DIR_EXP2 + "scenario" + scenario + "_N_" + str(N) + "_" + algo + ".txt"
		#os.system("python3 " + algo + ".py " + str(nb_runs) + " " + str(N) + " " + input_file + " " + output_file + " 0")
		R_list[algo], aggregate_time, aggregates_all[algo] = parse_json_output(output_file)
		aggregates_time[algo].append(aggregate_time)		
	# check that all algorithms give the same cumulative reward
	check_results(R_list, algos)
# generate plot
plot_lines_and_pie("_vary_K_", algos, algos_names, "Number of arms K", False, K_vals, aggregates_time, aggregates_all, "K=" + str(K), DIR_EXP2)'''
