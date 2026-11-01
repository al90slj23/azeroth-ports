# Fixed135 资源生成组件只读独审

**通过声明范围的独审。** 固定 `0.135.1 / 90898d5e3`，完整原函数1417×12、947×52，共64个fresh用例；严格复核122,748个已知值及196个完整opcode169包（32,043B）。本次仅读取既有源码、静态原件和证据，没有执行原件、模型、checker或builder，也没有新增original case。[独审收据](../evidence/resource-spawn135-independent-review-20261101T180953.939397Z/review.json) SHA256 `4b28ac7f2c381a1d12b854eb70708e6d3f24b33e7da91000df1200cb3ec48347`；[结构化报告](2026-11-02-resource-spawn0135-independent-review.json)。原[组件收据](../evidence/full0135-oracle-20261101T174727.123299Z/resource-spawn135-comparison.json) SHA `85b5c088e80e33d059b880275e59aa6f2a3613344fc887f2886566130fdde005`。

58份冻结源与审阅时当前源的SHA全部匹配，其中50份生产文件恰好构成AST导入闭包；资源核心SHA为 `f142c219f60abc3b69ba645ef2fd87adec7728a0e034069e524d06b15c0b2aa3`。私有模块仅追加1417、947和global0三个export，所有非export section及callee body保持原件字节。9个静态函数窗口同时匹配只读SQLite定位、WAT片段与原件body SHA，没有替换callee。

独立重做种类选择的xoshiro128++乘3和拒绝判定，确认5例重抽；传入1417的amount确为**接受该次抽签后的state[0]**，位置生成随后才继续推进同一RNG。结合已冻结的ordinary前缀draw计数，再独立推进位置draw、重做actor朝向抽签并比对最终四个RNG word。ordinary前缀draw数来自冻结模型标签，是明确的输入依赖；不是本次原件动态instrumentation的观察值。

12例future、12例cap与28例947资源出生均符合G2444分支。cap统计活动pickup前缀中kind3..5，不读取marker作为排除条件；12例cap均含非零marker。future/cap只停止资源分支，之前的ordinary947工作仍生成3个NPC并消费RNG、查询world，不能把该结论写成完整947不消费RNG。

2个13th fallback用例显式提高playerZ至100，前12次高度差检查失败，末次无条件尝试对应26个位置draw。静态13516窗口确认循环与最后一次无条件查询的次序；1417随后仍先按地图radius−2夹取XY，并在资源公共分支查询最终高度。审阅器独立重算最终XY，核对4例1417夹取；最终Z及完整packet与冻结expected/原件严格相等。本次没有重跑地形查询模型，不把Z对照称为第二份独立地形实现。

40个资源actor的GUID/counter、kind、amount、visual/display、XYZ、朝向及完整packet均绑定核对；其余156个ordinary NPC包同样逐包严格比较并解析169结构。56B记录仅+0及+8..55写入，新记录+4..7保持未知；aux为(capacity0,pointer8,count0)。容量增长、旧inactive backing和旧已知字节严格比较，71,736个未知byte单独审核来源与写掩码，其中28,209个原件byte非零；没有把None补零或用宽泛整行掩码掩盖已知payload。

world输入来自既有451资产独立解析的9块terrain、280宽navigation和560宽secondary文件，三项SHA及独立资产收据均核对。oracle的`ai_world135_packing.mjs`将这些查询文件**手工装成查询等价的Rc124/terrain/nav/secondary内存布局**，未消费的metadata显式置零；primary为空、flat-height关闭。这批没有读取原件memory snapshot，也没有执行原件World构造器或在oracle内重跑资产解析。该前提属于受控类型化world输入，不能据此宣称原件自然资源加载链已验收。

64个fresh实例，878项host import全deny、实际host0；所有入口及allocator栈均恢复1048576。32MiB WASM cap，峰值20,578,304B，512MiB heap，owned PGID/60秒预算。原件PID/PGID6261已退出0，记录耗时1.613秒；审阅时以无信号探测确认均不存在。完整输入、expected、输出、world、静态片段与模块SHA保持，stderr为空。

**这批尚未接入400帧组合链，0 full880帧、0自然40秒验收。** 52份opening来源记录均声明自然经过帧数为0，之后显式设置约40秒clock执行一次完整947；没有将组件计数与400链相加。其他due947事件/Boss/elite、资源实际拾取与效果、1417其他kind，以及primary存在但nearest miss的低地址读取仍pending。本次未修改98份冻结源、headless、checker或原证据。
