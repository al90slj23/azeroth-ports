# 当前139终局入口49961：不同作者只读独审

5个fresh fixture、10个完整49961入口通过独立复核，0差异。仅有两次受控field400=1且phase1／非endless转换；field400=0、endlessbit1、phase2以及转换后的二次phase5调用均保持不变。Boss／field400自然生产链未恢复，**自然胜利0、完整游戏0**。

- 当前49961先设phase5，再按17209的真实NPC→辅助112→companion88顺序停止移动，之后232与1965胜利通知。实际8个NPC、1个辅助和1个companion停止；12个完整新包／236B的GUID、坐标、序号、payload容量32和顺序逐字节匹配。
- 完整17字段JSON在当前1965／45182／11741／53225与reserve55846下独算，时间为1.250、整数计数和默认Warrior／Human／Elwynn English fallback标签。两条完整UTF8 JSON共466B、各String容量272；中文、双引号、反斜杠、LF、tab、CR、NUL及emoji按真实方言转义。合法hero RustString输入16B capacity=length，不假定C字符串终止。
- 10个调用的完整2592B Game共25920B精确重放，只有预测的phase/action／movement／packetcount／notificationcount变化。10次物理向量18080B完整回放，5160个None观察沿原输入守恒，4750个非零未知字节未补零；辅助／companion未激活5a尾记录也不变。
- 真实1108产生4NPC、2Rune、windows、4special、69bounds，真实925在now1／dt.1产生四个移动；不同作者纯opening／AI／geometry参考重算全部20个setup移动。控件仅在此后写clock／400／phase／endless、合法hero和另一个fixture的显式辅助／companion owner，完整Game输入逐项核，NPC物理来源与moving一致。其他背景50组守恒、RNG与HP未改。
- 75件源／63生产／250边与作者6件全部不变；22个作者声明body加12个额外纯helper相关函数从当前WASM和WAT重新绑定，非export section逐字节相同。旧版本通过没有转记。

20个2945／1600／1108／925为setup，目标49961仅10，共30个直接原件入口。原作者PID47994正常退出；独审PID19644 exit0／15.79秒、PID／PGID均missing。30个原件返回SP1048576，含28allocator共58stack检查，25轮2318-range世界守恒与0host调用均核冻结捕捉／静态守卫；独审未运行原件或作者model/checker/builder。

独参的5次BFS／392000值是纯模型诊断，本批没有原件BFS数组序列化，不能宣称这些表新增运行验证；移动输出与当前来源对齐。10次终止坐标的canonical nonflat高度均命中，miss／nearest-primary分支仍静态域。通用数值格式、其他class／race／locale、非空recap、其他终局输入、自然Boss胜利、完整884、Native、联机和存档均Pending。

首次独审仅因旧helper handoff字段名读取错误而退出，0作者／原件，源码和owned终态保留排除。最终目录 `evidence/terminal139-independent-owned-20261102T140535.721357Z/`，review SHA `74f970c1aed23527e0a70ca61e2de5941fc6c98da77565b50ce9d4edda59ae37`。安装包、存档、Android、公共登记与Git未改。
