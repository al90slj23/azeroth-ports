# fixed135 完整968本地路由：异作者只读独审

范围内通过。33例完整原件968目标调用，与先前38例直接2328分开记账。这里补上的是canonical24消息→本地inline Game→2328的实际调用链，尚未完成联网同步或自然App输入生产者。

## 冻结对象与输入层

`evidence/player-motion135-oracle-20261101T231626.255308Z/dispatch-comparison.json`，SHA256 `0513dc6d834df50dd845f032a417d6922accde21c575141a0e3c45516316349d`。0.135.1 / actual build `90898d5e3`，21冻结源、45本地导入边、33/33完整968、0差异。独立AST闭包与全部冻结/当前/运行前后SHA再次相符。

App是明确的typed partial fixture：App14549000，直接内嵌Game=App+16=14549016，网络tag2608=2。真实6730直接写该G，再调用真实1089，未把原快照Game复制成inline Game。使用真实缓存worldRc26204808，引用计数由2升3；不是伪造world或externref。

setup-only原件观察先产生setup-context，再作为显式pre968输入生成期待；随后每个目标968案例重新执行同样setup并逐字核同。setup-context是原件观察输入，不是独立构造器验证、自然4253/1371 App安装或fresh boot。setup6730与1089各34次（单独观察1次+33目标例准备），目标968为33次，互不冒充。

## 独立恢复与核对

审查者未执行原件、生产模型、checker或builder。从原件968窗口独立恢复外层LE24解析、非有限早退与route0行为，再明确复用前一份异作者2328数值/terrain审查器；不称第二次独立恢复2328 helper。

1. 24B依次为flags、u32毫秒、XYZ三词、朝向。4个坐标/朝向都在写Game前通过绝对位值≤0x7f7fffff检查。
2. route0/peer0定位App+16；G2496=flags，G440=1，G444=f32(f32(u32毫秒)/1000)，调用完整2328，之后清G440。
3. 随后调用完整17726，在mode2582=0时自然早退；route0跳过网络发送分支。

- 21有限输入、12在mutation前拒绝的非有限输入（XYZ/朝向各3个+Inf/−Inf/NaN）。覆盖12种实际opcode：181、182、183、185、193、198、200、201、203、218、219、238；静态可分派25种，不说全部动态覆盖。
- 全85536 Game字节（33×2592）与170544 App字节（33×5168）严格相等；inline Game以外85008 App字节、赋值范围以外84476 Game字节未变。12拒绝例完整App/Game均未改。
- 有限输入中的15例正常接受、5例纠正、1例pending拒绝；2次圆边界夹取、5次动作u32回绕。完整新增5×199/2×150包逐字节相等，原队列容量/指针保持，计数按7包推进。
- world124前后原始字节相等。既有queue prefix和2318几何范围的target后态不变，依靠冻结原件runner前后逐包/hash断言；结果未导出完整postmemory，不能称审查者独立重读这些后态。

33是runner的直接968计数；其中21次2328和21次mode0的17726调用由实际有限输入及原968静态分支共同推出，没有额外callee计数插桩。所有原件函数体和非导出section逐字节不变；新增导出仅968/2328/stack及setup6730/1089。

## 运行与边界

原setup进程9920 exit0、0.3410s/60s；原target进程9921 exit0、3.1751s/60s，PID/PGID均消失；878导入全拒绝、host0、166395904B/256MiB。没有存档访问或网络请求。

独审进程17700 exit0、1.0381s/60s、PID/PGID消失。独审收据`evidence/player-dispatch135-independent-review-owned-20261101T232159.020182Z/review/review.json`，SHA256 `f94ace04d567b7c3f682998c8b281313212de2fd41aaf915f14ad820faa3e5bf`。

未覆盖route1、peer非零、mode1的17726消息转运、broadcast/网络同步、199ACK、短截/损坏payload、非移动opcode、phase0、UI/摇杆消息生产者。完整游戏流程、完整880、原生客户端和联机可玩性仍未验。本批新增独审原件调用0，完整一局0；生产代码、primary和registry均未由审查者修改。
