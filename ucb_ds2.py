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

from ucb_ds import DataOwner, DataClient, R_node, ArmSelector


########## class R_node2
class R_node2(R_node):
	# Initialize arm node i, who has variables s_i, n_i, and t needed to compute B_i later on
	def __init__(self, K, i, pk_DC, key, key_AS_Ri):
		self.time = 0
		t = time.time()
		self.i = i
		self.s_i = 0
		self.n_i = 0
		self.t = K-1
		self.pk_DC = pk_DC # the pk of DataClient is needed to send ecrypted sum of rewards at the end
		self.key = key # shared key with AS, DO, and other R_i
		self.aesgcm = AESGCM(self.key)
		self.key_AS_Ri = key_AS_Ri # shared only with AS
		self.aesgcm2 = AESGCM(self.key_AS_Ri)
		self.time += time.time() - t

	# Step 3: Start ring computation
	def start_ring(self):
		t = time.time()
		nonce1 = os.urandom(12)
		nonce2 = os.urandom(12)
		nonce3 = os.urandom(12)
		ciphertext_i_m1 = self.aesgcm2.encrypt(nonce1, str(self.i).encode('utf-8'), None)
		ciphertext_i_m2 = self.aesgcm.encrypt(nonce2, ciphertext_i_m1, None)
		ciphertext_B_m = self.aesgcm.encrypt(nonce3, str(self.B_i).encode('utf-8'), None)
		self.time += time.time() - t
		self.R_nodes[self.next].receive_Ri((ciphertext_B_m, ciphertext_i_m2, nonce1, nonce2, nonce3))

	# Step 3/4: Arm node i receives pair (B_m, i_m), updates variables, and sends either to next arm node or to AS
	def receive_Ri(self, pair_and_nonces):
		t = time.time()
		ciphertext_B_m, ciphertext_i_m2, nonce1, nonce2, nonce3 = pair_and_nonces

		ciphertext_i_m1 = self.aesgcm.decrypt(nonce2, ciphertext_i_m2, None)
		B_m = float(self.aesgcm.decrypt(nonce3, ciphertext_B_m, None))
		if self.B_i > B_m:
			B_m = self.B_i
			nonce1 = os.urandom(12)
			ciphertext_i_m1 = self.aesgcm2.encrypt(nonce1, str(self.i).encode('utf-8'), None)
		nonce2 = os.urandom(12)
		ciphertext_i_m2 = self.aesgcm.encrypt(nonce2, ciphertext_i_m1, None)
		if self.next != 0:
			nonce3 = os.urandom(12)
			ciphertext_B_m = self.aesgcm.encrypt(nonce3, str(B_m).encode('utf-8'), None)
		self.time += time.time() - t
		if self.next != 0:
			self.R_nodes[self.next].receive_Ri((ciphertext_B_m, ciphertext_i_m2, nonce1, nonce2, nonce3))
		else:
			self.AS.receive_Ri((ciphertext_i_m2, nonce1, nonce2))



########## class ArmSelector2
class ArmSelector2(ArmSelector):
	# Initialize AS, who knows K
	def __init__(self, K, key, keys_AS_Ri):
		self.time = 0
		t = time.time()
		self.K = K
		self.i_m = 0 # index of arm to be pulled next, is updated during the Exploration-exploitation phase
		self.key = key # shared key with DO, R_i
		self.aesgcm = AESGCM(self.key)
		self.keys_AS_Ri = keys_AS_Ri # list of keys, each of them shared with a single R_i
		self.aesgcm2 = dict()
		for i in range(1, self.K+1):
			self.aesgcm2[i] = AESGCM(self.keys_AS_Ri[i])
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
	def receive_Ri(self, ciphertext_and_nonces):
		t = time.time()
		ciphertext_i_m2, nonce1, nonce2 = ciphertext_and_nonces
		ciphertext_i_m1 = self.aesgcm.decrypt(nonce2, ciphertext_i_m2, None)
		for i in range(1, self.K+1):	
			try:
				self.i_m = int(self.aesgcm2[i].decrypt(nonce1, ciphertext_i_m1, None).decode('utf-8'))
			except:
				continue
			if 1 <= self.i_m and self.i_m <= self.K:
				break
		self.time += time.time() - t



########## Main program 
def UCB_DS2(N, K, mu):
	t_start = time.time()

	# generate AES CBC key; the key is shared between DO, AS, R_i
	key = get_random_bytes(32)

	# generate K AES CBC keys shared between AS and a single R_i
	keys_AS_Ri = dict()
	for i in range(1, K+1):
		keys_AS_Ri[i] = get_random_bytes(32)

	DC = DataClient(N) # we create DataClient here because her pk is needed to initialize each arm node

	# step 0
	DO = DataOwner(K, mu, key)
	R_nodes = dict()
	for i in range (1, K+1):
		R_nodes[i] = R_node2(K, i, DC.pk, key, keys_AS_Ri[i])
		data_DO_Ri = DO.outsource_arm(i)
		R_nodes[i].receive_outsourced_mu(data_DO_Ri)

	# step 1
	AS = ArmSelector2(K, key, keys_AS_Ri)
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


run_experiment1(UCB_DS2)
