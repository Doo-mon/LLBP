import os
import pandas as pd
from datetime import datetime
import time
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mticker


# 设置要扫描的根目录
root_dir = '../results'


# 设置开始时间
start_time = datetime.strptime('12:27:05', '%H:%M:%S')

# 相关对应关系字典
bms = {
    'nodeapp-nodeapp': 'NodeApp',
    'mwnginxfpm-wiki': 'PHPWiki',
    'benchbase-tpcc': 'TPCC',
    'benchbase-twitter': 'Twitter',
    'benchbase-wikipedia': 'Wikipedia',
    'dacapo-kafka': 'Kafka',
    'dacapo-spring': 'Spring',
    'dacapo-tomcat': 'Tomcat',
    'renaissance-finagle-chirper': 'Chirper',
    'renaissance-finagle-http': 'HTTP',
    'charlie.1006518': 'Charlie',
    'delta.507252': 'Delta',
    'merced.467915': 'Merced',
    'whiskey.426708': 'Whiskey'
}

# 定义模型列表
models = [
    ("tage64kscl-ae.txt", "64K TSL"),
    ("tage512kscl-ae.txt", "512K TSL"),
    ("llbp-timing-ae.txt", "LLBP"),
    ("llbp-ae.txt", "LLBP-0Lat")
]

# 创建一个空的DataFrame用于存储所有数据
dfall = pd.DataFrame()

# 遍历每个模型配置
for cfg, model_name in models:

    dftmp = pd.DataFrame()
    for bm, benchmark_name in bms.items():

        file_path = os.path.join(root_dir, bm, cfg)
        if os.path.exists(file_path):
            # 获取文件修改时间
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            mod_time_seconds = mod_time.hour * 3600 + mod_time.minute * 60 + mod_time.second
            start_time_seconds = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
            execution_time = mod_time_seconds - start_time_seconds
        else:
            execution_time = 'N/A'

        # 创建数据记录
        record = {"Model": model_name, "Benchmark": benchmark_name, "Execution_Time": execution_time/100}
        # print(record)
        dftmp = pd.concat([dftmp, pd.DataFrame(record, index=[0])])

    # 计算当前模型的平均值并添加到数据集中
    mean_record = {"Model": model_name, "Benchmark": "Mean"}
    for metric in dftmp.columns[2:]:
        mean_record[metric] = dftmp[metric].mean()

    dfall = pd.concat([dfall, dftmp, pd.DataFrame([mean_record])])

# 计算时间的减少率
dfall["Time_Reduction"] = 0.0
ref = "64K TSL"  # 参考模型名称

# 遍历所有基准测试
for bm in dfall["Benchmark"].unique():
    m = "Execution_Time"
    # 获取参考模型的时间值
    tage64ksc_time = dfall.loc[(dfall["Benchmark"] == bm) & (dfall["Model"] == ref), m].values[0]
    # 计算time减少率
    dfall.loc[dfall["Benchmark"] == bm, "Time_Reduction"] = (tage64ksc_time - dfall.loc[dfall["Benchmark"] == bm, m]) / tage64ksc_time

# print(dfall)

# 绘图代码
width = 0.7
cw = 11.5
fs = 12

fig, axs = plt.subplots(1, 1, figsize=(cw, cw * 0.2), sharex=True, sharey=False)

_bms = [b[1] for b in bms.items()] + ["Mean"]

x = np.array([x_ + 0.3 if l in ["GMean", "Mean"] else x_ for x_, l in enumerate(_bms)])

colors = {
    '64K TSL': '#8ECFC9',  
    "512K TSL": '#FFBE7A',
    "LLBP": '#FA7F6F',  
    "LLBP-0Lat": '#82B0D2',  
}

plot_models = [
    "64K TSL",
    "LLBP",
    "LLBP-0Lat",
    "512K TSL",
]

nbars = len(plot_models)
bar_width = float(1) / float(nbars + 0.5)
init_offset = float(-nbars * bar_width) / 2
get_offset = lambda n: init_offset + n * bar_width

ax = axs
m = "Execution_Time"

for i, model in enumerate(plot_models):

    # if i == 0:
    #     continue

    dftmp = dfall[dfall["Model"] == model].set_index("Benchmark")

    y = dftmp.loc[_bms, m].values
  
    bars = ax.bar(x + get_offset(i), y, width=bar_width,
                  color=colors[model], label=model,
                  align='edge', edgecolor='k', zorder=2.3, alpha=0.6)


ax.yaxis.set_minor_locator(mticker.AutoMinorLocator(2))
ax.grid(True, which='both')
ax.grid(True, which='minor', linestyle=':')

ax.set_ylabel("time", fontsize=fs)

_y = ax.get_yticks()
ax.set_yticks(_y)
ax.set_yticklabels([f"{y*100:.0f}" for y in _y], fontsize=fs-1)

ax.set_xticks(x)
ax.set_xticklabels(_bms, rotation=10, horizontalalignment="center", fontsize=fs-1)
ax.tick_params(axis='x', which='major', pad=0)


#ax.set_ylim(bottom=-0.0, top=0.8)


handles, labels = ax.get_legend_handles_labels()

ax.legend(handles, labels, bbox_to_anchor=(0.98,1.03), loc="upper right", fontsize=fs, ncol=8,
            labelspacing=0.05, columnspacing=1.,handletextpad=0.2,borderpad=0.2,frameon=True)

ax.set_xlim(left=x[0]-0.8, right=x[-1]+0.8)

fig.tight_layout()

fig.savefig("time.pdf",dpi=300,format="pdf",bbox_inches='tight', pad_inches=0, facecolor="w")
