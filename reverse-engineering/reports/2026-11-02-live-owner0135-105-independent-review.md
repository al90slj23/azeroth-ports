# 固定135：105例物理live复核与栈来源反证

本审完整读取固定0.135.1 / `90898d5e3`的105组、105次原922/4600/1072记录。**选择续跑的物理retain/partial append限定通过；effect8/9辅助词来源的一般结论被反证，不能将整批标作通用physical caster已恢复。** 原件和生产模型均未在此复核中执行。

原采集收据SHA `d152eb693fe6ab39410d4977ec0e9e12e290dbe73a19920e111f1664e44c0541`；[本审收据](../evidence/live-owner105-review-owned-20261101T224434.323126Z/review/review.json) SHA `3e1df6d54b1464c4ab4a4bf483047eff3f7ceb4a73ff2da5c760ffc3ccc3ebe6`，独审39384 exit0／PID及PGID均missing，0.667秒。

## 通过与未通过的内容

- 冻结51源（43production）、全部非export二进制区段及六个真实函数body/WAT身份均绑定。仅新增922/1072/4600函数和stack0导出，878个host导入全拒绝，原件实际0host。完整输入、原输出、期望、runtime、terminal与模块哈希保留。
- 完整机械重比16,387已知值、2,388原期望None和66个结构null；这只复核既有numeric投影，不称独立重建全部1512算术。
- 自写的forward retain、整32B复制、inactive尾保留、扩容与partial append核对11,928个已知物理字节、980个来自输入None的严格poison继承、66次selection/resume。新分配未写的1,408字节保持未知。
- 922 effect8/9成功37次的辅助+16共148字节必须作为**有写入、来源尚未恢复**单列。它们不能视作目标槽未写字节或强行补零。

## 为什么旧105的0差异不能证明+16来源

原922 WAT的effect8路径5748..5757、effect9路径5759..5768，只写临时frame+40的kind和+44的强度，然后跳过5810..5813的default分支。后者才从definition+8写frame+48。因此8/9不会执行该初始化。公共append在5982..5986从frame+48无条件加载u32，并实际写live+16。

这一原函数在入口将stack减240，源地址为entryStack-240+48。105个direct harness没有捕获调用前的该词；37次成功cast输出均为0，而两种definition+8也恰好为0。该事实只能叫冷harness输出观察，不能证明来源或自然caller行为。

root新120帧采集给出了直接反例。本审使用已审CAS证据解码器，只读取到stage70：human perception / spell20600 / kind8的新live+16为`d5ad8942`（u32 `0x4289add5`），不是0。该辅助读是有界prefix观察、逐条SHA/blob验证，没有完整CAS finish，不冒称重新复核整个120帧采集。原120的6444差异与原105采集均原样保存。

## 消费者语义边界

限定空其它来源、periodic budget+28为0的kind8/9域中：1512 live块1282..1523以kind8、magnitude12、spell20和expiry24计算属性；1202正面聚合块17..350也不消费live+16。2088块23..181使用periodic28、expiry24、spell20和owner0，后续retain按完整32B复制；1073的保护/cleanup用kind12或kind7/sourceSpell20，其live+16仅随整行复制。这里确认的是这些已检查分支中的无语义读取，不是全程序永久无消费者证明。

独立重建应标记typed opaque栈来源，或显式提供已验证的caller源。已知有语义字段仍须严格比较；不能为了绿检查扩大None掩码。新的显式caller-scratch controlled批次另行验收，不转计本105结论。

未修改生产源码、primary或registry，未启动原件／模型／checker／builder，未触及安装包和存档。独立一局、完整880、Windows执行和最新138流程仍未完成。
