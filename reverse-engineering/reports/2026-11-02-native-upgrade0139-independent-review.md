# 当前139原生升级标量／完整WASM25511：不同作者只读独审

结论：2150套同源逻辑fixture的Native原始513B指令仿真与完整WASM25511保存结果，在五kind／五tier、当前114技能定义的count标量、显式uint32和IEEE binary32输入域内通过独立复核。Windows整应用、完整Native ABI及游戏主循环均未验收。

评审没有执行作者模型／builder／checker／runner，也没有导入Unicorn或执行任何原件。独立解析当前PE32+、exception目录／.pdata、15原始页、513B及108个LLVM／Ghidra边界；从原PE和WASM读取五组表及实际114份声明，按slug和execution匹配。私有WASM除了export段以外逐字节不变，25511完整body／WAT／签名绑定；无隐式start段。

使用此前独审的通用Fraction IEEE解码／舍入函数，另写每步float异常及五规则，在读取两引擎结果进行比较之前独立计算每套fixture。2090例严格result bits匹配；另外60例属于NaN输入关联，作者只验结果分类，原存结果全部为+0。输出为1840 finite、290 zero、20 infinity，NaN输出0；不得把60称为NaN输出，也不承诺NaN payload／sign等价。

独立重建分支计划，逐项核48335条已保存PC trace、94／108个实际指令边界、13750次数据读／67090B，连同PC、地址、宽度、来源均一致。每个partial owner仅初始化实际消费的4B字段，kind2另加8B definition pointer；114840个None字节均未读取。全114份定义只验证kind2数量上限标量，不代表114技能行为恢复。

三次负向guard独立核对：未初始化owner读、kind5越界跳表读、tier5到外部CALL前均被拒绝，不是三条有效原函数行为case或panic执行。Native映射数据只读，所有guest写及外部CALL／syscall被拒绝；执行限513B原边界，到RET sentinel结束，1秒／2000条指令预算。原页面、owner、64KiB栈守恒及nonvolatile寄存器保存来自冻结instrumentation源码检查和原件返回flags，没有保存前后原始内存pair可由本次重新逐字节对比。WASM每次4096B owner页／SP守恒，域外32MiB只保存batch hash相等bool；不扩大为中间内存状态证明。

Unicorn2.1.4官方wheel SHA及安装的Python／dylib字节经zip比对，未加载库。最初Native pilot SIGILL／-4保留，Native0行／runtime缺失，结果未知；当时13个WASM保存结果单列。sandbox两NOP探针在created后SIGILL，同脚本的非sandbox探针正常到0x100002，只证明仿真能力环境，不能算游戏执行。后两批13套成功pilot也排除在正式2150外。

一套fixture分别驱动Native仿真2150次和WASM完整25511入口2150次，不能称4300个独立fixture。Native每case全新emulator，WASM是1个新实例重用受控页。14源／14导入边全部绑定；本批不存在“source8852”字段。作者Native／WASM／guard三个owned进程均正常终止；本评审PID8870正常退出，PID／进程组均不存在，源前后SHA一致。

正式只读证据：`evidence/native-upgrade139-readonly-review-20261102T125925.523004Z/review/review.json`。作者7件、原件安装包／存档及其他冻结件不变；公共登记、Git与Android改动0。完整选卡应用、伤害／AI／网络／存档／bootstrap／WindowsApp仍Pending。
