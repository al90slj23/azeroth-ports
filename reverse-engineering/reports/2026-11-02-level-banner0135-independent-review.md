# 固定135 level banner：93例／110次完整4630独立复核

最终93例受控组件证据通过只读独立复核。审阅者不是该模块作者；没有运行原件、生产模型或原checker，没有修改20份冻结源、原收据或primary报告，也没有新增原件用例。

- 原[comparison](../evidence/level-banner0135-oracle-20261101T194550.118916Z/comparison.json) SHA：`4cd02d8adf74d4129e58040b3a81bd2dac1b96e2eed8ff4bb5c1e67a6561a4e3`。
- 最终[review.json](../evidence/level-banner135-independent-review-20261101T195147.952310Z/review.json) SHA：**`1b3014d52043a70f283709567f36d14b3ee14ae6b1b9621ec802165809e31f13`**。
- [复核脚本](../scripts/review_level_banner135.py)与[机器报告](2026-11-02-level-banner0135-independent-review.json)记录源、输入、输出、静态证据、进程和范围。

实际93个fresh实例执行110次完整4630。复核5,696个严格known值，全部状态投影与150 payload无None或wildcard。**146条growth＋26条DoT＝172条实际新增事件**；逐call重复捕获的累计队列比较为186个150／16,528B，不能记为186条新消息。

## 独立语义核对

本批stat-source vectors明确为空，owned选择记录单独提供。审阅器从原WASM静态class/race records读取数据，在这个有限输入域独立复算全部23项derived、XP wrapping/threshold/120cap、HP与每级heal、aux pools、speed及已知keyed fields；然后同时要求独立数值结果等于冻结expected、冻结expected等于原输出。没有调用被审生产模型，也没有把它的recalculate当独立复算。候选卡metadata仍以原先冻结expected与原输出作严格比较；两次eligible choice额外验证了真实RNG序列，共12draw，未声称另写了候选生成器。

146个逐级old/new1512状态连贯且与初始输入、各call实际endpoint一致。增长取原顺序的binary32运算：

```
damage = f32(f32(new1540-old1540)*100)
health = f32(new1536-old1536)
regen  = f32(new1576-old1576)
```

审阅器用精确binary32值转Decimal，再独立执行signed fixed0／0／2、ties-to-even，重建完整文本及type10 payload；不复用模块格式化函数。实际文本有`+9`和`+10`最大生命值增量，不能硬编码`3/9/.08`。14次multi-level call保留每个中间状态与包序，4次无升级call不新增banner，初始120的两次call也不新增。这里只覆盖实际146次有限数值，不证明全部Rust浮点格式或所有tie边界。

owned80的definition pointer来自显式输入，审阅读取原静态definition byte84，核对`==6`后才允许DoT提示；同时必须满足新1608大于旧1608。实际26条提示发生于升到15／30／45，堆叠上限为`min(new1608,3)+1`。有DoT技能但未过阈值、过阈值但只有cleave的负控制均没有提示。

WAT4630的原顺序是old1540/1536/1576/1608捕获→1512→growth28964→可选DoT28964→10847 heal→下一level；phase2587与choice flags的2159 guard在level循环之后。12次非零choice flags且实际升级的call仍发growth，不能把末尾选卡条件当UI抑制条件。

150 serializer由完整原28964执行，独立重建并逐字节比较：type10:u8、zero:u32、zero:u64、UTF8长度含NUL:u32、UTF8文本、两个末尾NUL。英文与简中均按UTF8字节长度核验，含全部186次累计payload观察的顺序与内容。

## locale与原件来源

两种template均来自原WASM memory初始零与全部active data segments依序覆盖的静态image。审阅重新读取language table `5212184+28*index`：EN index0、简中index11，核对dictionary SHA、growth/DoT keys和原格式描述。没有从原输出文本倒造expected。

runner只提供显式default/override selector `14384328`、`14384320/24`，不写Once `14384344`或注入dictionary。原19964检测Once并自然调用82070：92个有升级case冷0→3，唯一初始120case两次调用均保持0。EN47例、简中46例；其它语言未验收。

固定原件SHA为`c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`，build为实际9字节`90898d5e3`，历史8字节alias `0898d5e3`单独保留。私有模块只追加4630及原global0观察出口，所有其它section与所有原函数body/callee字节未改；没有隐式start或替换callee。

20份frozen与当时current源SHA在复核首尾一致。其中12份production源码没有文件/host/动态执行入口。旧helper会在import-time哈希读取`run_level_cycle135_oracle.mjs`与`full135_host.mjs`，最终20-source闭包包含了这两个未执行JS输入。旧18-source收据仍保留，closure correction绑定其与final的input/expected/labels/module/static/manifest/results逐文件相同，不累计旧批。审阅后root获准继续集成；这里不作永久current-source一致声明。

静态复核通过RO SQLite seek七个有限WAT窗口，核body/signature、原字节与caller顺序；没有扫描整1.3GB WAT。原始input/expected/labels、manifest、runtime、stdout、stderr及process receipt均计算SHA，见[static proofs](../evidence/level-banner135-independent-review-20261101T195147.952310Z/static-proofs.json)和机器报告。

## 进程与范围

原件PID/PGID53737已exit0，二者missing；4.286秒/60秒deadline。878个deny imports、实际0host，281条allocator/entry stack检查均返回并恢复1048576。WASM cap32MiB、peak20,578,304B，Node heap512MiB，输出3,746,021B；单行2MiB、累计16MiB预算满足。expected在原件启动前生成并冻结；未调用Appstart、网络、EXE、用户存档或原件snapshot。

审阅PID/PGID65608已exit0，二者missing，2.495秒/60秒deadline。[终态](../evidence/level-banner135-review-owned-20261101T195147.751309Z/process-terminal.json)与两个审阅断言修正的失败终态保留；这些只读检查不构成新的原件用例。

完整8192B Game前后快照仅作观察，投影数值另与raw Game字段绑定。全部Game写集、physical keyed-tree/packet owner分配身份及非150 payload没有独立预测。输入为手工已知Game8192/显式空stat sources与有限owned记录，不是真实constructor生产。未知locale、非finite Rust格式、未覆盖有限格式边界、完整主循环/完整游戏/native仍pending；650流程尚待新UI集成复验，本组件和本独审均不把它记为通过。
