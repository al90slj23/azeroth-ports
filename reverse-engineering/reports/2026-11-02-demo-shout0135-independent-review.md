# 固定135 Demo Shout组件：异作者只读独审

[最终180例／207阶段](../evidence/demo-shout135-oracle-20261101T204357.749953Z/comparison.json)通过限定范围独立复核，主收据 SHA **`ab48f8c30461793af8f0b93579b53bc8f9abc30671f85a8c902575a58e9dbe95`**。固定原件0.135.1／实际9字节build `90898d5e3`，WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`；旧`0898d5e3`是历史alias。

本审阅由未编写demo cast组件的作者完成，不执行原件、生产模型、原checker或builder。审阅者另编写了后续demo_ai135，因此**本文不自审该AI实现**；AI应由另一作者审阅，其中共享4543的cast来源可以引用本独审，避免把共享代码作者的重算误称异作者验证。

27份冻结/当前源在成功审阅两端SHA一致，22份production由独立AST闭包确认，78条本地依赖边完整。所有production禁止文件读取、动态执行和子进程调用。私有WASM仅增加922/1076/2244/21455和stack export，其余section、原body/callee/data与固定原件逐字节一致。9个原函数定点WAT经RO SQLite seek与二进制body/SHA核对，不全文读取WAT。

## 独立恢复与逐阶段重比

**21455完整16B合并。** 独立使用struct binary32和有序比较重建primary过期晋升、incoming优先级、fallback候选资格及稳定tie。134次直接原helper的全部**536个词按bitwise一致**，包括signed0、±Infinity与NaN；审阅器没有沿用原checker允许的NaN仅分类相等捷径。每次before16/after16原始字节也绑定到输入/连续状态。

**2244完整effect11。** 独立按第一个GUID且marker≠1的目标应用，两槽更新后仅在主槽接受当前strength/deadline时写duration364，完整spell360更换先写新ID，再remove旧非零Aura并add新Aura。marker2在此入口与31732的无效record路径分开；missing GUID与dead-first duplicate GUID均按原范围保留，不推广为所有其它effect分支。

**4543空U240 Aura。** 审阅器没有调用生产`_aura`：自行重建16槽first-remove/firstempty-add、已有/满槽不产生packet，以及79+slot、99+group的nibble2 flags与121+group的空ability应用数。自行编码packed GUID、字段mask与完整169字节。实际**119个新Aura169，共4,403B**；逐阶段累计队列观察为**153包／5,661B**，两者分开，不把153当作新事件。

**完整922与1076限定组合。** 独立恢复移动插值、稳定半径排序、radius14边界、base damage的逐指令binary32顺序、126次共享critical RNG抽样、117次实际非致死914伤害与class1原静态+80 leech、caster HP及22/28字段。另有9次phase拒绝damage但仍执行effect的真实分支。三套attempt ledger、owned/basic80词、owned成功cooldown／0.2秒retry、NaN和Infinity countdown、保持Infinity的class prelude timer逐阶段重算。

32次外部922、21次外部1076、20次外部2244及134次21455合计207入口；内部cast attempt44另记，不新增外部调用。整个投影74,648个已知值一致；9,328个未知物理字节均与原fixture的A5/5A原字节相同，未把None补零。完整424B的所有其它已知字节也比较，全部128..140与Aura词由独立状态演算产生，不读原件输出回填模型。

对原Game8192观测绑定RNG、f64 accounted total、HP、phase和timer；全部非Aura packet累计525次保留观察，其payload语义未扩张为已恢复。原动态输出只有已筛出的Aura子域被声明预测；物理BTree/allocator身份、完整Game写集与全部wire仍是边界。

## 输入与身份边界

末尾case使用独立665帧纯模型产出的selected demo80、23派生属性、HP/RNG/now，再手工放入3个near NPC、mode1/empty proc源与Infinity class prelude。相关外部片段SHA已核，**不是原件自然运行665帧**，也没有复制原件snapshot或把原world/全部技能/保存结构当独立生产。

真实原件PID46941 exit0／5.428秒／双missing；180 fresh实例、32MiB cap内、535次原件与allocator stack检查全恢复，实际host0。只读审阅owned PID3971 exit0／1.132秒／双missing，未新增原件case；审阅器本地源码前后快照见[源码来源](../evidence/demo-shout135-independent-review-owned-20261101T210700.766545Z/reviewer-source-provenance.json)。

[最终只读审阅收据](../evidence/demo-shout135-independent-review-owned-20261101T210700.766545Z/review/review.json) SHA **`33211f76462dc3708d29df764da5cff006ac64d6fcfbb40e505be768069b0f0e`**，详情见[JSON](2026-11-02-demo-shout0135-independent-review.json)。原主收据hash了准备输入和模块；本审阅另外逐文件绑定raw results/runtime/terminal等当前SHA，并明确是审阅时绑定，不覆写原收据或伪称原采集时已记录这些输出SHA。

两次失败的审阅器尝试均保留：210504把`const364+f32.store`误写为寻找`i32.store offset364`；210600错误假设owned wrapper的metadata.selected会暴露inner casttargets。修正为真实静态语法、只对direct cast核其selected metadata；owned仍独立重建并全量对照HP/RNG/424/ledgers/cooldown。210700从头完整复核通过，生产与原证据未改。这些审阅器失败不是原件失败或额外正例；先前fixture缺class leech的旧pilot也不与180计数合并。

当前仍不包含AI expiry／伤害调度的连续原件组合、非空44B NPC ability/15511、非空effect49/proc或死亡续接、全部wire与Game所有权、完整880、Windows原生执行或独立完整一局。135结果不外推新版。
