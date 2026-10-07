# Experiment 5b: Cilantro Experiment

In this experiment, we replicate the Cilantro Paper's Microservice Experiment. The purpose of this experiment is to highlight the impacts that the workload generator flaws have on experimental results by showing how wrk2-DSB's flaw impacts the results of the Cilantro paper. 

The Cilantro paper used wrk2-DSB to generate 3000 RPS towards the DeathStarBench HotelReservation application and recorded the throughput reported by the workload generator itself. This experiment highlights how the impacted measurements from wrk2-DSB's flaws impact the conclusion of the SelfTune paper.

## Setup

This experiment requires 10 40 vCPU machines (or any setup of a total of 400 vCPU works, but Ubuntu 22.04 for proper setup), where machines 1-10 run the HotelReservation application with Kubernetes along with a Kubernetes service that runs the LG every 30 seconds. Regarding this, here is the procedure

1. Initialize 10 machines with each machine having 40 vCPU 
2. Clone this repository in the machines if you have not
3. On machines 1-10, check out to `cilantro_experiment/experiment5b` directory and install Kubernetes cluster by running (Follow instructions on the command line after running commands):
```
source cloudlab_k8s_setup.sh
```
4. On machine 1, clone the Cilantro code and change to that directory by running
```
git clone https://github.com/mittal1787/cilantro.git
cd cilantro
git checkout hotelreservation-k6
```
5. To run the default experiment (wrk2-DSB with exponential distribution, 3000 RPS with 32 threads and 32 connections), run with wrk2-dsb by following the exact instructions of the Microservice experiment in Cilantro docs.
```
cd experiments/microservices
./starters/launch_hotelres.sh #instructions from the README. Make sure to verify with watch kubectl get pods
# Set the policy to run - ucbopt, propfair, msile, msevoopt
POLICY=propfair
# Our setup is similar to running on EKS, so we use the EKS driver (but if running on kind, use the kind driver)
./starters/launch_cilantro_driver.sh ~/.kube/config $POLICY
```

6. After 8 hours of running the experiment, fetch the results using
```
# From the documentation
./starters/fetch_results.sh
```

7. Clean the cluster by running
```
./starters/clean_cluster.sh
```

8. Repeat steps 5-7 for each baseline you want to run by changing the POLICY variable (as also mentioned in the Cilantro Repo Microservices experiment README) (One other thing to suggest is to rename the workdirs_eks to `workdirs_eks_default` if you are going to do all the experimenting in all the same directory)

### Different Combinations of Threads and Combinations

9. Now we do similar for different combinations of threads and connections, where in the [starters/hotel-res/cilantro-hr-client.yaml](https://github.com/mittal1787/cilantro/blob/c7513cb6159bded8cc9bed4664814bf235db3247/experiments/microservices/starters/hotel-res/cilantro-hr-client.yaml#L35) file, you change the `--wrk-num-threads` to change the number of threads and `--wrk-num-connections` to change the number of connections. 

10. Repeat steps 5-8 for these new combination of threads and connections (One other thing to suggest is to rename the workdirs_eks to `workdirs_eks_wrk2dsb_<num_threads>t_<num_connections>c` if you are going to do all the experimenting in all the same directory).

### Fixed Distribution wrk2-DSB

11. We also do similar for fixed distribution rather exponential distribution for wrk2-DSB. To start, in the home directory, clone the `cilantro-workloads` repository:
```
cd ~
git clone https://github.com/mittal1787/cilantro-workloads.git
cd cilantro-workloads/deathstarbench/hotelreservation
```

12. In that directory, remove the "exp" from `command` in [`construct_command` of wrk_driver.py](https://github.com/mittal1787/cilantro-workloads/blob/f5e2cca3476fdbd889a18224c9acd80af012b0ea/deathstarbench/hotelreservation/hr-client/driver/wrk_driver.py#L74)

13. Push the wrk driver to the docker image by running:
```
sh ./hr-client/docker_build_ecr.sh
```

14. Change back to the `cilantro` directory
```
cd ~ && cd cilantro
```

15. Repeat Steps 5-10 for this setup (One other thing to suggest is to rename the workdirs_eks to `workdirs_eks_wrk2dsb_fixed_<num_threads>t_<num_connections>c` if you are going to do all the experimenting in all the same directory).

### Experiment with k6
16. Repeat steps 5-10, with some differences:
    
    a. Instead of running `./starters/launch_cilantro_driver.sh ~/.kube/config $POLICY`, you run `./starters/launch_cilantro_driver_k6.sh ~/.kube/config $POLICY` to run the k6 code
    
    b. Instead of changing the threads (`--wrk-num-threads`) and connections (`--wrk-num-connections`), we instead change the number of Preallocated Virtual Users (VUs) (`--k6-preallocated-vus`).

    c. Rename the workdirs_eks to `workdirs_eks_k6_<num_pre_vus>prevu` if you are going to do all the experimenting in all the same directory

### Earthmovers Distance Computation
17. For each of these computed `workdirs_eks`, copy their path, and add it to the `directories` list in  the `cilantro_experiment/compute_earthmovers_distance.py` file (Future work is to polish that file thoroughly). 

18. In the `LG_Configurations` list of that same file, put the wrk2-DSB threads count, connections count, and distribution type as a list entry in the form of `"wrk2-DSB (<num_threads> threads, <num_connections> connections, <distribution_type> distribution)"` for the wrk2-DSB experiments. In that same list, for the k6 experiments, type as a list entry in the form of `"k6 (<num_preallocated_vus> VUs)"`.

19. For each of the instances of `thread_and_conn` variables in that same file, update the list with each entry representing the number of threads and connections (in a tuple) (e.g `(<num_threads>, <num_connections>)`) for wrk2-DSB runs. Similar case for the `ax.plot3D`.

20. For the k6 experiment, edit the `VUs` variable in that file with the number of preallocated VUs used for each k6 experiment iteration.

21. Generate the graphs by running these commands:
```
cd ~
cd ~/load-fiction-artifact/cilantro_experiment
# We change directory first, so then the graphs show up in the experiment5b directory
python3 compute_earthmovers_distance.py
```