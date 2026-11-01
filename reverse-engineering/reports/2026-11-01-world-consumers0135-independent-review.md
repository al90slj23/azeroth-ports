# 固定0.135.1：world查询与位置消费者独立复核

**两批均通过。** 本复核只读原始收据、原件字节、完整snapshot及冻结输入/输出，运行纯独立规格；没有实例化原件、打开浏览器或增加原件案例。证据：[review.json](../evidence/world-consumers0135-independent-review-20261101T102452.631588Z/review.json)，SHA `02a38bc9c6750064a3fb65b3dfce2b1ab7c978671280aef767637c61e2369932`。可执行复核器：[review_world_consumers135.py](../scripts/review_world_consumers135.py)。

## 查询批

绑定[query最终收据](../evidence/world-snapshot0135-oracle-20261101T100514.012707Z/world-query135-comparison.json)，SHA `24427929f2419ed3343f05e3bbcb35ed19cc3df3bf7062bc3018abc58159a720`：959输入、1,858原件调用、0差异，16份冻结源码和10份artifact全部SHA一致。

899个高度点逐字重算已有terrain/world规格，独立从原始输出确认96次真实secondary抬升、47次合法miss。另用单独实现的ring候选收集与排序检查全部60个23181案例，覆盖首个非空圈、严格分数、先Y后X同分、20包含/21排除、±Infinity及短count trap；16B输出、poison和失败payload全部严格一致。本地79个nav契约replay仍是0次新增导航原件调用。

从原始117,440,512B snapshot另行解码9tile/2,304chunk/334,080vertex、560²secondary和280²原始nav字节，重算2,318段来源SHA，并核两instance各段读回未变。唯一trap后原栈1048448实例被弃用，下一次完整restore后栈1048576；原Node20645正常退出0且PID已缺失。

## 位置批与闭包补正

绑定[新position最终收据](../evidence/world-snapshot0135-oracle-20261101T102145.966200Z/world-position135-comparison.json)，SHA `583fc27a56155963d25e90d49da031bddda1df009fbecada6200b0846f81c1eb`：96输入/96完整原件入口/0差异；58真实world、38显式受控组件。30份生产、runner和fixture生成闭包、9份artifact的SHA全部一致。完整seed→fixture、XYZ/RNG与诊断规格均只读重算一致。

此前旧100700批的21份只覆盖生产/runner，漏登记seed helper的9份fixture导入源；原始旧收据 `df810825f678e26c8b3307d41e8274fdf46e96b2eb516cca53049221eb43bd36` 保留。作者补齐30份后重新运行96例；复核独立确认新旧inputs、fixtures、results、export模块四份artifact逐字节相同。[补正凭证](../evidence/world-snapshot0135-oracle-20261101T102145.966200Z/source-closure-correction.json) SHA `4e40c6dffd44af1a86395c61089de7d23363a0197d36d0a65fa40d356e70f23e`。旧新案例不相加。

每例从原snapshot重建声明的Game setup，再核全部G2592前后原始字节，共248,832B；唯一可变偏移1720/1724/1728/1732对应RNG4word。受控Rc124所有字段逐字重建，真实Rc124保持原snapshot值；62份受控数组输入SHA另行重算一致。数组返回后不变依赖冻结原runner实际rehash断言，未单独保存数组返回后全字节，故不扩称完整world所有payload均有双份原始dump。

受控真实完整函数输出区分无path只拦byte1、有path及13516拦任意非零；field24的400/401和成本门槛、8751最多16轮及半径减2到小于12、13516前12轮与第13次无条件回退均有覆盖。最近primary案例确实只取Z=77，随机XY保持且不等于最近格中心；无最近格时Z=99。原Node69100正常退出0且PID已缺失。

## 共同边界

核原件SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`、完整snapshot SHA `f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a`。研究副本只追加section7研究导出与global0读出口，其它全部section/函数体/原callee字节不变。原global section只有一个mutable i32初值1048576；定点SQLite/WAT另核6730栈帧、23181循环与8751→13516→23181调用边界。

两批均单独256MiB/4096页上限，峰值117,440,512B，878导入拒绝且实际0调用；没有恢复JS/externref，没有重新bootstrap或访问用户存档。snapshot adapter是显式输入解码，受控geometry是组件fixture；它们不构成独立world producer。纯模型重放不增加原件案例，也不增加主切片帧数。完整独立world、同主切片整合和完整一局目标仍未完成。

复现：`python3 reverse-engineering/scripts/review_world_consumers135.py`。复核器仅读取原件；其输出是新的只读复核凭证。
