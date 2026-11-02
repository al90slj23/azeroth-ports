# 0.139.0 Native 升级标量：真实指令仿真与 WASM 双原件差分

Windows 0.139.0 原件中 `0x145f64cc0..0x145f64ec1` 的513字节未修改机器码，已在 macOS arm64 上用官方 Unicorn2.1.4 实际执行；同一2150个受控输入也进入仅增导出的完整当前 WASM25511。两种原件分别与执行前冻结的 Fraction/binary32 独立规格比较，27911项断言0差异。这里没有启动 Windows、EXE、Wine 或完整游戏。

## 正式收据和计数

- 2150个唯一逻辑fixture；Native实际指令仿真2150入口/2150个fresh emulator；完整WASM25511入口2150/1个fresh instance。不是4300个唯一fixture。
- 五种kind、五种tier共25组合；计数转换边界、浮点阈值前后ULP、正负零、subnormal、极限有限数和Infinity。60个NaN输入只比较结果分类，其余2090个严格比较结果bit并比较两原件bit。
- count分支真实读取全部114个definition，每个5tier×count0/1/2；普通cap12边界及实际exec11四个特殊名称cap2/其他exec11cap0均覆盖。没有把114个技能的行为算成已验证。
- Native实际48335条指令、13750次数据读/67090B，94个有效指令边界（静态108个）；114840个未知owned字节未被消费。整个受控owner页、64KiB栈、15张原件PE页及Win64非易失寄存器每次都守恒。
- Native PID89185，exit0/2.30秒/PID与PGID均missing；WASM PID89212，exit0/0.31秒/PID与PGID均missing。三个拒绝探针由独立子进程捕捉，单独记录，不计作有效函数fixture。
- 原件Native SHA `0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274`；WASM SHA `71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299`。
- 正式目录 `evidence/native-upgrade139-full-20261102T124511.825553Z/`；comparison `cc2da65bc3266331971c5adee19c3576073982e12020b5016c7336052d9a3e2a`；expected先验prepared `b7eafad241fc12f5d7134540a68cbb9db0db3c17a9bce82f4633363e129f912b`。14件源闭包前后和当前一致。

## 可执行标量规格

每步按binary32的round-to-nearest-even舍入。Native显式MXCSR=0x1f80，DAZ/FTZ关闭、异常mask开启。五条原件20B系数表在Native与WASM逐字节相同；表地址/精确u32值保存在JSON和manifest中。

| kind | Native consumed field | WASM field | 返回的标量公式（每步f32） |
|---|---:|---:|---|
| 0 | +36:u32 | +32:u32 | damage[tier] / (f32(counter) × .5 + 1) |
| 1 | +20:f32 | +16:f32 | cooldown[tier] × max0((field - .2) / .8) |
| 2 | +24:u32 | +20:u32 | f32(min(max(cap - count, 0), countTable[tier])) |
| 3 | +28:f32 | +24:f32 | radius[tier] × max0((5 - field) × .25) |
| 4 | +32:f32 | +28:f32 | duration[tier] × max0((6 - field) / 5) |

`max0`是原件MAXSS第二参数+0及WASM显式NaN/严格正值select的行为：NaN与非正数归零。不能从Ghidra的普通C max伪码忽略此NaN语义。kind2才额外读取owner+0 definition指针；Native实际120B definition的execByte117与WASM88B的execByte84按实际slug匹配。exec!=11时cap12；exec11且名称为seal_fate/soul_fire/lightwell/faerie_fire时cap2，其余cap0。名称fatptr/字符串仅在原件对应分支允许读取。

Win64入口以RCX=state、DL=kind、R8=tier（零扩展）初始化，读取XMM0低32位返回。这里只恢复实际消费的字段，64B是受控fixture尺寸，不宣称Native owned完整sizeof；其余字段None。WASM的80B/4096B页同样是受控fixture，并非真实App拥有对象。

## 执行约束与失败保留

真实x86引擎来自[官方Unicorn2.1.4](https://pypi.org/project/unicorn/2.1.4/)，macARM wheel SHA `d6c93e0f60328d8f4a1792af3f834137a28050fcc2305f2ec01efe8558a9844e` 经PyPI发布摘要核对；已安装Python/dylib字节与wheel逐文件匹配。venv、wheel、pipcache、tmp全部在4TB，未系统安装。采用[官方API](https://www.unicorn-engine.org/docs/tutorial.html)，没有自制指令解释器替代原件。

PC钩子只接受513B中的原始指令边界或RET哨兵；整页原件字节保留，页内其他代码不能执行。读钩子仅准许实际已初始化owned字段、必要definition/slug、原始表/常量、8B返回地址。所有guest内存写、外部CALL、syscall、陷阱、未知或域外读全部拒绝。每case指令/时间有界，子进程各120秒deadline。

三个先验拒绝探针分别证明：未初始化owner读被拒；kind5越过五项switch表的读被拒；tier5在原外部panic CALL执行前被拒。均返回Unknown而不是补零；guest writes=0。不是在验证原版非法输入/panic的最终行为。

第一次沙箱内原件pilot由Unicorn宿主SIGILL退出-4，0 Native行、无runtime文件，完整保存在 `evidence/native-upgrade139-pilot-20261102T123440.439019Z/`。该旧checker的zip缺陷令当时成功的WASM13未比较；本报告只读补核该批原先冻结expected/实际WASM13，13个bit相同，单列为事后诊断不转计正式。新checker分别核两引擎输出，避免一方缺行遮蔽另一方。

同一冻结2NOP能力探针沙箱内在内存映射阶段SIGILL，沙箱外成功完成map/execute；0原件函数调用。随后沙箱外两批pilot各13组0diff均保留排除在正式2150之外。初次pip DNS失败、官方网络下载、离线安装和全部PID/terminal也保留；没有把失败改成通过。

## 验证层和未知项

静态提取：当前PE头/.pdata/LLVM-Ghidra指令/原始513B、五系数表、114实际slug+exec的跨平台字节与字段映射。独立实现：纯Fraction规则，不执行Unicorn或WASM、不读取原件输出，期待先写盘并哈希。正式原件差分：Native指令仿真2150与完整WASM25511的2150入口。本文原始捕捉统计是事后作者诊断；异作者独立复核仍Pending。

WASM每次核4096B fixture页与SP=1048576，32MiB其余内存只保留批前/后hash一致标记，没有逐call外域hash。Native每个fresh emulator核全owner页/64KiB栈/15张PE页；只读许可与None守卫另由每次数据读捕捉证明。NaN payload/sign、CPU flags、XMM0高位及其他MXCSR环境不作通过声明。

本批不增加完整Windows应用、Native伤害/AI/主循环/联机、自然选卡应用或完整游戏流程的验证。完整Native Game/Unit/owned ABI、其他函数、tier域外原版语义仍未知；现有安装包和存档未动，封装与Android未动。
