# fixed139 自然位置采样8740与13563 fallback

**正式80例：完整8740调用63次、显式完整13563调用17次，独立模型与原件XYZ/RNG全部0差异。** 期待世界仅来自独立的新139 raw-assets producer输出，原件侧仅恢复已独审的健康v2上下文；882准确import全部拒绝、实际0调用。整批独立只读复核待完成，不代表完整1108、自然path owner、App或完整游戏已完成。

## 独立规则与当前输入域

新增纯[`world_position139.py`](../reconstruction/core_spec/world_position139.py)、[`position_math139.py`](../reconstruction/core_spec/position_math139.py)与[`world_position139_data.py`](../reconstruction/core_spec/world_position139_data.py)。运行时不读原件、快照或文件，世界是显式height/nav_probe/nearest_primary接口。已验证的139 NPC atan/atan2数值模块作为依赖；未导入旧135位置或trig模型。

`WorldPositionInput139`当前只接纳zone0 Elwynn、有限XYZ/velocity/bias、`0<=low<high<=8192`、4个u32 RNG和显式可选`DistanceMap139`。这里只实现位置/RNG，不修改任何实体、消息、成长、phase或world owner。

8740真实消费G1416/1420/1424、G1736/1740、G1720..1732、G2348 worldRc、G2368 path query view。移动平方和严格>4时先取高24位概率决定bias；bias角为atan2+[-1.2,1.2)，其他为[0,TAU)。范围内sin/cos按原件有序f64多项式再舍为f32，hypot按f64两平方之和→f32 demote→f32 sqrt→缩放，没有调用宿主sin/cos/hypot替代。

每次尝试先取radius，只有radius>=12进入候选检查；最多16次。距离<=zoneRadius+18后查高度：圈内高度差允许<=25，圈外允许<=8。失败radius减2，不重新抽角；低于12才重抽下一次。无path时nav byte1阻挡；有path时非0 nav阻挡，field24<401无需读cost backing；否则要求in-bounds且cost!=65535、cost<=1.5×距玩家距离+12。

16次失败后原件完整转13563。其前12次先把XY夹至zoneRadius，拒绝非0 nav并要求高度差严格<25；第13次不夹XY，也不再按nav/高度差拒绝，height命中取Z，否则primary nearest仅提供Z，再不命中取world fallback。**当前真实Elwynn primary为空，nearest-present分支仅有静态规格，未宣称新的动态通过。**

zone12行数据直接由本版表5871348的+104/+108/+120取得；除Elwynn外均仅静态数据，不动态接纳其他地图。sin/cos角实际范围在[-TAU,+TAU]，大角缩减不在本接口。独立作者另只读核过11425/11499/50441/33028的有限域表达，未执行模型或原件，不替代本批整体独审。

## 来源与真实原件入口

WASM固定0.139.0 / `f79c5e2b4`，SHA `71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299`。8740 body SHA `35e2f8bf141c22a07857ff8327892bf7b6f971aea2d1ad0f705ba12dfa02af38`，ABI `(i32 out,i32 Game,f32 low,f32 high,f32 bias)->void`；13563 body SHA `724158538ddf6fdcb38eb520beaa5ff8467952b418be3400132013b105a136ae`，省略bias参数。builder仅追加两个原件入口和global0导出，其他段与所有callee原始字节不变。

[静态收据](../evidence/world-position139-static-20261102T033613.062984Z/proof.json) SHA `52d2f0cb1afec1ae720337740fac07fab73efc1bbd27a1e8ddcd9498a9852d0d`，8函数/77,479B有界WAT。1740 velocity、2368惰读、半径阈值、RNG、trig、fallback及新zone消费者均按本版绑定，不能把1358751通过转成1398740通过。

