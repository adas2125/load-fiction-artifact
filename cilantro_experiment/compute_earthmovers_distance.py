import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
import os

ROOT_DIR = "../../../Load Fiction (original)"
directories = [
    # f"/users/yugm2/cilantro/experiments/microservices/workdirs_eks",
    f"{ROOT_DIR}/workdirs_eks_wrk2dsb_40t_1000c",
    f"{ROOT_DIR}/workdirs_eks_wrk2dsb_40t_3000c",
    f"{ROOT_DIR}/workdirs_eks_wrk2_dsb_fixed",
    f"{ROOT_DIR}/workdirs_eks_wrk2_dsb_fixed_40t_1000c",
    f"{ROOT_DIR}/workdirs_eks_wrk2_dsb_fixed_40t_3000c",
    f"{ROOT_DIR}/workdirs_eks_k6_3000prevu",    # CHANGE LOG: ADDED
    f"{ROOT_DIR}/workdirs_eks_k6_1500prevu",
    f"{ROOT_DIR}/workdirs_eks_k6_6000prevu",
    f"{ROOT_DIR}/workdirs_eks_vegeta"
]

LG_configurations = [
    # "wrk2-DSB (32 threads, 32 connections, exponential distribution)",
    "wrk2-DSB (40 threads, 1000 connections, exponential distribution)",
    "wrk2-DSB (40 threads, 3000 connections, exponential distribution)",
    "wrk2-DSB (32 threads, 32 connections, fixed distribution)",
    "wrk2-DSB (40 threads, 1000 connections, fixed distribution)",
    "wrk2-DSB (40 threads, 3000 connections, fixed distribution)",
    "k6 (3000 VUs)",
    "k6 (1500 VUs)",
    "k6 (6000 VUs)",
    "Vegeta"
]

autoscalers = [
    'msile',
    'ucbopt',
    'msevoopt',
    'propfair'
]


all_dataframe_data = {}
all_dist_data = {}
for i in range(len(directories)):
    directory = directories[i]
    config = LG_configurations[i]
    starting_autoscaler = "ucbopt"
    dataframes = {}
    # print(directory)
    for subdir, dirs, files in os.walk(directory):
        if subdir != directory:
            # print(subdir)
            for autoscaler in autoscalers:
                if autoscaler in subdir:
                    dataframes[autoscaler] = pd.read_csv(f"{subdir}/hr-client.csv")
    
    
    # print(wasserstein_distance(dataframes["ucbopt"]["p99"], dataframes["propfair"]["p99"]))
    # print(wasserstein_distance(dataframes["ucbopt"]["p99"], dataframes["msile"]["p99"]))
    # print(wasserstein_distance(dataframes["ucbopt"]["p99"], dataframes["msevoopt"]["p99"]))
    all_dataframe_data[config] = dataframes
    all_dist_data[config] = {
        "propfair": wasserstein_distance(dataframes["ucbopt"]["p99"], dataframes["propfair"]["p99"]),
        "msile": wasserstein_distance(dataframes["ucbopt"]["p99"], dataframes["msile"]["p99"]),
        "msevoopt" : wasserstein_distance(dataframes["ucbopt"]["p99"], dataframes["msevoopt"]["p99"])
    }
    # print(dataframes)
print(all_dist_data)


autoscalers = [
    'msile',
    'msevoopt',
    'propfair'
]

autoscaler_to_true_name = {
    "msevoopt": "ε-Greedy",
    "msile": "EvoAlg",
    "propfair": "ResourceFair" 
}  

