# 固定0.135.1：完整默认开局独立复核

**只读复核通过。** 绑定[完整开局最终收据](../evidence/world-snapshot0135-oracle-20261101T103934.606037Z/opening135-comparison.json)，SHA `91de74157f822199071a0998d02b40354de124fe9a823ff4d688da47b6520b72`：16输入、32次完整6730缓存命中构造与1089入口、0差异。复核器未执行原件或浏览器，新增原件案例为0。[复核证据](../evidence/opening0135-independent-review-20261101T104856.729179Z/review.json) SHA `9a7e780a7ce22cb83a747ccc4bfeeb0386826590fda43400923d0a9d7e25d19c`；[可执行复核器](../scripts/review_opening135.py)。

## 身份、输入与真实缓存边界

独立AST导入遍历确认完整39份生产、fixture、builder、runner依赖闭包，当前/运行前后/源码快照SHA完全一致；9份原件artifact逐项核SHA。重算完整16组seed、class/race、sourceGUID输入到独立expected和诊断，与原先冻结fixture逐项一致。expected先于原进程生成，Node仅接id与五个声明字段，未读取fixture或expected。

原件SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。私有WASM只追加6730/1089函数出口和global0读出口；所有非section7字节、原导出、函数体和原callee保持。原global section只有一个mutable i32初值1048576，16次完整恢复及全部正常调用前后栈一致。

原件恢复真实166,395,904B after_begin内存，SHA `23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf`；独立world decoder读取117,440,512B after_world输入，SHA `f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a`。另行解码两份纯world模型相等，并重算2,318段读取范围除Rc所有权头8B外共5,950,600B完全相同，未拼接heap。

逐例核App原始5168B等于合法snapshot，再独立重建class/race、LCG seed、sourceGUID四处声明patch。完整6730后App仅4928..4935的LCG seed变化，按原64位LCG重算一致；1089不再改变App。原world Rc124仅6730强引用加1，所有其它字节及1089前后Rc保持；同一真实world进入新phase0 Game后执行完整1089。没有写Once或假造Rc/world/cache。

## 六vector与消息链

全六vector物理头与Game2592偏移、allocation范围、capacity/count、所有backing行逐项交叉检查。每个active记录的None必须恰好落在独立写范围清单的补集；inactive槽保留全未知，不能在已写区域扩大豁免。55,808B backing中33,936B已知字节严格匹配；9,504B active未写中8,228B非零，12,368B inactive中9,731B非零，全部raw保存，未假定零值。

真实完整1089本批新产生的记录合计：32条companions、64条NPC、32条kind2、64条special、38条windows、1,104条boundaries。窗口10例产生2条、6例产生3条；四special/69boundary及banner均来自这16次新完整1089结果，**没有用旧116次组件调用或历史终态重放替代组合验收**。仅验证当前默认Elwynn域，其它地图的polygon/分支不据此宣称覆盖。

所有1,248条新消息/134,560B及16条start JSON逐字匹配。额外用独立格式解析器读完1,232条169包的全部字段与payload边界，核packed GUID、物理88/424/56/8B记录中的GUID和XYZ、NPC完整64位sourceGUID、kind2数量2再1、boundary entry9013。16条150 banner独立编码比较。全部队列metadata backing与active payload allocation backing的长度、指针范围、已知payload前缀一致。夜精灵case10的原构造器226包前缀在1089后原样保留并单独登记，未改算为开局模型输出。

G2408逐例10→87、phase0→1、同一RNG状态贯穿整条链并与独立结果一致。构造器Game1428朝向实际为 `0x3fcccccd`（1.6），不是0；静态原1560的zone+116→local33→temp1516路径与新原件Game/companion包朝向一致，原件前已经修正的开发假定未混入最终fixture。所有完整2592B Game、5168B App、124B Rc sidecar均核长度/物理字段映射；未投影的Game字节依然未知，不扩称整块Game已独立预测。

## 执行与完成边界

原Node22524真实退出0且PID/进程组均缺失，约1.986秒；独立256MiB/4096页上限，峰值166,395,904B。878宿主导入拒绝、实际0次，未启动应用、访问网络或用户存档。WAT仅通过只读SQLite定点取8个原函数，核完整1089的1744/5736/1417/1821/17979链及内联vector地址，无全读1.3GB WAT或原件重跑。

这证明显式已解析world输入上的默认开局组合；world/menu/profile生产、非空装备天赋、其它地图/模式/语言、完整880、存档、UI、联机与独立完整一局仍未完成。新增fresh bootstrap=0，主切片帧数增加=0。

复现：`python3 reverse-engineering/scripts/review_opening135.py`。该命令只读既有原件证据，运行纯独立规格及字节审计。
