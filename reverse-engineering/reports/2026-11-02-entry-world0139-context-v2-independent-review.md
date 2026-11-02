# 139匹配原件context v2：受控观察独审通过

**修正尺寸后的明示研究输入观察gate通过。** 原件2917→2945→6786→1108已完整返回；本次独审只解析冻结字节和记录，没有执行作者observer/acquirer/model或任何原件。独立开局模型用例仍为0。

## 2945完整输出与保护区

本体12条store写30B，最高到+35，返回区至少36B；首个local0重绑定在1204行，此后无store。v2实际申请72B：前16B C3、40B输出、后16B D7，传入base+16。完整36B返回已记录；内部5..7/13..15六个未写padding保持A5，40B区末4B也保持A5，两侧16B canary在返回后及两份后续完整内存中都不变。只复制前16B到profile224..239；其余profile仍是明示研究输入。

旧5d940批的16B申请不足，保持受限、不接受合法context gate。旧作者8文件和memory未改，也没有用新批结果追认旧批。更大的合法缓冲区、guard和完整输出都由新fresh执行产生。

## 独立核查

- 全原件非export7段逐字节相同；官方JS未修改的187,604B前缀加研究绑定接口，没有替换宿主函数。10个冻结源/9条导入边与snapshot/current一致。
- 实际882导入中允许24个真实JS函数，实际16种共3396次调用；deny命中0。资源561次请求全部200，唯一454项85,332,479B逐文件重新hash，逐项绑定三批新139官方HTTP来源。前后manifest与f339dd20e0fe stamp一致、当前index成员关系及每文件SHA都核对；这是点时coherence，不是额外的签名资产manifest。
- 四个组件加六次malloc共10次export入口栈前后均1048576。Node24683/browser24686均退出0，Node PID/PGID消失。最大memory177,078,272B低于256MiB，276个分块POST完整组成两份memory。
- 新worldRc从6786实际生成，App5116与Game2348均指向20544696；此地址动态从本批metadata/内存读取，没有沿用旧20544640或借用flat V。
- phase0/phase1全量memory重新hash；完整App/Game/worldRc、六组vector全部backing、所有packet/notification元数据和payload与独立读取结果一致。phase0六组均空；phase1 NPC4、companions0、pickups2、special4、windows2、boundaries69、counter85、76条packet和1条start通知。

Account实际调用链为2917→48446→66941→import640，空Storage的rogue.characters不含存档。4562实际是Spell.dbc/SpellIcon.dbc resolver；locale查询经20060→83304，14份内嵌JSON与原件Once3/count14作为观察绑定，不宣称独立Once或语言选择producer。

研究App/profile/transport不是自然App，JS/externref生命周期未独立恢复；真实Rc有了可用观察，不代表独立world/1108实现已通过。原initial139零376fixture与这里带tag255/A5的profile属于不同组件域。phase1的windows/1972已有2项，不能把它冒称早先damage139的空1972来源。

最终独审证据：`evidence/entry-world139-v2-independent-review-20261102T031929.466664Z/review.json`，SHA `77bf86b8bddde893f394c678699560b9da0e840388e01293835f2c3bb37473ee`。

独审脚本SHA `11ac5bd8e481ec7f2c880125cfdf29258d14aadeec0b86031a6bbb5a54502a43`；owned SHA `8e2055f57a32f503805ece41e02539608aafdd32bcbc197d8be005a4c9d31bc0`。

机器报告SHA `e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1`。
