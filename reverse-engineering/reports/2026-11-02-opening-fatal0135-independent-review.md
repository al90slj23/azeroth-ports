# Fixed135 连续移动至死亡：异作者只读独审

最终第四批在限定域内通过：**921 帧、7 次选卡、44 次移动输入、12,945 个阶段、13,870 条 CAS 记录**全部读到结束。独审没有运行 production、作者 checker/builder、原件 WASM 或本地客户端，新增原件调用为 **0**。这是一条真实同状态的受控死亡流程，尚不代表完整游戏重造完成。

- 作者原件比较：[第四批 comparison](../evidence/opening-combat0135-oracle-20261102T012524.271526Z/comparison.json)，SHA `430e764bfc0b556bf33489796ed04e96da8e1f4f0aedbcc4bee8217b67967160`。
- 独审程序：[review_opening_fatal135.py](../scripts/review_opening_fatal135.py)，SHA `d2cf6093815de7eb8497de6400630a7fd90acffaa08e80bd3114e563dd418e06`。
- 完整独审收据：[review.json](../evidence/opening-fatal135-independent-review-owned-20261102T013810.490178Z/review/review.json)，SHA `c456646eb66da5e9b610e600c14a705ab8704cc49cc25d6b3ef33e02c2f4796a`。
- 结构化结论及失败链：[独审 JSON](2026-11-02-opening-fatal0135-independent-review.json)。PID 17503 正常退出，耗时 152.65 秒，PID/PGID 均不存在；外部期限 900 秒。

## 输入域与证据来源

对象是固定 **0.135.1 / c62c85f5…** 原件；human/warrior、Elwynn、seed 0、object ID 42，显式空研究 profile。实际 snapshot profile 在任何 fixture 写入前读回，rank count/flag、19 个装备和 name length 均符合空输入条件。constructor 实际 phase 0，随后真实 1089 进入 phase 1；Game hero 的实际 String header 为 `0/1/0`，空串由 profile producer 与原始 header 共同约束。

Game 位于 typed partial App 的 `App+16`，App/network tag 均显式为 2。每帧的时间由外部控制器写入 G2352，再调用真实的 14 个入口；原件共有 12,947 次导出入口调用。此批没有自然 1371、完整 880、原生客户端执行，也没有把 latest138/139 的证据移入 fixed135。

130 个冻结源、113 个 production 源和 614 条有效本地导入边完整闭合；独审自身包含 17 个 reviewer 源。独立解析原始 WASM 的函数身份，并重新绑定 18 个函数的索引 WAT。世界查询独立读取固定原件 snapshot 的真实输入，非 fresh world/cache/Rc producer；primary absent，不能给予 nearest-primary 动态覆盖。

## 独立重算的行为

从每个 AI 前的实际单位、轨迹、时间、属性与完整 source vectors 重建有序 contact 队列，逐次执行 binary32 运算。267 次 contact 中，19 次被有效 raw12 保护拦截，248 次进入实际 history 追加；这些是重算诊断数量，不是新增 267/248 个原件组件 case。source GUID 均来自真实匹配单位，原件 contact flag 为 1；没有复用早期 GUID 0/flag 0 绕过 callbacks 的验证域。当前 raw13 非正、item8/modifier36 来源为空，post-history callback 的窄谓词由既有异作者独审依赖约束。

合法 special64 guardian 按实际三 timer owner 分区：2,884 次 idle/no-contact 输入由 921 的 raw108、HP、home/player 距离谓词独立证明，没有笼统把整个单位数组当成 ordinary。guardian engage/技能、受伤 guardian 和实际 guardian 死亡仍不在此域内。

48 字节环独立经历 6 次扩容、248 次追加、176 次裁剪，最终 **capacity 128、head 48、count 72**。完整 backing 的已知 scalar/length/rank/padding 保留规则和 active 字符串逐项核对：17,749,802 个已知 backing 字节观测匹配，10,896,598 个 pointer/allocator 未知字节观测保持 `None`。原件指针和完整 backing 是被核对的物理观测，没有反填 production。

