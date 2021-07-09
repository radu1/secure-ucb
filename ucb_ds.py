import time
import os
import sys
import json
from math import sqrt, log

from phe import paillier
from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

sys.path.append(os.path.relpath("."))
from tools import pull, generate_permutation, get_inverse, run_experiment1


########## class DataOwner
class DataOwner():
	# Initialize DataOwner, who knowns K and mu
	def __init__(self, K, mu, key):
		self.time = 0
		t = time.time()
		self.K = K
		self.mu = mu
		self.key = key # shared key with AS, R_i
		self.aesgcm = AESGCM(self.key)
		self.time += time.time() - t

	# Step 0: DataOwner outsources mu[i]
	def outsource_arm(self, i):
		t = time.time()
		nonce = os.urandom(12)
		ciphertext_mu_i = self.aesgcm.encrypt(nonce, str(self.mu[i]).encode('utf-8'), None)
		self.time += time.time() - t
		return (ciphertext_mu_i, nonce)


########## class DataClient
class DataClient():
	# Initialize DataClient, who has a budget N
	def __init__(self, N):
		self.time = 0
		t = time.time()
		self.N = N
		self.pk, self._sk = paillier.generate_paillier_keypair()
		self.time += time.time() - t

	# Step 1: Send the budget
	def send_budget(self, N):
		return N

	# Step 6: Receive the cumulative reward
	def receive_R(self, ciphertext_R):
		t = time.time()
		self.R = self._sk.decrypt(ciphertext_R)
		self.time += time.time() - t


########## class R_node
class R_node():
	# Initialize arm node i, who has variables s_i, n_i, and t needed to compute B_i later on
	def __init__(self, K, i, pk_DC, key):
		self.time = 0
		t = time.time()
		self.i = i
		self.s_i = 0
		self.n_i = 0
		self.t = K-1
		self.pk_DC = pk_DC # the pk of DataClient is needed to send ecrypted sum of rewards at the end
		self.key = key # shared key with AS, DO
		self.aesgcm = AESGCM(self.key)
		self.time += time.time() - t

	# Step 0: Arm node i receives its mu[i] that is outsourced by DataOwner
	def receive_outsourced_mu(self, data_DO_Ri):
		t = time.time()
		ciphertext_mu_i, nonce = data_DO_Ri
		self.mu_i = float(self.aesgcm.decrypt(nonce, ciphertext_mu_i, None))
		self.time += time.time() - t

	# Step 2: Arm node i receives a triple of ciphertexts (b, first, node), is pulled if b=1, then updates its variables
	def receive_AS(self, triple_and_nonces):
		t = time.time()
		ciphertext_b, ciphertext_first, ciphertext_next, nonce1, nonce2, nonce3 = triple_and_nonces
		self.b = int(self.aesgcm.decrypt(nonce1, ciphertext_b, None))
		self.first = int(self.aesgcm.decrypt(nonce2, ciphertext_first, None))
		self.next = int(self.aesgcm.decrypt(nonce3, ciphertext_next, None))
		self.t += 1
		if self.b == 1:
			r = pull(self.mu_i)
			self.s_i += r
			self.n_i += 1
		self.B_i = 1. * self.s_i / self.n_i + sqrt(2. * log(self.t) / self.n_i)
		self.time += time.time() - t

	# Step 3: Start ring computation
	def start_ring(self):
		t = time.time()
		nonce1 = os.urandom(12)
		nonce2 = os.urandom(12)
		ciphertext_B_m = self.aesgcm.encrypt(nonce1, str(self.B_i).encode('utf-8'), None)
		ciphertext_i_m = self.aesgcm.encrypt(nonce2, str(self.i).encode('utf-8'), None)
		self.time += time.time() - t
		self.R_nodes[self.next].receive_Ri((ciphertext_B_m, ciphertext_i_m, nonce1, nonce2))

	# Step 3/4: Arm node i receives pair (B_m, i_m), updates variables, and sends either to next arm node or to AS
	def receive_Ri(self, pair_and_nonces):
		t = time.time()
		ciphertext_B_m, ciphertext_i_m, nonce1, nonce2 = pair_and_nonces
		B_m = float(self.aesgcm.decrypt(nonce1, ciphertext_B_m, None))
		i_m = int(self.aesgcm.decrypt(nonce2, ciphertext_i_m, None))
		if self.B_i > B_m:
			B_m = self.B_i
			i_m = self.i
		if self.next != 0:
			nonce1 = os.urandom(12)
			ciphertext_B_m = self.aesgcm.encrypt(nonce1, str(B_m).encode('utf-8'), None)
		ciphertext_i_m = self.aesgcm.encrypt(nonce2, str(i_m).encode('utf-8'), None)
		self.time += time.time() - t
		if self.next != 0:
			self.R_nodes[self.next].receive_Ri((ciphertext_B_m, ciphertext_i_m, nonce1, nonce2))
		else:
			self.AS.receive_Ri((ciphertext_i_m, nonce2))


	# Step 5: Arm node i sends the sum of rewards that it produced
	def send_partial_reward(self):
		t = time.time()
		ciphertext_s_i = self.pk_DC.encrypt(self.s_i)
		self.time += time.time() - t
		return ciphertext_s_i


