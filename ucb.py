import time
import os
import sys
import json
from math import sqrt, log

sys.path.append(os.path.relpath("."))
from tools import pull, argmax, run_experiment1, generate_permutation


def UCB(N, K, mu):
	t_start = time.time()

	# Initialization phase: Pull each arm once and initialize variables
	R = 0
	s = dict()
	n = dict()
	xhat = dict()
	B = dict()
	for i in range(1, K+1):
		r = pull(mu[i])
		s[i] = r 
		n[i] = 1
		xhat[i] = r
		R += r
		B[i] = xhat[i] + sqrt(2. * log(K) / n[i])

	# Permutation of arm indexes needed to randomly select the next arm to pull if multiple arms have same B_i
	sigma = generate_permutation(K)

	# Exploration-exploitation phase: Pull the arms until the end of the budget
	for t in range(K+1, N+1):
		a = argmax(B, sigma)
		r = pull(mu[a])
		s[a] += r
		n[a] += 1
		xhat[a] = 1. * s[a] / n[a]
		R += r
		for i in range(1, K+1):
			B[i] = xhat[i] + sqrt(2. * log(t) / n[i])
		sigma = generate_permutation(K) # New permutation for the next iteration
	
	# construct and return result
	result = dict()
	result["R"] = R
	result["time"] = time.time() - t_start
	return result


run_experiment1(UCB)
