import time
import os
import random
from phe import paillier
from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


time_Paillier_enc = 0.
time_Paillier_dec = 0.
time_AES_enc = 0.
time_AES_dec = 0.
nb_runs = 100
N = 100000
K = 10

for i in range(nb_runs):
  # draw a random message
  m = random.randint(0, N)
  
  # Paillier
  pk, sk = paillier.generate_paillier_keypair()
  
  t = time.time()
  c = pk.encrypt(m)
  time_Paillier_enc += time.time() - t
  
  t = time.time()
  m2 = sk.decrypt (c)
  time_Paillier_dec += time.time() - t
  assert (m == m2)
  
  # AES
  key = get_random_bytes(32)
  aesgcm = AESGCM(key)
  nonce = os.urandom(12)
  
  t = time.time()
  c = aesgcm.encrypt(nonce, str(m).encode('utf-8'), None)
  time_AES_enc += time.time() - t
  
  t = time.time()
  m2 = int(aesgcm.decrypt(nonce, c, None))
  time_AES_dec += time.time() - t
  assert (m == m2)
  
time_Paillier_enc /= nb_runs
time_Paillier_dec /= nb_runs
time_AES_enc /= nb_runs
time_AES_dec /= nb_runs
diff_enc = time_Paillier_enc - time_AES_enc
diff_dec = time_Paillier_dec - time_AES_dec

print ("Encryption")
print ("\t Paillier:   {0:.10f}".format(time_Paillier_enc), "seconds")
print ("\t AES-GCM:    {0:.10f}".format(time_AES_enc), "seconds")
print ("\t Difference: {0:.10f}".format(diff_enc), "seconds")

print ("Decryption")
print ("\t Paillier:   {0:.10f}".format(time_Paillier_dec), "seconds")
print ("\t AES-GCM:    {0:.10f}".format(time_AES_dec), "seconds")
print ("\t Difference: {0:.10f}".format(diff_dec), "seconds")

nb_op = K + (N - K + 1) * 2 * K
overhead = int (nb_op * (diff_enc + diff_dec) / 3600)

print ("For a fixed N=", N, " and K=", K, ", overhead=", overhead, "hours")
