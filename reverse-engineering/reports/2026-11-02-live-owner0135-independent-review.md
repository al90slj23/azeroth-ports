# 固定135：完整live所有者与显式栈源独立复核

**限定通过。** 本审不运行生产模型、原件、checker或builder，完整读取固定0.135.1 / `90898d5e3`的109组／109次原件调用：43次922、33次4600、33次1072。独立核对完整live capacity/backing、forward retain、partial append以及显式922栈源的传递。**这不是自然1076 caller栈来源已恢复，也不是headless、完整880、Windows或一局验收。**

[原件比较收据](../evidence/live-owner135-oracle-20261101T224420.333917Z/comparison.json) SHA `85979898b212c591d45bc81dc3c3baf8311b861622e5687c6cefb6aa9965e695`；[独审收据](../evidence/live-owner109-review-owned-20261101T224655.075582Z/review/review.json) SHA `d2fd7c367c173c4c09b59cd5a0cf9a8a586179a30ebc512f2c0e9c291c4efb0a`。原件39284 exit0／双missing，3.901秒；独审44132 exit0／双missing，0.948秒。

## 原件与来源绑定

51源／43production的当前文件、前后表和冻结snapshot逐一相同；生产AST未引入文件、网络或原件执行入口。完整原件SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`，六个真实body与WAT绑定。非export二进制区段逐字一致，只增加922／1072／4600及stack0导出，全部原callee保留。原件109个fresh instance、32MiB内存限制、512MiB JS heap、878拒绝导入、实际0host和所有返回栈均核对。

输入、冻结expected、所有原输出和queue元数据、runtime、terminal与私有module哈希均保留并读回。expected-first时序由冻结启动器和prepared描述绑定；独审自己不重新生成生产expected。

## 独立重建的物理规则

自写算法从immutable输入推导结果，不调用生产helper：按原顺序保留行、仅向前面的孔复制完整32B、不清inactive尾；满capacity按max(4,2cap)扩容，新分配未写字节保持未知。

- 66次selection/resume：先移除所有spell1020，再append kind12／1020／now+1／periodic0，仅写实际0..11与20..31。目标槽+12/+16必须继承retain之后的旧槽，已知byte严格核对，输入None的poison也不丢失。
- 922 effect8/9：只移除owner64==0的同spell行，非零owner同spell保留；独立计算kind、strength、duration和expiry。辅助+16是来自调用栈frame+48的实际写入，与目标槽继承不同。
- 完整核对12,732个独立已知物理字节、980个继承输入None的严格poison字节、36次整行移动、99行移除与19次增长；1,504个新分配未写字节单独未知，不补零。

完整冻结numeric投影另机械重比17,215个已知值、2,500个原expected未知byte和66个结构null。它支持原件/模型投影一致性，不冒称此审重新实现了全部1512算术或UI/packet语义。

## 显式来源与typed opaque路径

原922 effect8/9分支只写frame+40/+44，跳过default分支的frame+48初始化。公共append随后从该词写live+16；因此它不是definition+8，也不能假定为0。旧105批两种definition+8和冷栈输出均为0，曾使错误来源猜测通过。自然120帧的perception反例已由[105反证审](2026-11-02-live-owner0135-105-independent-review.md)保留，新109不能倒改其结论。

本109 harness在922入口**显式写入受控源**，同时保存entry stack、240B frame、offset48、地址、原值、declared值、调用前和调用后值。37次显式known源成功cast分别覆盖0、`0xa5a5a5a5`、`0x5a5a5a5a`和自然反例词`0x4289add5`；独审从输入u32独立预测并严格比较live+16。2次无目标不append。

另4例使用`ScratchAuxiliaryWord135(None)`向模型声明caller源未恢复，其+16共16字节不能说是预测通过。相同controlled输入另以已知源进行companion推导，独审从输入重建完整concrete backing并与原件严格一致。typed unknown的来源限定922 effect8/9 frame+48，返回descriptor必须由组合控制器随复制/压缩继续保留，不能扩大成任意字段的None掩码。

已检查的1512/1202/2088/1073限定live消费者分支，不将该kind8/9辅助词用于数值，只在整32B复制时传播。该静态检查限定空其它来源和periodic0，不证明整个程序从不读取此词。

## 剩余范围

自然caller栈producer、caster7/12物理append、1073完整incoming清理、1202物理Aura与所有消息语义、App及完整游戏流程仍分别待验。本审未改生产、primary、registry、安装包或存档，未执行EXE/WASM。两份reviewer脚本来源已保存在独审自己的source-snapshot；旧105与新109计数不相加。
