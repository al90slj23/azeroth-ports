# 固定0.135.1：受伤48B日志的独立复核

[组件原件收据](../evidence/full0135-oracle-20261101T092259.307993Z/incoming-history135-comparison.json)为164组、924次完整1073入口、915次实际追加及9次守卫返回，声明字段0差异。[独立只读复核](../evidence/incoming-history0135-independent-review-20261101T093042.886399Z/review.json)已通过，SHA `62ed36f102d40876a84ab2f7c67bba2d5cbbaefecd1c2aaaba4de2aef709cf06`；复核未重跑原件，也未修改作者源码。

复核从显式初始backing和操作输入独立重算10秒严格小于剪裁、`len>399`剪裁、环形下标、全部增长搬移及逐f32护盾/HP字段。覆盖74次非环绕增长、33次移动旧高位段、15次移动旧低位段，其中10次前后两段等长，均按原55797的严格`prefix>suffix`判断处理。不是只调用作者模型自检。

8,408,160B实际history backing中，独立严格比较5,516,958B；33,030B原槽未写padding严格保留。2,439,658B新分配未写字节单列未知，其中981,581B实际非零，没有预测成零。另451,544B为已写入的翻译姓名指针观察，按语义规范化；所有active字符串与长度均严格核对，source指针1和静态icon指针进一步逐字节严格验证。已观察106,263条有实际姓名的active记录。

初次复核曾错误地把`19964`的返回姓名指针等同于输入literal地址；真实默认翻译表返回了正确英文文本的堆切片。该[复核失败记录](../evidence/incoming-history0135-review-failed-20261101T092749.966196Z/failure.json)保留。修正依据为原19964/82070的真实初始化与查表行为，不是放宽文字内容或修改作者实现。source与icon地址仍保持严格核验。

另核对12份源码及传递core入口快照、独立expected重放、原件只接收8个输入字段、不接expected、完整1073签名/body和所有非export节保持一致；878宿主导入全拒绝且实际0次，32MiB上限与60秒期限、进程退出0均已读回。2,395,008B rawG与变化清单一致；66次首阶段增长前未保存的旧history堆指针词另作观察，没有伪造其旧值。消息/通知payload和metadata的长度、数量与rawG头一致。

本批只验收无匹配source、spellID0、英文fallback域的受伤标量和history组件。真实DBC元数据、完整registry/keyed/proc、致死复活、真实进场、主切片整合及完整一局仍未完成；rawG保存不等于其全部语义已经恢复。完整范围和复现命令见[JSON](2026-11-01-incoming-history0135-independent-review.json)与[复核脚本](../scripts/review_incoming_history135.py)：`python3 reverse-engineering/scripts/review_incoming_history135.py`。