期待侧[`load_world_position139_inputs.py`](../scripts/load_world_position139_inputs.py)只解独立139 canonical数据：`asset-world139-owned-20261102T031312.028310Z/model/receipt.json` SHA `46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48`。其453个声明资源中实际加载451项/67,281,330B，从raw139资源生成terrain/nav/secondary，原件/内存输入0。三个canonical SHA分别为terrain `3ecb0d08bc2202524a0b2a86cf43b7a6eba7d201de70f104c4dc675bf1e12b9e`、nav `239b456859bedd6c4e1ebcdf5dadeefc6da66b344ec108e17f8b85819157fd79`、secondary `07c7ab72911e7425456abdbad2a16b3d9fe068db17367996693f70a8be2df1d5`。通用WorldQueries135/terrain数据算法名称保留，139验收重新比较，没有读旧世界snapshot作期待。

期望生成阶段的Python open audit禁止.memory/.wasm/.wat/.exe读取，0违例；之前仅为身份核验流式hash原件/snapshot，不解析或向模型传入其字节。该audit是Python hook，不冒称OS syscall审计。期待文件先冻结，原件输入不含期待、case group或模型诊断。

原件侧仅使用健康v2 `entry-world139-v2-probe-20261102T030946.739944Z/after_real_world6786.memory`，SHA `ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2`；G14685248、App14680072、R20544696。未使用旧5d940的错误夹具。新实例恢复该原件组件上下文，不称fresh world/bootstrap或JS/externref全生命周期恢复。

## 实际差分与字段边界

[正式comparison](../evidence/world-position139-oracle-20261102T035151.444640Z/comparison.json) SHA `eb52328da53d1f90ccba3957f649cd3d52314e20287096e23cac2c46794bb931`。25来源、14production、49本地导入边，生成期待前/执行后完整SHA相同。

语料覆盖真实world静止、非轴bias、8组RNG、边缘位置、velocity平方和4两侧、bias0/1、16次转fallback、13563第13次height和world fallback，以及距离图400惰读/401 cost0/65535/500。radius upper拒绝还用独立逆xoshiro构造使radius draw为0xffffffff，26..36及窄一ULP范围均比对通过。

80份XYZ和四word RNG完全相等。所有80×2592B Game除四个RNG word外逐字不变；真实R124及2318个实际world范围、共5,950,608B的before/after digest一致。原件保留完整Game前后与R124、range metadata。输出分配48B，传中间16B，实际XYZ写12B，余4B保留A5，双侧16B C3/D7全保持。

G2368的非空距离图是显式借用32B query view，不冒称自然Rc/path owner。field24=400时values=None，实际P12/P16保持5A，未读backing；401的cost数组是明确填入的已知u16输入，不是未知项补零。全部query view和数组调用前后保持不变，真实world从未改造成假flat/nav数据。

诊断模型得到5个8740 fallback案例，最大169次radius shrink、最大58个RNG draw；这些是模型分支统计，**不是原件内部attempt/draw计数器观察**。直接执行数只计63个8740和17个13563 export；原件内部fallback callee次数不另加。RNG最终状态和XYZ是原件差分依据。

882准确import全deny/0调用，80个实例恢复；256MiB上限，实际111,804,416B，182次stack guard全1048576。Node79403 exit0、PID/PGID均消失，8.2592秒，自有60秒期限。4例先导收据`world-position139-oracle-20261102T034721.504188Z` SHA `45d31448547a85133128602d524607dac974626157d035ed85d3f3fbffb3450a`独立保留，不加为正式84例；它是修改GC执行包装与补边界输入前的先导来源版本。

## 继续组合的边界

完整NPC四连必须按“每只8740取位置→5719其余RNG/记录/消息→下一只”交错，不能先采四个位置再统一耗NPC RNG。下一组合将只新增独立wrapper/原件实验，保持本批和既有NPC源冻结。

自然distance-map生产、其他地图/primary-present、极端finite/非finite数值分支、完整1108全部实体/窗口/通知、App与完整游戏流程仍未验收。数据/函数差分不替代这些未知项。
