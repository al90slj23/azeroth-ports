# Fixed135 opening→500帧→资源生成只读独审

**通过声明范围的独审。** 固定 `0.135.1 / 90898d5e3`，单一human warrior、seed0、navigationFalse、静止输入，500帧、4次真实选卡、7004个阶段、7006次原件入口。本次没有执行原件、模型、checker、builder或资产producer；0新增original case、0完整880帧，不与400帧或64例组件求和。[最终独审收据](../evidence/resource500-independent-review-owned-20261101T182704.730013Z/review/review.json) SHA256 `cd9b122b6f004552c84d2efde8f8d61b313af9fb102cd010e8ee5887911d92e7`；[结构化报告](2026-11-02-opening-resource-combat0135-independent-review.json)。原[comparison](../evidence/opening-combat0135-oracle-20261101T181700.263141Z/comparison.json) SHA `2ce0181ba4f9303213d6038e9e0f5001c361dcddb771086b609ca96ff356dd71`，范围及独立raw资产入口另见[主报告](2026-11-02-opening-resource-combat0135.md)。

99份冻结源与审阅时当前源SHA全部相同，86份生产文件恰好形成AST导入闭包，未发现直接文件或动态代码执行调用。私有模块只追加已声明的entry与stack export；所有非export段保持原件字节，callee没有替换。实际phase1、六类opening物理向量、容量和None继续保留；未新增zero128或清空非空owner。

完整重建7508条CAS逻辑记录、2,437,042,742B，逐条验证逻辑SHA及最终滚动SHA `1d3cf9e46f594e2b27932c41f1c4e42cc5e8155bd6666a078e0430ff7529f715`。20,696个唯一blob共123,298,206B，1,476,054次展开引用的次数、first/last、DAG与全部文件hash均核对。索引2,428,120B、单gzip620,140B；所有记录和唯一数据均在2MiB/8GiB/512MiB/256MiB预算内，最大逻辑记录930,431B。expected gzip的7005条、243,693,335B也完整读至EOF并核双hash；每个clock、action、阶段、entry和选择index按原顺序核对。

传输层明确依赖冻结的正式`CaptureCAS135`，SHA `f9ace95818b6384ad2663d293a07d036efc0aac52c8cd75fdabb3ec82065cd2c`，其encode_basestring改动有既有完整等价benchmark及[2正例/26拒绝独审](../evidence/opening-cas-codec135-review-20261101T181343.524929Z/review.json)，收据SHA `fa66c3ba5a9aa13e118ec04fc694ed63cffae5efbba5391c76d3ec63410795d3`。本审仅缓存**字段完全相同**的完整packet item及完整expected row/None描述；任何字段变化都会重新校验，未跳过逐logical SHA、字段展开、引用或阶段。

重新对齐31,918,511个已知叶：30,720,713个record byte、1,043,690个projection叶、140,100个vector shape字段和14,008个阶段身份值。26,583,383个未知byte按已恢复写集合审核，其中16,796,491个原件值非零；14,541个pickup未写arrival word单独记账。没有扩大None范围或用整行掩码跳过已知内容。九类count-only payload域的全程最大count均为0。非空域完整保留并核对，最大unit14、pickup8、special4、windows2、boundary69、owned3、live2；其他完整packet仍保留为观察，不能据原件队列1129项就声称全部wire语义通过。

首次跨40秒来自逐次正常f32加0.1：前一clock为39.999961853027344，zero-based frame400（第401个受控帧）达到40.09996032714844；资源只在该帧完整947后的spawn阶段5615/action404出现。G2444此前一直为40，在这里写为f32(now+45)=85.09996032714844，余下阶段保持。clock依旧由明确的外部调度写入G2352；这是受控14入口连续流程跨阈值，不是完整880或原件自然主循环的40秒验收。

该见证帧没有ordinary新生unit，完整旧unit backing保持，预算小于1；从前一claims阶段共享RNG独立重放，1次kind选择得到kind5、amount3146146168，2次位置draw后1次朝向draw，最终四个RNG word与原件一致。G2408由168→169，G2412保持；GUID `17370383913897164969`与新56B、visual9008、display5991、XYZ及完整169创建包绑定。pickup slot2在cap8内复用，**+4原有非零字节`111f1e42`继续作为已知字节严格比较**，没有改成None。旧活动前缀与其他inactive槽保持，最终XYZ另与原件运行前冻结的模型expected严格相同；本审没有重跑地形查询模型。

资源消息仅按canonical单actor169、GUID typeF110及entry9006..9008筛选；完整payload、数量、GUID及队列顺序逐阶段严格比较，未用delta、去重或opcode计数代替payload。实际这条流程只产生一个kind5资源；另外两种、cap2与13th fallback仍属于[64例组件证据](2026-11-02-resource-spawn0135-independent-review.md)，不冒称500帧覆盖了它们。资源随后真实拾取和效果尚未完成；第二次85秒deadline也未到达。

4个guardian的16,816次timer payload比较覆盖4204个owner capture；单位GUID、slot、header、ability slice、3个timer、静态44B定义及28B header全部绑定，67,264个未知byte仅为U68物理pointer。跨单位GUID、漏owner、timer/backing不一致、错误timer bit和扩大已写byte掩码的5项反例均拒绝。静态记录按WASM初始零内存加全部active data段顺序覆盖重建，未归因于snapshot创建。独立Dijkstra确认78400格、seed39340、reachable72660及完整u16 SHA。

四次选择仍为帧87 Thunder Clap、130升级、214 Cleave升级、379 Battle Shout，原候选与1072输入index一致。Battle在第6个后续player tick、帧384真实施放，effect8完整owner0 payload、强度/到期与CD乘数独立核对；后续所有阶段继续比较，未替换卡。最终level5、XP20、gold64。

原件PID/PGID78734退出0、deadlinefalse、审阅时均missing；878项host全deny，host0、栈恢复，512MiB heap、256MiB WASM预算保持。comparison的127.616秒包含parent逐阶段重比，不能当作Node运行时长或据此断言60秒Node超时。本审[owned终态](../evidence/resource500-independent-review-owned-20261101T182704.730013Z/process-terminal.json)为PID/PGID96527、exit0、60.197秒、无timeout、两者missing，低于120秒审阅预算。

保留两类失败历史：旧181407 expected-first批在list/tuple TypeError处中止，尚未形成fixtures/inputs/owned原件进程或输出，不计original case。本审首轮182511已遍历完整CAS，但审阅器迁移误改8GiB常量导致收尾断言失败；没有生成通过收据。只修新审阅器常量后，182704轮完整重审并取得本页最终收据，失败产物原样保留。400帧旧审阅器与证据未修改。

原件侧仍依赖声明的历史snapshot、已初始化world/locale和外部clock；独立侧使用预解析world。完整880、native Windows、整局、资源实际消费、60秒其他due事件、Boss及终态保存都不在此审阅结论中。
