This is the code used for the experiments from our papers:

+ Conference version: [Secure Outsourcing of Multi-Armed Bandits](https://ieeexplore.ieee.org/document/9343228)

+ Journal version: [Secure Protocols for Cumulative Reward Maximization in Stochastic Multi-Armed Bandits](https://content.iospress.com/articles/journal-of-computer-security/jcs210051)

If you use our code, please cite:


    @inproceedings{CLLS20,
      author    = {Ciucanu, R. and Lafourcade, P. and {Lombard-Platet}, M. and Soare, M.},
      title     = {{Secure Outsourcing of Multi-Armed Bandits}},
      booktitle = {IEEE International Conference on Trust, Security and Privacy in Computing and Communications (TrustCom)},
      year      = {2020},
      pages     = {202--209}
    }
    
    @article{CLLS22,
      author    = {Ciucanu, R. and Lafourcade, P. and {Lombard-Platet}, M. and Soare, M.},
      title     = {{Secure Protocols for Cumulative Reward Maximization in Stochastic Multi-Armed Bandits}},
      journal   = {Journal of Computer Security (JCS)},
      year      = {2022},
      note      = {Accepted (to appear)}
}

We have done our implementation in Python 3 on Ubuntu.
We provide a detailed description of the experimental setup and results in Section 4 of our paper.
The script `install-python-and-libraries.sh` installs Python 3 and the necessary libraries.

The script `scalability-experiments.py` allows to reproduce the plots "Scalability with respect to N" and "Scalability with respect to K".

The script `real-world-experiment.py` allows to reproduce the plot on "Real-world data scenarios".

Each of the aforementioned two scripts assumes that each scenario (N, K, mu) from each of the figures has been already run 100 times and the running times are already reported in `output_experiment1` for "Scalability with respect to N", `experiment2` for "Scalability with respect to K", and `real-world-data-output` for "Real-world data scenarios".
If you want to re-run the 100 runs for each scenario (N, K, mu), you simply need to uncomment the lines that start with `#os.system("python3 " + algo...` in the scripts.