从真实 alive→dead 变化独立累计 109 个 ordinary kills；earned 与实际可用 gold 增量一致，为 115。结算为 level 8、elites/guardians/bosses/chests 均 0。damage/taken 的 JSON 值为 11221.293 / 754.159；完整 f64 与原始序列化字节保存在收据中，未以这些显示小数替代精确值。

致死发生于 **0-based frame 920，即第 921 帧，AI stage 12939**。时钟为 binary32 的 92.09916687011719 秒；Young Wolf 的原始攻击 3.841827154159546，经属性减伤为 2.9966251850128174，history 保留 prefix HP **-1.8937066793441772**，最终 Game HP 为 0。1367 使用另一个作者已独审的纯 reference，在独立核过其消费字段后生成相同 recap：72 条记录、47 个合并 hit groups、3 个 source groups；recap capacity 2610，完整 defeat JSON 为 1,875 字节、capacity 3748，逐字节匹配。不能把本人曾编写的 production1367 再算一次独立恢复。

## 221 的真实来源及死亡后的尾续

同一次 921 调用新增的 opcode 顺序为 `170×3 → 221普通移动 → 330命中 → 221停止×10`。

- 普通移动来自 **921→27457**，先于 incoming drain：48 字节、capacity 64、sequence 1136、duration 2380ms。格式为 packed GUID、XYZ12、sequence4、flag0、u32(256)、u32(duration≥1)、u32(1)、endXYZ12。
- 停止格式由 **45845** 绑定：精确 `1+popcount(mask)+17` 字节，末 flag 1。本例十包均 24 字节、capacity 32，sequence 1137…1146；独立 world Z、位置、停止后的单位字段和真实新增 queue tail 对齐。

因此不能仅凭“phase1→4 调用里所有 221”就把它们全部归为死亡停止包。第四批只按真实 wire grammar 分类，完整 ordinary 包和 all-packet queue 均保留；没有用 expected payload 筛选 actual。

同一 Game 随后实际完成 `collect2862 → claims2573 → spawn947 → special2376 → terminal49037` 五个 phase4 阶段，HP 0、暂停时间和 defeat 通知保持；没有一律跳过这五个函数。模型下一次 frame 返回 not_running，原件重放的 921 次输入全部完成，原件 case_end boundary 为 null；这不能写成已执行 950 帧或死亡后的下一帧 880。

## 失败记录和限制

前三批均保留：首批 case_end 发出 logical-budget 错误，先前未输出的 boundary 原因为 unknown；第二批触及 unique-blob 512MiB 限制；第三批完成原件和比较，但有 72 个 capture 分类差异，仍为失败。第三批的 1 个普通 221 被误归入 stop-only projection，第四批修采集 schema 后重新 fresh 验证，production113 源和独立预期规则未变。独审确认前两批解压预期 SHA 均为 `bd026bac03cae8b39a4fb6e5088ac0c4c848a12c138faba6cc975e55e5a4b627`，各自 gzip 文件 SHA 不同；最终完整预期也有相同逻辑 SHA。

独审自己的首轮也保留：过强的全数组 ordinary 断言拒绝了第 200 帧首次合法 guardian；修正为实际 owner 分区与真实 idle 谓词后，对同一最终 artifact 全量重新独审。没有重跑原件或改作者源码。

最终 CAS 全部 blob、引用次数和逻辑 SHA 完整 finish：50,470 个 blob、559,062,917 字节唯一 blob、8,573,768,533 字节逻辑记录。所有声明 projection 和完整 storage 的已知字节重比通过；unknown 没有补零。live922 caller scratch 的数值 producer、物理 packet allocator/queue header 和完整 17119 heap return 仍未恢复；opaque source 注释不能变成已预测值。完整 ordinary AI/技能仍依赖已有独立预期与原件差分，此 reader 没有另写一套完整 AI。上述有限结果不支持“全部游戏行为已还原”的结论。
