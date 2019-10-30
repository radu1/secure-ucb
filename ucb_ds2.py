import time
import os
import sys
import json
from math import sqrt, log

from phe import paillier
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

sys.path.append(os.path.relpath("."))
from tools import pull, generate_permutation, get_inverse, run_experiment1

from ucb_ds import DataOwner, User, R_node, ArmSelector


########## class R_node2
class R_node2(R_node):
	# Initialize arm node i, who has variables s_i, n_i, and t needed to compute B_i later on
	def __init__(self, K, i, pk_U, key, key_AS_Ri):
		self.time = 0
		t = time.time()
		self.i = i
		self.s_i = 0
		self.n_i = 0
		self.t = K-1
		self.pk_U = pk_U # the pk of User is needed to send ecrypted sum of rewards at the end
		self.key = key # shared key with AS, DO, and other R_i
		self.key_AS_Ri = key_AS_Ri # shared only with AS
		self.time += time.time() - t

	# Step 2: Arm node i receives a triple of ciphertexts (b, first, node), is pulled if b=1, then updates its variables
	def receive_AS(self, triple_and_iv):
		t = time.time()
		ciphertext_b, ciphertext_first, ciphertext_next, iv, self.iv_i_m = triple_and_iv
		cipher = AES.new(self.key, AES.MODE_CBC, iv)
		self.b = int(unpad(cipher.decrypt(ciphertext_b), AES.block_size))
		self.first = int(unpad(cipher.decrypt(ciphertext_first), AES.block_size))
		self.next = int(unpad(cipher.decrypt(ciphertext_next), AES.block_size))
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
		iv = get_random_bytes(16)
		cipher1 = AES.new(self.key, AES.MODE_CBC, iv)
		cipher2 = AES.new(self.key_AS_Ri, AES.MODE_CBC, self.iv_i_m)
		ciphertext_i_m1 = cipher2.encrypt(pad(str(self.i).encode('utf-8'), AES.block_size))
		ciphertext_i_m2 = cipher1.encrypt(pad(ciphertext_i_m1, AES.block_size))
		ciphertext_B_m = cipher1.encrypt(pad(str(self.B_i).encode('utf-8'), AES.block_size))	
		self.time += time.time() - t
		self.R_nodes[self.next].receive_Ri((ciphertext_B_m, ciphertext_i_m2, iv))

	# Step 3/4: Arm node i receives pair (B_m, i_m), updates variables, and sends either to next arm node or to AS
	def receive_Ri(self, pair_and_iv):
		t = time.time()
		ciphertext_B_m, ciphertext_i_m, iv = pair_and_iv
		cipher = AES.new(self.key, AES.MODE_CBC, iv)
		ciphertext_i_m2 = unpad(cipher.decrypt(ciphertext_i_m), AES.block_size)
		B_m = float(unpad(cipher.decrypt(ciphertext_B_m), AES.block_size))
		if self.B_i > B_m:
			B_m = self.B_i
			cipher_i_m = AES.new(self.key_AS_Ri, AES.MODE_CBC, self.iv_i_m)
			ciphertext_i_m2 = cipher_i_m.encrypt(pad(str(self.i).encode('utf-8'), AES.block_size))
		iv = get_random_bytes(16)
		cipher = AES.new(self.key, AES.MODE_CBC, iv)
		ciphertext_i_m = cipher.encrypt(pad(ciphertext_i_m2, AES.block_size))
		if self.next != 0:
			ciphertext_B_m = cipher.encrypt(pad(str(B_m).encode('utf-8'), AES.block_size))
		self.time += time.time() - t
		if self.next != 0:
			self.R_nodes[self.next].receive_Ri((ciphertext_B_m, ciphertext_i_m, iv))
		else:
			self.AS.receive_Ri((ciphertext_i_m, iv))



########## class ArmSelector2
class ArmSelector2(ArmSelector):
	# Initialize AS, who knows K
	def __init__(self, K, key, keys_AS_Ri):
		self.time = 0
		t = time.time()
		self.K = K
		self.i_m = 0 # index of arm to be pulled next, is updated during the Exploration-exploitation phase
		self.key = key # shared key with DO, R_i
		self.keys_AS_Ri = keys_AS_Ri # list of keys, each of them shared with a single R_i
		self.time += time.time() - t


	# Step 2: Send triple (b, first, node) to each arm node, based on the generated permutation
	def send_Ri(self):
		t = time.time()
		self.sigma = generate_permutation(self.K)
		self.time += time.time() - t
		self.iv_i_m = dict()
		for i in range(1, self.K+1):
			t = time.time()
			b = 1 if (self.i_m == 0 or self.i_m == i) else 0
			first = 1 if (self.sigma[i] == 1) else 0
			next = 0 if (self.sigma[i] == self.K) else get_inverse(self.sigma, self.sigma[i]+1)
			iv = get_random_bytes(16)
			cipher = AES.new(self.key, AES.MODE_CBC, iv)
			ciphertext_b = cipher.encrypt(pad(str(b).encode('utf-8'), AES.block_size))
			ciphertext_first = cipher.encrypt(pad(str(first).encode('utf-8'), AES.block_size))
			ciphertext_next = cipher.encrypt(pad(str(next).encode('utf-8'), AES.block_size))
			self.iv_i_m[i] = get_random_bytes(16)
			self.time += time.time() - t
			self.R_nodes[i].receive_AS((ciphertext_b, ciphertext_first, ciphertext_next, iv, self.iv_i_m[i]))
			t = time.time()
			if first == 1:
				first_node = self.R_nodes[i]
			self.time += time.time() - t
		first_node.start_ring()


	# Step 4: Receive the index of the arm to be pulled next
	def receive_Ri(self, ciphertext_and_iv):
		t = time.time()
		ciphertext_i_m, iv = ciphertext_and_iv
		cipher = AES.new(self.key, AES.MODE_CBC, iv)
		ciphertext_i_m2 = unpad(cipher.decrypt(ciphertext_i_m), AES.block_size)
		for i in range(1, self.K+1):	
			cipher2 = AES.new(self.keys_AS_Ri[i], AES.MODE_CBC, self.iv_i_m[i])
			try:
				self.i_m = int(unpad(cipher2.decrypt(ciphertext_i_m2), AES.block_size).decode('utf-8'))
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

	U = User(N) # we create User here because her pk is needed to initialize each arm node

	# step 0
	DO = DataOwner(K, mu, key)
	R_nodes = dict()
	for i in range (1, K+1):
		R_nodes[i] = R_node2(K, i, U.pk, key, keys_AS_Ri[i])
		data_DO_Ri = DO.outsource_arm(i)
		R_nodes[i].receive_outsourced_mu(data_DO_Ri)

	# step 1
	AS = ArmSelector2(K, key, keys_AS_Ri)
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

	result["time DO"] = DO.time
	result["time U"] = U.time
	result["time AS"] = AS.time

	check_time = 0
	check_time += DO.time + U.time + AS.time

	for i in range(1, K+1):
		result["time R" + str(i)] = R_nodes[i].time
		check_time += R_nodes[i].time

	assert (result["time"] - check_time < 0.03 * result["time"])

	return result


run_experiment1(UCB_DS2)
