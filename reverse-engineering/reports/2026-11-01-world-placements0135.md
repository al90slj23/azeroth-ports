# 独立 ADT 场景对象与真实 world 实例选择

新增可执行 [world_placements135.py](../reconstruction/resource_spec/world_placements135.py)：从实际 WDT／ADT 文件字节产生 M2／WMO placement，再按原6730的顺序和范围规则生成碰撞实例输入。完整原1446新增 **13例／13次调用／0差异**：9份真实 Elwynn ADT，加4组有效 canonical 控制输入。完整 world、渲染和独立一局尚未完成。

[最终原件收据](../evidence/full0135-oracle-20261101T110558.641205Z/world-placements135-comparison.json) SHA `b4225466e0a41e217d00c214415d42addb57bdf9d2a3e57ad3db74b9140c197a`；[机器报告](2026-11-01-world-placements0135.json)保存冻结源码、原件身份、运行边界和未知项。此前1例 pilot 另存，不叠加为本轮14例。

## 完整1446的 placement 投影

原1446输出两个有序44B向量。每条记录的 String 指针保留原值作观察，比较真实 UTF8 字节、String容量／长度及其后的全部8个32位数值字；向量容量／长度也严格比较。13例总计11,649份 M2 与76份 WMO记录，严格核对1,181,761B数值／字符串字节，没有浮点误差放宽。全部44B backing另存；254,100B非活跃尾部保留为未知，其中405B非零，不填零冒充已恢复。

实际9份ADT独立产生8,512个M2和45个WMO原始placement。`MMDX/MMID`、`MWMO/MWID`恢复文件名，`MDDF/MODF`保留各自源顺序；名称索引超出已解析名称表时跳过该条记录，已由控制输入原件重验。四组控制输入另验scale的0／1／1023／1024／2048／65535、跨32位uniqueID、正负零／坐标交换、Euler字、WMO非零sets，以及多个offset指向同一合法字符串。

坐标换算为 `(f32(17066.666015625 − sourceZ), f32(17066.666015625 − sourceX), sourceY)`，旋转三字保持原Euler顺序；实际18572负责后续基底／旋转变换。M2的scale为源u16除1024，uniqueID来自源+4；WMO碰撞scale恒1、uniqueID同样源+4，record+40保留 `u16source58 | u16source60<<16`。没有把MODF的包围盒、flags或渲染doodad选择猜作已还原语义。

原13850的有效名称规则也独立落地：259B以内的MDX／MDL／M2后缀转换为ASCII小写basename加`.m2`，WMO经既有canonical路径规则处理。原1446返回的原始`.mdx`名字继续保留；实际31条MDX转换结果与历史原件请求吻合。MDL／M2和超长路径分支只有静态依据，本批没有新增对应原13850直接调用。

## 世界实例选择与历史读集复核

纯 [planning入口](../scripts/plan_world_placements135.py)只接真实文件provider，不读取原件内存。最终[计划收据](../evidence/world-placements0135-plan-20261101T110820.988358Z/plan.json) SHA `4a017d870c130ec0daa433b330d7f04a69e53b09281e91a7390759c0f0e72643`，10份传递依赖源码前后一致：

| 原6730 pass | 独立规则 | 实际Elwynn结果 |
| --- | --- | --- |
| nav_m2 | 两轴严格小于 `extent + 40×max(scale,1)`，再按uniqueID首次保留 | 244实例，31资源链 |
| nav_wmo | 两轴严格小于 `extent + 400`，独立uniqueID集合 | 14实例，10资源链 |
| secondary_wmo | 不做前述XY过滤，独立uniqueID集合 | 36实例，23资源链 |

运行顺序为M2导航、WMO导航、WMO secondary；WAT中文本靠前的9513分支不能直接当作实际执行顺序。9ADT顺序和每个文件的原placement顺序全部保留；距离外的重复ID不占用集合，后续距离内同ID仍可入选。

31条M2首次请求、nav加secondary的23条WMO root首次请求，以及其后按root/group原序展开的410条WMO首次请求，逐项与此前真实6730的453文件读集相同。这个复核新增原件调用为0，不算新的完整6730独立差分，也不证明所有实例效果或完整world等价；它使后续world缓存构造能从真实资产产生明确实例，无需拿原版快照提供placement。

## 执行边界与接口

原件只执行未改body的完整1446与内部callee；复用已有shared52中的`adt_parse`角色，没有扩展白名单。14份完整fixture／模型源码先冻结；原件input仅含id及真实asset路径／大小／SHA，不含expected。每例fresh实例，32MiB WASM上限、单块4MiB、512MiB Node heap、独立进程组60秒上限；878个导入全部拒绝，实际宿主调用0。峰值26,738,688B，PID／PGID95177 exit0后均确认missing。无EXE、app start、网络、原用户存档或安装包操作。

`load_world_placements(map_id, center_xy_bits, provider)`返回有序`(ADTname, AdtPlacements135)`；`select_collision_instances(..., phase=...)`返回稳定`Placement135`，含实际chain、XYZ、Euler、scale、uniqueID和源记录位置。后继缓存模块可直接消费这些输入。复现命令：`python3 reverse-engineering/scripts/check_world_placements135.py --phase full`；历史计划为`python3 reverse-engineering/scripts/plan_world_placements135.py`。

未知项保留：其它地图／模式和完整107ADT、格式错误恢复、原VFS与cache所有权、场景渲染／动画／材质、完整world主／secondary栅格及nav后处理、开局接主切片、存档／UI／联机和独立完整一局。此批不增加旧1,614帧计数。

[独立只读复核](2026-11-01-world-placements0135-independent-review.md)已通过，最终review SHA `341f3b3fccf1393fc6078f1864a4d0d5620d69b7359a4a3e1309792dcac562a1`；没有新增原件调用或扩展原批范围。
