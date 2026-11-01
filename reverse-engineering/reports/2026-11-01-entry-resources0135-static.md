# 0.135.1 真实开局的资源与对象输入

固定0.135.1/0898d5e3。本轮只静态读取完整WAT/原始data和已有本地资产，新增[资源路径规格](../reconstruction/resource_spec/entry_resources135.py)。**没有执行原件、伪造SELF/VFS/cache、写Once标志或绕过资源初始化。1089入口仍未完成。** [机器报告](2026-11-01-entry-resources0135-static.json)保存39个完整函数body身份、两份静态trace及本地读回证据。

## 第一处阻断真正要读取什么

1089先写phase1，然后调用4546(0)并丢弃返回值。4546首先初始化全局Spell/SpellIcon Once；它并非在此刻加载整张地图。首次正常路径依次经过64B FileSystem构造、`__wenilla_data_base`配置、可选名称索引，再读取：

| 真实链名 | 4546指令依据 | 现有本地字节 |
|---|---|---|
| `DBFilesClient\Spell.dbc` | ptr5305649、len23，第106行前后调用20468 | 16305013B；WDBC22357行×173字段，692B/行；SHA`913d01c0376d88310ed4a44ea1115f30fd8be15af64ce304f4f17b6bc51cf15b` |
| `DBFilesClient\SpellIcon.dbc` | ptr5305672、len27，第192行前后调用20468 | 46442B；WDBC1033行×2字段，8B/行；SHA`938e8c333fe914938994fc331c04655d7eb5719bc2d1b29eaf5fad4239abdfdc` |

两文件都已存在Android静态data中，逐字节等于已验证patch.MPQ索引的对应payload。4546检查WDBC头和长度；本轮独立reader按更严格的完整容器条件读入，没有把这称为执行原4546或证明其全部列语义/缓存构造。

VFS正常读链是20468先查25611内存overlay，随后78412懒加载名称索引，再由48920构建URL、11489进行同步GET。23171优先读取真实`__wenilla_data_base`并去掉尾部`/`；缺失时取浏览器origin加`/data`。索引请求为`base/__index`加真实`__wenilla_data_stamp`，JSON字符串列表按23187统一ASCII小写和`/`→`\`。静态layout把链名按两种分隔符拆分、逐段编码；其它layout编码整条链名。成功GET为200，404进入not-found路径；完整异常/overlay生产者/生命周期仍未知。

现有JS也明确设置static layout/base/stamp，并区分boot-manifest与world-manifest的预取；这些仅暖HTTP缓存，不能据其名称推定完整游戏资源闭包。既有严格probe在获取真实SELF处就抛错，未走到任何文件读取；其部分phase1写入仍不是合法入口完成证据。

## 世界对象先于1560产生

真实producer位于6730的大构造路径。它按152B zone表的mapID和centerXYZ检查App5116缓存；只有App5100的mapID、5104/5108/5112的XYZ都相同时复用world Rc。否则构造116B世界payload，分配124B、strong/weak均置1并把payload复制到+8；随即strong从1增至2，同一Rc存入App5116并作为1560的第三参数。完整ownership/drop尚未独立实现。

该路径直接把mapID映射到Azeroth、Kalimdor、PVPZone01/03/04、MonasteryInstances或Stratholme Raid目录；不是这里查Map.dbc决定路径。它先读`World\Maps\{map}\{map}.wdt`，取MAIN/NIAM的4096项mask，再按中心邻接3×3范围读取存在的ADT。MAIN每8B项的第一个字节低位决定存在，索引是world-x-tile×64+world-y-tile；文件名则为`{map}_{y}_{x}.adt`。

例如Elwynn的真实候选读取从`Azeroth_32_48.adt`开始，包含`Azeroth_33_49.adt`，到`Azeroth_34_50.adt`结束。之后还要处理MCVT高度、ADT对象与碰撞、导航/栅格和世界输出，不能把WDT/ADT存在当成world124已经恢复。SM/Naxx的zone+148标志也与普通区域不同，必须保留。

## 已有资产能满足的明确部分

[本地读回清单](../evidence/entry-resources135-local-inventory-20261101T072438.139967Z/inventory.json)覆盖12个zone的第一层资源请求：**2份DBC、7份WDT、107份不重复ADT，共116份/170383346B**，全部在4T已有MPQ中逐项读出，并与先前StormLib逐字节验证过的索引SHA一致。每份都是唯一archive归属，本组不用猜override优先级；整体MPQ覆盖顺序仍未知。

116条链名全部在既有Android `__index`中，但Android目录实际只持有其中2份DBC；名称索引有条目不等于文件已打包。完整WDT/ADT字节现可由本地独立MPQ reader提供，无需新增下载。

这些ADT声明了1531条不同的候选MMDX/MWMO模型路径。158条可直接在索引找到，1355条在假设`.mdx`→`.m2`别名后可找到，18条两者均未找到。这里尚未证明别名转换、实例选择或哪些路径真正触发读取；不能把所有字符串当必需read-set，也不能据18条候选缺失断言真实入口必定失败。基础包身份仍不等于0.135.1全部最新资产已齐全。

## 4个NPC与2个kind2的真实调用输入

在默认mode0、G2576=0和初始对象向量为空的域，1089先调用1744，再按顺序调用四次5736：每次definition index为0，position Option标志为0。因此由原8751真正采样位置，参数为26、36、0.5；不是手工指定四个坐标，也不是做四次加权选怪。实际world、RNG、G2408计数及全部前置副作用都要续传。

随后两个请求各先调用13516(G,18,50)，再调用1417(G,kind2,amount,position)，amount顺序为2、1。13516按真实地图半径夹取、碰撞/高度执行12次候选尝试及回退路径；1417还会独立按radius−2再夹取并重新查询高度。mode0 kind2闲置上限为5，空向量时这两次都走新建分支；descriptor为(visual9005, display259, scale1.0)，1821的附加参数为(3,0)。kind2的后续收取/选择语义仍未恢复，不能删掉这两个开局对象来缩小实现。

本轮的`default_opening_calls`只提供这段静态调用契约，不执行1744、生成完整对象、模拟原始VFS或完成1089。后续G1964/G1972事件计划、所有UI/对象键/包、真实world完整producer及开局后的全流程继续保留未知。

## 下一次受控验证的边界

本地真实资源字节和第一层路径已经可用；下一步应恢复或执行真实资源/世界生产者并核对其结果，再继续1089。不能通过假SELF返回值、写入全局Once“已初始化”状态或拼造cache指针跳过这些工作。116是资产库存数量，**本轮新增原件玩法差分数为0**，未调用app start、原生EXE、网络、存档或现有安装包。

[当前规格复核](../evidence/entry-resources135-contract-replay-20261101T073037.619657Z/replay.json)再次读回116份资产SHA、重算12区域请求顺序，并做4项本地URL契约检查；它仍不是原件函数差分。独立规格与静态提取脚本本轮冻结，不扩展整个VFS未来资源。
