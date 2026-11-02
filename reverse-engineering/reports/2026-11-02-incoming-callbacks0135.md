# fixed135：post-history HP callback完成的窄谓词

新增纯模块 `core_spec/incoming_callbacks135.py`，SHA256 `4045cd21c510175bfe87313687045ee66de8b2dffc3dd3a498580b3955ef4fc9`。它只在完整显式输入足以证明post-history回调无作用时返回 `IncomingCallbacksProof135`，不修改HP、不执行原件；未知源、可能触发914的正反击、未恢复的984种类均拒绝。旧shared core/headless没有修改，也没有把 `callbacks_complete=True` 写入既有路径。

静态及模型自检证据：`evidence/incoming-callbacks135-static-20261102T003044.215536Z/trace.json`，SHA256 `54853c37c7a3285384c921f1b289ab6151bb105efa62c68ad6b18051cfbc55a7`。5个函数1073/984/914/921/1560的原件body/WAT重新绑定，13个静态窗口；18个新模块检查9接受/9拒绝仅为模型自检。新增原件调用/样例0，旧163/40没有重跑或重复计数。本模块尚无新增完整1073差分或异作者独审，不代表完整1073已经恢复。

## 原件顺序与完成条件

1073先写48B history（其中HP为prefix扣血后的值），然后对G1708/G1712的完整32B live记录按原顺序累加：仅 `now < expiry24` 且 `kind8==13` 的value12进入binary32总和，初值为负零。若sourceGUID=0或原始参数3=0，原件跳出**整个**post-history callback块，item22与两次984都不会执行。旧fatal40采用GUID0/参数3=0，因此不能作为普通接触攻击该链已验证的依据。

普通921调用1073明确传参数3=1、非零NPC GUID。此域中，active raw13总和为正可能调用914；本模块直接拒绝，不假定该反击不影响玩家HP或其它状态。总和不正且phase1时进入item分支：G2028/G2032的8B item记录按byte0==22累加value4。正item22总和与正local1（原始/模式缩放后、护甲前amount）共同满足时，原件临时把774设3、调用914、再恢复774；这不是无作用证明，模块同样拒绝。

随后两个完整984事件结构分别由1073写出（第一个含1024，第二个含5），再真实读取Game1440、执行可选minimum-one，最后才是intrinsic12、modifier31、lives与死亡续接。984的G2056 count=0直接跳过整个回调主体，连cap/pointer都不读。非空的窄补充域仅接受完整已知36B tag54记录：selector41指向common-exit label6，跳过所有事件分支，local41保持初始0，释放快照并恢复Game472/476，因而不进入1512。其它984 kind一律unknown。

## API与输入层

`CallbackVector135(stride, count, storage, capacity_word=None)` 要求完整active记录；可附带真实inactive backing，未知字节继续为None。capacity未知时保持None，不能用 `len(storage)` 捏造capacity；count0时不要求虚构pointer或未消费backing。`IncomingCallbacksInput135` 显式包含now、history后HP、sourceGUID、参数3、phase、item反击基数及三种typed vector。

`prove_post_history_callbacks135(input)` 成功后才能使用 `.callbacks_complete` 与 `.hp_before_minimum_one1440_bits`。`active_raw13_sum135(live32, now_bits)` 只用于局部分析，不能据其返回值宣布callback完整。None物理源会抛unknown；模块特意没有把level的空semantic tuple转换成物理空源的便利函数。

输入点必须在history append之后：shield-break984、reserve spill及其它prefix前序效果已经落实到同一源owner。后续minimum-one、复活、死亡、keyed HP、Aura和源registry/history仍分别处理，不能混成这个谓词的结果。

## 当前human warrior moving Rune的已知与未知

另一作者的独立model observer提供921条pre-AI源输入，最后是frame921/level8，仍保留source before/after、完整live backing及None：`evidence/incoming-callback-sources135-model-observer-20261102T002438.264636Z/sources.json`，SHA256 `880fc4c769ee4da33a2261ea632bf021c873b32188d8dcbee70b92f31f77f59c`。本次只消费其声明输入，未重跑scheduler，未读取原件输出反填。

921条canonical live的kind均在0/8/9/12内，raw13总和全部为负零；fatal前active记录只有Battle Shout产生的kind8。其auxiliary+16仍为None，但13反击分支不消费它，故可保留。这个结果说明该明确live域没有13反击来源；pre-AI到post-history的同一性仍依赖前序prefix没有新增源的独立证明。

observer同时明确将原始G2028 item8与G2052 eventdef36 owner记录为null未知。虽然level.sources.item_modifiers与definitions始终是空tuple，旧headless也强制传 `modifiers=()`、`incoming_item_effects=()`，这些均不能代替真实producer。当前不能仅凭该observer给完整moving921返回callback完成；必须由另行恢复的empty-profile/选择/事件producer证明这两个完整源的active count，或者提供其它完整typed vector。接续时不得从原件观察到0倒填模型。