autoscaler_to_linestyle = {
    "msevoopt": "-",
    "msile": "--",
    "propfair": ":" 
}  

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
thread_and_conn = [(32,32),(40,1000), (40,3000)]
# for autoscaler in autoscalers:
#     try:
#         ax.plot3D([32,40,40], [32,1000,3000], [all_dist_data[f"wrk2-DSB ({thread} threads, {conn} connections, exponential distribution)"][autoscaler] for thread, conn in thread_and_conn], label=autoscaler_to_true_name[autoscaler], linestyle=autoscaler_to_linestyle[autoscaler])
#     except KeyError:
#         print(f"Missing data for {autoscaler} in wrk2-DSB (exponential distribution)")
#     # ax.plot3D([32,40,40], [32,1000,3000], [all_dist_data[f"wrk2-DSB ({thread} threads, {conn} connections, exponential distribution)"]["msile"] for thread, conn in thread_and_conn])
#     # ax.plot3D([32,40,40], [32,1000,3000], [all_dist_data[f"wrk2-DSB ({thread} threads, {conn} connections, exponential distribution)"]["msevoopt"] for thread, conn in thread_and_conn])
# ax.set_title("Difference in Performance Between Autoscalers When Stressed With wrk2-DSB (Exponential Distribution)", wrap=True, size=16)
# ax.set_xlabel("Threads", size=15)
# ax.set_ylabel("Connections", size=15, labelpad=7)
# ax.set_zlabel("Earthmover's Distance", size=15, labelpad=7)
# plt.xticks(fontsize=14)
# plt.yticks(fontsize=14)
# ax.tick_params(axis='z', labelsize=14)
# # ax.tick_params(axis='both', pad=2.5)
# # ax.tick_params(axis='both', which='major', fontsize=15)

# plt.legend(fontsize="14")
# plt.show()
# # plt.savefig("wrk2_dsb_exp_emd.pdf", bbox_inches='tight')

# plt.clf()
ax = fig.add_subplot(111, projection='3d')
thread_and_conn = [(32,32),(40,1000), (40,3000)]
for autoscaler in autoscalers:
    try:
        ax.plot3D([32,40,40], [32,1000,3000], [all_dist_data[f"wrk2-DSB ({thread} threads, {conn} connections, fixed distribution)"][autoscaler] for thread, conn in thread_and_conn], label=autoscaler_to_true_name[autoscaler], linestyle=autoscaler_to_linestyle[autoscaler])
    except KeyError:
        print(f"Missing data for {autoscaler} in wrk2-DSB (fixed distribution)")
# ax.plot3D([32,40,40], [32,1000,3000], [all_dist_data[f"wrk2-DSB ({thread} threads, {conn} connections, fixed distribution)"]["propfair"] for thread, conn in thread_and_conn])
# ax.plot3D([32,40,40], [32,1000,3000], [all_dist_data[f"wrk2-DSB ({thread} threads, {conn} connections, fixed distribution)"]["msile"] for thread, conn in thread_and_conn])
# ax.plot3D([32,40,40], [32,1000,3000], [all_dist_data[f"wrk2-DSB ({thread} threads, {conn} connections, fixed distribution)"]["msevoopt"] for thread, conn in thread_and_conn])
ax.set_title("Difference in Performance Between Autoscalers When Stressed With wrk2-DSB (Fixed Distribution)", wrap=True, size=16)
ax.set_xlabel("Threads", size=15)
ax.set_ylabel("Connections", size=15, labelpad=7)
ax.set_zlabel("Earthmover's Distance", size=15, labelpad=7)
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
ax.tick_params(axis='z', labelsize=14)
# ax.tick_params(axis='both', pad=2.5)
# ax.tick_params(axis='both', which='major', fontsize=15)
# ax.set_zticks(fontsize=14)
plt.legend(fontsize="14")
plt.show()
# plt.savefig("wrk2_dsb_fixed_emd.pdf", bbox_inches='tight')

plt.clf()
VUs = [1500,3000, 6000]
for autoscaler in autoscalers:
    try:
        plt.plot([1500,3000,6000], [all_dist_data[f"k6 ({VU} VUs)"][autoscaler] for VU in VUs], label=autoscaler_to_true_name[autoscaler], linestyle=autoscaler_to_linestyle[autoscaler])
    except KeyError:
        print(f"Missing data for {autoscaler} in k6")
# plt.plot([1500,3000,6000], [all_dist_data[f"k6 ({VU} VUs)"]["propfair"] for VU in VUs])
# plt.plot([1500,3000,6000], [all_dist_data[f"k6 ({VU} VUs)"]["msile"] for VU in VUs])
# plt.plot([1500,3000,6000], [all_dist_data[f"k6 ({VU} VUs)"]["msevoopt"] for VU in VUs])
plt.title("Difference in Performance Between Cilantro and Autoscalers When Stressed With k6", wrap=True, size=16)
plt.xlabel("Virtual Users (Preallocated)", size=15)
plt.ylabel("Earthmover's Distance", size=15)
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.legend(fontsize="14")
plt.show()
# plt.savefig("k6_emd.pdf", bbox_inches='tight')