# fixed135 fatal40：异作者只读独审

本批在明确输入域内通过。原作者 `stats138_review` 的 18 次完整5620、22 次完整1073共40例，全部冻结期待与实际原件输出均由本次独立读取器重算；新增原件调用0，未导入或执行 production、原作者 checker/builder，未更改原件、旧模型、primary、registry 或 shared headless。完整游戏目标仍未完成。

原批：`evidence/player-death135-oracle-20261101T235258.508019Z/comparison.json`，SHA256 `f4c71af5b092d629812c8084a7cf9daab96292151739059b1fb80393013e9c08`。本次独审：`evidence/player-death135-independent-review-owned-20261102T000645.796312Z/review/review.json`，SHA256 `99e1d1ca91cd52941f8a6f37e14aaa1f9f91862b5be55e22adb287b3f02f96d3`。读取器 `scripts/review_player_death135.py` 的最终SHA由同名JSON绑定。

## 独立恢复与核验

- 从固定135原件二进制重新解析函数签名、函数体和section。私有模块仅变更export section7，添加1560、5620、1073与stack0出口，全部原件代码段逐字不变。13个相关原件函数及45845序列化器共14个函数的WAT按SQLite只读索引有限读取，未读取完整WAT。
- 独立确认1073先扣除HP、累加f64 taken、形成history，再经过minimum-one、intrinsic raw12、modifier31及剩余生命数分支。真实lives0路径写HP1440=+0后调用5620；5620自身写phase2587=4、paused408=1、paused-time412=now，mode0调用17119，再生成1938 defeat通知。17119尾部真实调用17217和16340。
- 重算三域停止条件、逐步binary32插值、flat-height分支、全部动作存储和未写字节，确认NPC、auxiliary、claim各停止9个对象，共27个221包、513个有效载荷字节。movement2412先递增再编码、包含u32环绕；action1644保持不变。本批没有232胜利包。
- 18个直接5620完整扫描46,656个Game字节；26个新heap指针字单列为实际分配观察，不声称独立预测地址。22个完整1073扫描57,024个Game字节，同时每例明确保留8个registry观察字节和4个history分配指针观察字节；其余变化与未变化字节独立核对。没有把未知registry布局算成已恢复。
- 重算完整23,712个motion backing字节，包含87个未触发停止的记录。额外从原始谓词独立构造稀疏输入并执行本审查器自己的惰性解释器：152个已知字节与同case1原件实际值匹配，1,096个None保持未知。这是既有case1投影与模型保留性质，不增加原件样例数。
- 完整40条defeat JSON共14,380字节，字段顺序、英文fallback、unsigned counters、UTF8/control escaping、52241数字格式及Vec容量增长均独立逐字匹配。Mage/Human/Elwynn Forest等标签、Melee及INV_Sword_04从原件data段读出；Mage基础HP215、Human只含XP/gold两项调整另行核对。
- 22条真实incoming48 history的748个已知字节、header(cap4/head0/count1)、三条字符串均独立核对。输入sourceGUID恒0且没有匹配NPC，history source为空、rank4；其余实际pointerword和padding仅为观察。未导出的3个空闲history槽继续保留None，未声称完整history backing比较。

## 1367的作者边界

本审查器作者曾实现 production1367，不能把自己的重算算作异作者独审。12条left0通知消费由 `self_buffs119_review` 的纯独立reference计算；该reference已对103个完整1367实际调用逐字重算，包含ring400、last8/top6、排序、聚合、UTF8与容量。

依赖报告：`reports/2026-11-02-player-death-recap0135-independent-review.json`，SHA256 `1625cc4628bbb215121e6a5f770bed12f090896c7fcace6b17d9a38b29af6b88`；独审证据SHA256 `9a0b879daa2d18d2b87d3d56786134f4497c0348d32acc338ae353310b7a6dcf`；pure reference源码SHA256 `b0c92d1116587a58022028844e2bf24d4fc259d6faec092708f9c5d6f2a7b088`。这里不新增1367独立恢复信用，也不把103例重复计入fatal40。

对单条active history，reference使用原件导出的active48逻辑投影；先核所有被消费的标量/字符串，再将逻辑容量0/1的等价有序视图交给reference。实际canonical cap4的3个空闲槽仍为None，没有补0或宣称读过未导出内存。真实408=1和412=now与1938选择reference time的静态分支一致。

## 收据与限制

27个冻结源、20个production源、73条本地import边，当前文件与冻结snapshot、before/after/prepared均一致。期待文件在启动原件前冻结，input不包含expected。原件进程74333在1.162秒内exit0、PID/PGID消失；40次fresh1560为单列setup，18个5620和22个1073为目标调用，内部5620数量来自静态路径而非插桩。host调用0/878deny，337次stack guard通过，内存峰值20,578,304B，32MiB限制有效。本次独审进程92380在0.656秒内exit0、PID/PGID消失。

保留三次审查器自身失败与一次中间通过，目录及hash在JSON中列出：首次984 WAT切片上限过小；第二次把221 literal误定位在17119而非45845；第三次新增稀疏解释器提前读了inactive NPC的未知start340，已按原件短路顺序修正。没有修改作者冻结源或原始失败材料。

实际构造器innate kind为8；原作者期待边界使用9。两者均在原件 `kind!=12` 分支跳过cooldown读取，本批逐例验证actual8及该谓词等价，未声称二者数值相同。16个负向guard是作者模型自检，本次仅静态核边界，不重跑、不计原件差分。

本批限定fresh1560后显式fixture、phase1/mode0、HP致死、minone0、innate非12、modifier31缺席、lives0、空live/item/modifier/callback域、sourceGUID0未匹配、英文fallback及明确无terrain/collision或flat-height。没有验收intrinsic12复活、modifier31、剩余生命复活、mode1、真实非平坦地形适配、自然callback/source-registry producer、完整App、Windows动态行为或完整游戏流程。
