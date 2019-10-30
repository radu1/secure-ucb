import time
import os
import sys
import json
from math import sqrt, log

sys.path.append(os.path.relpath("."))
from tools import pull, generate_permutation, get_inverse, run_experiment1

########## class DataOwner
class DataOwner():
	# Initialize DataOwner, who knowns K and mu
	def __init__(self, K, mu):
		self.K = K
		self.mu = mu

	# Step 0: DataOwner outsources mu[i]
	def outsource_arm(self, i):
		return self.mu[i]


########## class User
class User():
	# Initialize User, who has a budget N
	def __init__(self, N):
		self.N = N

	# Step 1: Send the budget
	def send_budget(self, N):
		return N

	# Step 6: Receive the cumulative reward
	def receive_R(self, R):
		self.R = R


########## class R_node
class R_node():
	# Initialize arm node i, who has variables s_i, n_i, and t needed to compute B_i later on
	def __init__(self, K, i):
		self.i = i
		self.s_i = 0
		self.n_i = 0
		self.t = K-1

	# Step 0: Arm node i receives its mu[i] that is outsourced by DataOwner
	def receive_outsourced_mu(self, mu_i):
		self.mu_i = mu_i

	# Step 2: Arm node i receives a triple (b, first, node), is pulled if b=1, then updates its variables
	def receive_AS(self, triple):
		self.b, self.first, self.next = triple
		self.t += 1
		if self.b == 1:
			r = pull(self.mu_i)
			self.s_i += r
			self.n_i += 1
		self.B_i = 1. * self.s_i / self.n_i + sqrt(2. * log(self.t) / self.n_i)

	# Step 3: Start ring computation
	def start_ring(self):
		self.R_nodes[self.next].receive_Ri((self.B_i, self.i))

	# Step 3/4: Arm node i receives pair (B_m, i_m), updates variables, and sends either to next arm node or to AS
	def receive_Ri(self, pair):
		B_m, i_m = pair
		if self.B_i > B_m:
			B_m = self.B_i
			i_m = self.i
		if self.next != 0:
			self.R_nodes[self.next].receive_Ri((B_m, i_m))
		else:
			self.AS.receive_Ri(i_m)

	# Step 5: Arm node i sends the sum of rewards that it produced
	def send_partial_reward(self):
		return self.s_i


########## class ArmSelector
class ArmSelector():
	# Initialize AS, who knows K
	def __init__(self, K):
		self.K = K
		self.i_m = 0 # index of arm to be pulled next, is updated during the Exploration-exploitation phase

	# Step 1: Receive budget
	def receive_budget(self, N):
		self.N = N
	
	# Step 2: Send triple (b, first, node) to each arm node, based on the generated permutation
	def send_Ri(self):
		self.sigma = generate_permutation(self.K)
		for i in range(1, self.K+1):
			b = 1 if (self.i_m == 0 or self.i_m == i) else 0
			first = 1 if (self.sigma[i] == 1) else 0
			next = 0 if (self.sigma[i] == self.K) else get_inverse(self.sigma, self.sigma[i]+1)
			self.R_nodes[i].receive_AS((b, first, next))
			if first == 1:
				first_node = self.R_nodes[i]	
		first_node.start_ring()

	# Step 4: Receive the index of the arm to be pulled next
	def receive_Ri(self, i_m):
		self.i_m = i_m

	# Step 5: Sums up all partial rewards to obtain the cumulative reward
	def compute_cumulative_reward(self):
		R = 0
		for i in range(1, self.K+1):
			R += self.R_nodes[i].send_partial_reward()
		return R



########## Main program 
def UCB_D(N, K, mu):
	t_start = time.time()

	# step 0
	DO = DataOwner(K, mu)
	R_nodes = dict()
	for i in range (1, K+1):
		R_nodes[i] = R_node(K, i)
		data_DO_Ri = DO.outsource_arm(i)
		R_nodes[i].receive_outsourced_mu(data_DO_Ri)

	# step 1
	AS = ArmSelector(K)
	U = User(N)
	data_U_AS = U.send_budget(AS)
	AS.receive_budget(data_U_AS)

	# make nodes know each other
	AS.R_nodes = R_nodes
	for i in range(1, K+1):
		R_nodes[i].AS = AS
		R_nodes[i].R_nodes = R_nodes

	# steps 2, 3, 4
	for i in range(N-K+1):
		AS.send_Ri()
		
	# steps 5, 6
	R = AS.compute_cumulative_reward()
	U.receive_R(R)
	
	# construct and return result
	result = dict()
	result["R"] = U.R
	result["time"] = time.time() - t_start
	return result




run_experiment1(UCB_D)

