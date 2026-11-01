# 真实cast的697B独立预测复核

对 [实际App投影](2026-11-01-app-state0135-capture.md) 的独立只读复核通过：**730B一致，其中33B是明确输入、697B是独立预测；另4,438B保持None而不比较**。复核只读取此前原件自然构造的cast观察，新增原件调用、案例和主循环帧均为0，不证明完整App生产者或游戏完成。

作者[比较收据](../evidence/app-state0135-capture-check-20261101T121246.633972Z/comparison.json) SHA `0850bf419fe3b430117255ddd445501721c0c3c6ffb343d99fdd7c3e0b09c03a`，来源[原观察](../evidence/full-app0135-probe-20261101T120144.289175Z/receipt.json) SHA `fd5dba35d0aeacffe822ce070fd5bc218da8352a5b725e48c166df289b91c726`。[最终独审收据](../evidence/app-state0135-capture-independent-review-20261101T122346.076103Z/review.json) SHA `1745dcd8d245eeaa21e79b074e34c7f94e585b460afac942c410cfef695af144`；[机器报告](2026-11-01-app-state0135-capture-independent-review.json)保留原始绑定和重算结果。

## 输入与预测独立重算

[review_app_state135_capture.py](../scripts/review_app_state135_capture.py)没有导入生产模型。它复用先前独审的逐byte WAT工具，重新从原WASM／SQLite读取4253、53845、83825、122123的精确范围和body哈希；直接解释原53845的30条store生成history240，并从原data section重建16B空table头及13B server字符串。

仅从cast App取以下33B作为输入：4008处16B首map seedpair、4768处4B transport指针、4928处8B LCG seed、5056处4B server指针、5161处1B启动flag。四份map头及其后3份seedpair由首pair逐次wrap64生成；没有复制整个128B map或240B history，也没有提供三个livecopy区。

随后独审WAT VM在不同的App／scratch地址运行原直线窗口，重新生成完整5168位byte／None投影，并逐项核对作者expected、已知／输入／预测mask和每个region哈希。结果是240B空history、112B map头与后3pair、8B seed派生值及337B其它精确写入，共697B预测一致；33B直接输入不计预测。settings368、loaded-state48、preferences36与其它未恢复范围继续None。

## cast时间与后继状态分开

观察来源固定为原import867返回真实callback时的 `env+8 → Rc → App=Rc+16`，env12、5305816 vtable、25ms timer和原host事件相互吻合。App=21088840、Rc=21088824，cast时内存27,787,264B；当时App clock marker为0。后来final内存达到413,728,768B，clock marker已变1，独审没有用后继memory替代cast数据，也没有恢复任何原memory／table／global状态。

独审重新核对原观察冻结的10份脚本、配置和bridge哈希，并确认bridge完整保留官方JS原前缀，仅追加透明观察入口；浏览器在编译前校验完整原WASM SHA。记录App字节的代码只读真实原内存，没有制造App对象或改写原函数。原观察的所有owned进程／进程组当前均missing。

作者capture checker的7份完整源码闭包与前后／snapshot一致。reviewer及自己的WAT工具另行冻结，未执行生产模型、原WASM、浏览器或网络。

原观察中的8次idle880返回和SwiftShader渲染panic只作为背景保留，没有计入本次投影验收。cast时Rc strong／weak属于opaque观察，不预测holder数量；697B吻合也不恢复剩余4,438B、分配器／熵／profile／settings producer及完整所有权，不宣称健康启动、实际游戏态880或独立完整App已完成。

复现：`python3 -Werror reverse-engineering/scripts/review_app_state135_capture.py`，只读取固定证据。
