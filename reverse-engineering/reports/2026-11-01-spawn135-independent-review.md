# 0.135.1 三批生成模型独立只读审查

结论：在各自声明的平地、空peer、记录/计时器投影范围内通过复核。motion 5,068、Boss 871、elite 549，共 **6,488 个既有fixture**；从各批冻结source snapshot重新运行纯模型，与保留预期全部相同，再独立比较既有原件结果，没有超出既定NaN策略的差异。审查没有执行原件、修改作者源或共享builder。

原始WASM的90,959,080字节及SHA-256已重核。三个研究模块除export section7外逐段字节完全相同，原导出保留，新增角色与函数body SHA吻合，原件无隐式start section、878个import均为函数。各批source snapshot、fixture/results/runtime等artifact哈希均吻合。motion的当前builder/host与旧快照不同，符合后来扩角色；历史快照及已执行模块字节保持有效。

Boss唯一地址归一化是实体U248的allocator指针，按canonical0比较；其全部冷却payload另行回读并比较，计数、capacity、ability定义指针及其余424字节均参与比较。没有发现以指针mask隐藏计时器或实体内容。作者的Boss/elite字数统计把列表当一个比较项；本次递归逐叶计数分别309,680/333,473，不代表作者遗漏列表内容。

motion有80处NaN payload或sign位差异，现策略按NaN分类接受；“0差异”不代表这些NaN逐bit相同。checker代码顺序显示预期先于原件子进程生成，纯模型不读取原件或旧结果，冻结模型重算也重现全部预期；本次只读审查不能单独证明历史墙钟时间。

另检查了grid/pathfinding pending、16次失败后的fallback pending、其他事件到期拒绝、非有限时间拒绝、畸形实体记录拒绝。实际947的elite到期/候选/配对偏移与deadline，以及Boss一次调度、最终Boss额外0.6和endless300秒分支，与生产模型吻合。

这三批没有恢复地形寻路、Boss/elite AI、UI广播、对象注册表、特殊spell对象或联机包字节。farthest static point fallback保留静态规格但不作为动态验证成果；整体重造目标仍未完成。完整审查数据、独立复算脚本及逐段原件身份见 [review.json](../evidence/spawn135-independent-review-20261101T044947.975435Z/review.json)。

来源冻结补充：本报告引用的旧receipt仅冻结当时列出的文件，没有单独记录执行包入口 `core_spec/__init__.py` 的SHA。当前该327字节入口仅导入已在旧清单中的upgrade_values，但不能据此证明历史入口字节；旧计数保持原范围，不自动升级为本轮含包入口的33源证明。原receipt与旧review证据未修改，补充来源见 [package-init provenance caveat](../evidence/owned-cast0135-independent-review-20261101T045826.625090Z/previous-source-provenance-caveat.json)。
