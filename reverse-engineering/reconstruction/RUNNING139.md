# 运行固定139的独立研究入口

`run_headless139.py`把已有独立组件接成可运行命令：原始地图／模型文件 → 地形与碰撞／导航构造 → 默认角色与开局 → 刷怪、自动战斗、死亡、经验、首次选卡和继续战斗。入口只读取本地原始资源、资源身份清单及本仓库Python源码，使用标准库；原作EXE、WASM、内存快照及预解析world均不作为输入。

当前绑定 **0.139.0 / f79c5e2b4**。功能对齐目标仍为官方最新稳定版，当前版本登记见 [`version-support.json`](version-support.json)。本入口的结果按固定139保存，不转算新版通过。

在仓库根目录运行；以下路径对应本机已取得的固定139原始资源包，完整资源没有上传GitHub。输出目录必须是4T硬盘上的新目录：

```sh
python3 -B reverse-engineering/reconstruction/run_headless139.py \
  --asset-map reverse-engineering/originals/entry-assets139-20261102T022818.157124Z/resource-map.json \
  --acquisition-receipt reverse-engineering/originals/entry-assets139-20261102T022818.157124Z/receipt.json \
  --seeds 0 50 111 \
  --steps 110 \
  --output reverse-engineering/evidence/my-independent139-run
```

每步使用明确的时间采样，经已恢复的主循环时钟规则限制delta；110步约为游戏时间11秒。`--choice first`在真实三张候选出现时尝试第一张已支持的Thunder卡；`--choice pause`保留选择状态。遇到未恢复的卡、第二选择来源、怪物或事件时，输出实际停点和最后一个完整状态，不重抽、改卡或跳过事件。

结果保存在输出目录：

- `receipt.json`：源码与资源哈希、world哈希、实际停点和最终状态。
- `states.jsonl`：开局、每个已完成组件步及选择后的状态，保留物理容量、尾槽和未知字节。
- `world-progress.jsonl`：本次地形、导航和碰撞构造进度。
- `read-audit.json`：Python文件读取审计及拒绝项。这一层不是操作系统级全局审计。
- `source-snapshot/`：本次执行的本地Python源码。

首次构造需要读取451份实际资源、67,281,330字节并计算地图缓存，耗时与最终App帧率分开评估。此入口目前只执行2123→925→2890→952及声明范围的选择动作；实际完整884主循环、其余阶段、图形界面、渲染、音频、存档、联机与完整一局继续实现。现有Mac／Android安装包和存档保持原样。