########## class ArmSelector
class ArmSelector():
	# Initialize AS, who knows K
	def __init__(self, K, key):
		self.time = 0
		t = time.time()
		self.K = K
		self.i_m = 0 # index of arm to be pulled next, is updated during the Exploration-exploitation phase
		self.key = key # shared key with DO, R_i
		self.aesgcm = AESGCM(self.key)
		self.time += time.time() - t

	# Step 1: Receive budget
	def receive_budget(self, N):
		t = time.time()
		self.N = N
		self.time += time.time() - t
	
	# Step 2: Send triple (b, first, node) to each arm node, based on the generated permutation
	def send_Ri(self):
		t = time.time()
		self.sigma = generate_permutation(self.K)
		self.time += time.time() - t
		for i in range(1, self.K+1):
			t = time.time()
			b = 1 if (self.i_m == 0 or self.i_m == i) else 0
			first = 1 if (self.sigma[i] == 1) else 0
			next = 0 if (self.sigma[i] == self.K) else get_inverse(self.sigma, self.sigma[i]+1)
			nonce1 = os.urandom(12)
			nonce2 = os.urandom(12)
			nonce3 = os.urandom(12)
			ciphertext_b = self.aesgcm.encrypt(nonce1, str(b).encode('utf-8'), None)
			ciphertext_first = self.aesgcm.encrypt(nonce2, str(first).encode('utf-8'), None)
			ciphertext_next = self.aesgcm.encrypt(nonce3, str(next).encode('utf-8'), None)
			self.time += time.time() - t
			self.R_nodes[i].receive_AS((ciphertext_b, ciphertext_first, ciphertext_next, nonce1, nonce2, nonce3))
			t = time.time()
			if first == 1:
				first_node = self.R_nodes[i]
			self.time += time.time() - t
		first_node.start_ring()

	# Step 4: Receive the index of the arm to be pulled next
	def receive_Ri(self, ciphertext_and_nonce):
		t = time.time()
		ciphertext_i_m, nonce = ciphertext_and_nonce
		self.i_m = int(self.aesgcm.decrypt(nonce, ciphertext_i_m, None))
		self.time += time.time() - t

	# Step 5: Sums up all partial rewards to obtain the cumulative reward
	def compute_cumulative_reward(self):
		ciphertext_partial_rewards = []
		for i in range(1, self.K+1):
			ciphertext_partial_rewards.append(self.R_nodes[i].send_partial_reward())
		t = time.time()
		ciphertext_R = sum(ciphertext_partial_rewards)
		self.time += time.time() - t
		return ciphertext_R



########## Main program 
def UCB_DS(N, K, mu):
	t_start = time.time()

	# generate AES CBC key; the key is shared between DO, AS, R_i
	key = get_random_bytes(32)

	DC = DataClient(N) # we create DataClient here because her pk is needed to initialize each arm node

	# step 0
	DO = DataOwner(K, mu, key)
	R_nodes = dict()
	for i in range (1, K+1):
		R_nodes[i] = R_node(K, i, DC.pk, key)
		data_DO_Ri = DO.outsource_arm(i)
		R_nodes[i].receive_outsourced_mu(data_DO_Ri)

	# step 1
	AS = ArmSelector(K, key)
	data_DC_AS = DC.send_budget(AS)
	AS.receive_budget(data_DC_AS)

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
	DC.receive_R(R)
	
	# construct and return result
	result = dict()
	result["R"] = DC.R
	result["time"] = time.time() - t_start

	result["time DO"] = DO.time
	result["time DC"] = DC.time
	result["time AS"] = AS.time

	check_time = 0
	check_time += DO.time + DC.time + AS.time

	for i in range(1, K+1):
		result["time R" + str(i)] = R_nodes[i].time
		check_time += R_nodes[i].time
	assert (result["time"] - check_time < 0.03 * result["time"])

	return result


# to avoid executing run_experiment1(UCB_DS) when classes from this file are imported in ucb_ds2.py
if __name__ == "__main__":
	run_experiment1(UCB_DS)
