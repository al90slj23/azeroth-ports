# 固定138：连续流程迁移入口与可执行准入

已为官方0.138.0／`382771e6c`定位13个流程入口，并新增可执行source／body／signature guard。此层是静态迁移基础，**不代表138连续流程通过**。实际运行的138属性组件另见[10,569例新差分](2026-11-02-stats0138.md)。135既有750帧、原件snapshot和通过次数均未转计。

| 角色 | 固定135 | 固定138候选 | 主要变化 |
|---|---:|---:|---|
| Game构造 | 1560 | 1571 | 同三参数ABI；body7242→7069B，输入profile与构造写集需逐项恢复 |
| 带缓存world构造 | 6730 | 6760 | 同双参数ABI；body22481→15613B，不能恢复旧版内存来运行新版 |
| 开局 | 1089 | 1087 | 同单参数ABI；body和引用数据改变 |
| 属性 | 1512 | 1512 | 完整opcode序列相同；timed ptr/count600/604→596/600，reserve768→764 |
| 玩家逐帧 | 2088 | 2086 | 完整opcode序列相同；衰减pool756→752 |
| 拥有技能调度 | 1076 | 1232 | body9730→7133B，frame208→224B；需重新恢复调度 |
| 实际施法 | 922 | 916 | body23288→25177B，不能套用同号922 |
| 额外计时施法 | 916 | 917 | opcode骨架相同，callee／常量仍需核对 |
| 玩家Aura | 1202 | 1155 | body6561→7112B，有实际指令／来源变化 |
| 单位AI | 921 | 919 | body与调用结构改变，Unit stride432 |
| 刷怪 | 947 | 946 | Unit424→432及尾部字段迁移 |
| 拾取 | 2862 | 2862 | 控制骨架相同，奖励callee需迁移 |
| 选卡 | 1072 | 1072 | 36B definition tag阈值55／54→59／58，不能只搬地址 |

[core收据](../evidence/flow135-to138-core-static-20261101T230745.455530Z/mapping.json) SHA `038eea903cd28433582e7c6d92f5dd686828aa62fedfd13930175f842ac535b9`；[consumer收据](../evidence/flow138-consumers-static-20261101T230740.134611Z/mapping.json) SHA `78793903582b10ad7455bfc0853eb182872bb64bdd4ef1b9900fbd03ecb7944e`。共有限seek6,048,028B WAT，没有读取整份1.32GB WAT或重新建立profile；全部原件／模型运行计数为0。完整raw body／WAT／callee差异保留，规范化仅作定位，不能作为行为等价证明。

[verify_flow138_contract.py](../scripts/verify_flow138_contract.py)实际重新解析固定138原件，核13个角色的精确body SHA及完整参数／返回签名。[guard收据](../evidence/flow138-contract-guard-20261101T231438.634673Z/guard.json) SHA `b94e37029c093a73c410da24b0ceba781227a3f68243573a3ccbea8fb169f456`。独立常量文件不读取原件，也没有把静态准入标为运行支持。

1512引用的class HP／armor及8种race modifier向量在两版本逐字一致。138 Windows EXE中9种实际class HP／armor的8B组合各有唯一文件位置，间距144B；WASM相关class指针间距88B。这只是scalar数据组织的静态对应，未证明native class完整布局、函数ABI或Windows游戏执行。

最初static producer误用138固定parser解析135字节，正确触发function-count guard；[失败目录](../evidence/flow135-to138-core-static-20261101T230730.663255Z/failure.json)保留。修正后分别调用各版parser，未覆写旧目录，没有因此放宽source SHA或函数数量限制。

下一实际阻碍是138 constructor1571的输入profile／默认写集、缓存world6760的真实所有权和bootstrap、owned1232／Aura1155的来源变化，以及所有Unit432适配。官方Windows仍作native数据与平台行为主参照，Web静态或函数差分不冒称Windows运行。此任务仅新增文件，未修改135核心、登记表、安装包或存档。
