# 最后一级分支预测器模拟器

<p align="left">
    <a href="https://github.com/dhschall/LLBP/blob/main/LICENSE">
        <img alt="GitHub" src="https://img.shields.io/badge/License-MIT-yellow.svg">
    </a>
    <a href="https://github.com/dhschall/LLBP/releases">
        <img alt="GitHub release" src="https://img.shields.io/github/v/release/dhschall/LLBP">
    </a>
    <a href="https://doi.org/10.5281/zenodo.13197409"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.13197409.svg" alt="Trace DOI"></a>
    <a href="https://github.com/dhschall/LLBP/actions/workflows/build-and-run.yml">
        <img alt="Build and test" src="https://github.com/dhschall/LLBP/actions/workflows/build-and-run.yml/badge.svg">
    </a>

</p>



最后一级分支预测器 (LLBP) 是一种微架构方法，通过支持基线 TAGE 预测器的额外高容量存储来提高分支预测准确性。关键见解是 LLBP 将分支预测器状态分解为多个程序上下文，这些上下文可以被视为一个调用链。每个上下文仅包含少量模式，并且可以提前预取。这使得 LLBP 能够将大量模式存储在高容量结构中，并仅将即将到来的上下文的模式预取到一个小的、快速的结构中，以克服高容量结构的长访问延迟。

LLBP is presented at [MICRO 2024](https://microarch.org/micro57/).


此存储库包含用于评估 LLBP 预测准确性的分支预测器模型的源代码。该代码基于 [CBP5 框架](http://www.jilp.org/cbp2016/)，但经过大量修改和扩展，添加了各种统计数据，以评估 LLBP 和基线 TAGE 预测器的性能。


该框架的目的是提供一种快速方法来评估不同的分支预测器配置并探索 LLBP 的设计空间。它**不模拟整个 CPU 管道**，而只模拟分支预测器。

该框架支持通过为每个执行的分支和/或分支之间执行的 8 条以上指令对预测器进行计时来估计时间。虽然我们发现这种近似值对于了解后期预取的影响是相当准确的，但这只是一个粗略的估计。要获得准确的时间，预测器需要与完整的 CPU 模拟器（如 ChampSim 或 gem5）集成。


> 我们目前正在致力于将 LLBP 与 gem5 进行整合，一旦准备就绪，我们就会发布代码



## Prerequisites

基础架构和以下命令已通过以下系统配置进行了测试:

* Ubuntu 22.04.2 LTS
* gcc 11.4.0
* cmake 3.22.1

> See the [CI pipeline](https://github.com/dhschall/LLBP/actions/workflows/build-and-run.yml) for other tested system configurations.



## Install Dependencies

```bash
# Install cmake
sudo apt install -y cmake libboost-all-dev build-essential pip parallel

# Python dependencies for plotting.
pip install -r analysis/requirements.txt

```


## Build the project

```bash
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Debug ..
cd ..

cmake --build ./build -j 8

```

## Server traces


The traces use to evaluate LLBP collected by running the server applications on gem5 in full-system mode. The OS of the disk image is Ubuntu 20.04 and the kernel version is 5.4.84. The traces are in the [ChampSim](https://github.com/ChampSim/ChampSim) format and contains both user and kernel space instructions. The traces are available on Zenodo at [10.5281/zenodo.13133242](https://doi.org/10.5281/zenodo.13133242).

The `download_traces.sh` script in the utils folder will download all traces from Zenodo and stores them into the `traces` directory.:

```bash
./utils/download_traces.sh
```


## Run the simulator

可以使用以下命令运行模拟器，并将跟踪文件、分支预测器模型、预热指令数量和模拟指令数量作为输入。

分支预测器模型可以是 `tage64kscl`, `tage512kscl`, `llbp` 或 `llbp-timing`.
> 分支预测器模型的定义在 `bpmodels/base_predictor.cc`

```bash
./build/predictor --model <predictor> -w <warmup instructions> -n <simulation instructions> <trace>
```

为了方便起见，模拟器包含一个脚本，用于针对给定分支预测器模型的所有评估基准运行实验 (`./eval_benchmarks.sh <predictor>`).

结果以统计文件的形式存储在 `results` 目录中。请注意，模拟器每执行 5M 条指令后就会打印出一些中间结果，这有助于监控模拟的进度。


## Plot results


Jupyter 笔记本 (`./analysis/mpki.ipynb`) 可用于解析统计文件并绘制不同分支预测模型的分支 MPKI。

Mispredictions Per Kilo-Instructions 是一个用于衡量处理器分支预测器性能的指标。它表示每执行 1000 条指令时发生的分支预测错误次数。在现代处理器中，分支预测用于预测代码执行中的条件分支，以保持流水线的连续性。如果预测错误，处理器需要清除错误路径中的指令并重新获取正确路径，这会导致性能下降。

为了重现与论文中类似的图表（图 9），我们提供了一个单独的脚本 (`./eval_all.sh`)，该脚本针对所有评估的分支预测模型和基准运行实验。


> *Note:* 由于我们在论文中将 LLBP 与 ChampSim 结合起来，因此结果可能与论文中呈现的数字略有不同。

该脚本可以按如下方式运行:

```bash
./eval_all.sh
```
运行完成后，打开 Jupyter 笔记本并点击运行所有单元格。



## Code Walkthrough

**Misc:**
*  `main.cc` 文件包含模拟器的主入口点。它读取跟踪文件，初始化分支预测器模型，并运行模拟。
*  `bpmodel` 目录包含 TAGE-SC-L 和 LLBP 分支预测器模型的实现。

**TAGE:**
* TAGE-SC-L 分为 TAGE 和 SC-L 两个部分。代码取自 CBP5 框架，并经过修改，添加了额外的统计数据以评估分支预测器。
* 512KiB TAGE-SC-L 的唯一区别是 TAGE 预测器中的条目多了 8 倍。

**LLBP:**
* LLBP 源自 TAGE-SC-L 基类，并重写了几种方法来实现 LLBP 功能。
* LLBP 有两个版本：`llbp` 和 `llbp-timing`。两者功能相同，但后者对模式集的预取进行建模，可用于研究后期预取的影响。
* 高容量 LLBP 称为`LLBPStorage`，用于存储所有模式集。`PatternBuffer`是一种小型、快速的结构，用于存储即将到来的上下文的模式。
* `RCR` 类实现了计算程序上下文的所有功能。


## Citation
If you use our work, please cite paper:
```
@inproceedings{schall2024llbp,
  title={The Last-Level Branch Predictor},
  author={Schall, David and Sandberg, Andreas and Grot, Boris},
  booktitle={Proceedings of the 57th Annual IEEE/ACM International Symposium on Microarchitecture},
  year={2024}
}
```

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

David Schall - [GitHub](https://github.com/dhschall), [Website](https://dhschall.github.io/), [Mail](mailto:david.schall@tum.de)

## Acknowledgements
We thank all the anonymous reviewers of MICRO and the artifact evaluation team for their valuable feedback. Furthermore the members of the EASE-lab team at the University of Edinburgh as well as Arm Ltd. for their support and feedback.