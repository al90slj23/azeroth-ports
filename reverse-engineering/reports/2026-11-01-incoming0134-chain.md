# Official 0.134.0 / 983346a7 玩家受伤1063与IceBarrier

本报告只绑定新版原件 SHA256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52`。已保留完整1063、922及七个相关消费者，恢复完整1063的可见控制流、标量算术和副作用入口；**没有运行任何 WASM，尚无完整1063差分案例**。旧版1107只用于导航，不计作新版验证。

独立模型 [incoming134.py](../reconstruction/core_spec/incoming134.py) 只依赖标准库和binary32。它实现入门guards、模式/armor/两种距离减伤、已知盾消费前缀及“给定已计算candidate”的barrier替换。结果明确输出 `returned` 或 `pending`、原函数阶段及尚未实现的消费者；`core_hp_write_L1793` 是中途标量状态，不能当作完整1063返回状态。生命保护、复活、事件、容器及所有后继效果仍须继续独立重建。

## 原件身份与可复核入口

1063签名为type273：`(i32 G,f32 amount,i64 sourceGUID,i32 raw3,i32 raw4,i32 raw5)->void`。本报告中的 `L` 是完整单函数WAT的1-based行号；JSON同时保留其在完整WAT里的行号。原1063 body范围 `[5601777,5614102)`，12325字节，SHA256 `e6ea2aaca5f6d402fe5969f637e1b2cad398f2e2b3250b18c4fd0950d3ac59bf`；其5888行完整WAT SHA256 `c916ae5af9d5cd3d9e9acb4645cc63816052157377a120bbc5d94a13693a7808`。

完整1063/922与辅助38322、58020、27959、1453、1202、984、5620均来自只读index定位、按原件body范围重新提取。1063/922完整body和WAT另外用既有固定hash复核，33段原件region逐行保留全部指令和region hash。原件、完整WAT、index、静态reader在提取前后重验；未使用callee stub或修改现有builder/host。

## 入门、模式、减伤与距离

1. `G.u8(2579)!=1` 或 `(G.u8(2568)&1)!=0` 直接返回。
2. 当 `G.u8(2574)==1`，按如下完整顺序缩放输入；0.8是本版固定乘数，但仍有map/wave动态部分。

```text
b = call38322(G.ptr184,G.len188) <u 3 ? f32(.7) : f32(1)
n = f32.convert_u32(wrapping_sub_u32(G.u32(2532),1))
t = f32.mul(b,n)
t = f32.mul(t,f32(.064))
t = f32.add(t,f32(1))
t = f32.mul(t,f32(.8))
mode_amount = f32.mul(input_amount,t)
```

38322是精确字节查表：`elwynn,duskwood,wsg,ungoro,ab,feralas,arena,sm,av,brm,aq,naxx` 分别返回raw0..11；不认识的字节串返回0。因此未知map也通过 `<u3`。`2532=0` 必须先u32回绕到4294967295再转f32，不能改成负1。

3. 扫描32B buff向量 `G1704/G1708`；任一 `record.u32(+8)==12 && record.f32(+24)>entry_now` 直接返回。`entry_now=G.f32(2344)`；严格比较，NaN不通过。
4. `damage=f32.mul(mode_amount,f32.sub(1,G.f32(1392)))`。没有armor clamp，没有敌人914的最少1规则。
5. 仅当 `G.f32(1444)>0` 且至少**五个** `unit.u32(0)==0` 单位距玩家平面距离平方 `<=64`，再乘 `f32.sub(1,G.f32(1444))`，只乘一次。原件是展开的五层搜索，不能解读成存在一个附近单位即可。
6. 顺序扫描36B `G2044/G2048`，选择第一条 `rawtag_u32(+0)==54 && u8(+4)==1`。只要有一个marker0单位距玩家距离平方 `<=49`，乘 `f32.add(f32.div(f32.convert_u32(u8(+5)),-100),1)`。不累加后续54；u8允许0..255，比例没有截在0..100。

玩家XY为G1504/G1508。单位424B、marker+0、开始XYZ+316/320/324、终点XYZ+328/332/336、移动起时+340、duration+344。当 `!(duration<=0)` 时按 `t=(now-time)/duration`，先select小于0为0，再select大于1为1，坐标为 `start+(end-start)*t`，每步f32；duration为NaN也进入插值，NaN t经select保留，NaN距离不通过 `<=`。duration<=0直接用终点。58020与展开版顺序一致。

## 总盾、来源、IceBarrier消费

只有 `G.f32(1532)>0` 才进吸收块（L784起）。此处的 `minNum/maxNum` 均指原件select序列，单个NaN时选另一个数；不以传播NaN的 `f32.min` 擅自替换。有限值相等时保留该序列的选择顺序。

```text
absorbed = minNum(old_total_shield,damage)
G1532 = f32.sub(old_total_shield,absorbed)
G1536 = positive_or_zero(f32.sub(old_barrier_component,absorbed))
```

`positive_or_zero` 明确先NaN→+0，再仅保留严格正值。**没有先把damage或absorbed clamp到非负**：负伤害可增加盾与barrier，NaN伤害在正盾情况下会吸收整个盾但残余仍NaN。总盾不正时，barrier和来源字段完全不进入这个吸收块。barrier组件每次扣去的是本次总吸收量，未按其他来源优先级分摊。

随后维护 `G.u32(1344)=source_spell`、`G.f32(1348)=source_remaining`：

- source非零：`spill=positive_or_zero(absorbed-old_remaining)`；`source_depleted=(old_remaining<=absorbed)`；耗尽则source与remaining均清0，否则remaining做f32减法。
- source为0：remaining仍直接减去absorbed（可变负），`spill=absorbed`，source_depleted=false。
- `reserve_used=minNum(G768,spill)`。仅当其 `>0`，先扣G768，再调用27959/1453；之后重新读总盾和reserve。因此不能把调用前HP视为最终扣血使用的HP。该未重建回调在模型中返回pending。
- reserve最后写成 `minNum(current_total_shield,current_reserve)`。
- 若total_shield<=0：清barrier1536、将1344/1348整8B清0，稳定过滤掉所有buff rawtag7；若只来源耗尽：过滤所有spell+20等于旧source的buff。随后调用1202。模型在这个回调前返回pending，不伪装其完整效果。
- `damage -= absorbed`；`G740=absorbed+G740`，`G744=maxNum(old_total_shield,G744)`。总盾或来源耗尽时将740/744两字段一起清0，并取刚才两统计的maxNum；若不是 `<=0` 且36B向量非空，构造含raw packed-u16=1536的记录，调用984。这是HP写入**之前**的事件消费者。

1202、1453、984完整body均已保留；它们的所有容器、属性和传递影响没有在本轮逐个重写。984直接可调用914/922等，所以不能把它当作只追加日志。

## 施放922中的IceBarrier替换与上限

922的spell11426分支写入barrier1536，且敌人914完整函数无1536/11426引用。两条路径不可混为一谈。对完整922建立保守结构化CFG、保留所有条件双臂和br_table目标后，L5311前局部25/26/27/28的唯一reaching-definition分别为L4414/663/684/688。因此该支candidate可确定为以下有序公式，A是本次能力记录、D是其definition；**不包含G1364伤害属性**。raw effect7路径先置局部25=`A76*D4`，并在已有同spell buff时直接拒绝；上游共有施放条件仍须另行恢复。模型尚未实现sqrt与完整cast，要求提供**已经计算好的candidate bits**。

```text
a = f32.mul(f32.sqrt(f32.mul(A.f32(12),A.f32(52))),f32(1.4))
b = f32.mul(G.f32(1360),f32.mul(A.f32(76),D.f32(4)))
candidate = f32.mul(f32.mul(a,b),f32.add(G.f32(1424),f32(1)))
```

11426替换标量顺序可完整恢复为：

```text
other = positive_or_zero(G1532-G1536)
replaced = G1344==11426 ? +0 : G1348
other = positive_or_zero(other-replaced)
base = f32.max(f32.min(other,+0),+0)  # 此时other已非NaN且非负，精确为+0
available = positive_or_zero(G1360-base)
candidate = candidate<0 ? +0 : candidate
granted = available<candidate ? available : candidate
G1536 = base+granted
G1532 = other+granted
```

随后L5439–5447写 `G1348=granted`、`G1344=definition.u32(+44)`；完整cast的buff/packet/mode分支仍pending。有限非负maxHP与candidate时，新barrier≤maxHP；**总盾并不要求≤maxHP**，它还包含other。例如total80/barrier30/source11426/maxHP100/candidate150，结果barrier100、total150。若旧source是其他spell且remaining20，则先在剔除barrier后的50中再剔除20。candidate为NaN时最后严格比较为false而选candidate，NaN传播，不能擅自归0。这个cap不是敌人914的maxHP/5特例。

## HP写入之后的完整控制流与未完成部分

HP之前还有sourceGUID扫描及定义registry：单位表 `G1780/G1784`、stride424、GUID+112；命中且raw244!=-1时，通过unit+256指针的+32值去重加入G1196/1200/1204向量。sourceGUID=0且空units可以跳过它。

L1777–1793写 `G1648=entry_now`；**重新读取当前G1528** 后减去残余damage；`G.f64(992)+=f64.promote_f32(damage)`。统计没有按旧HP上限截顶、没有非负/NaN修复；过量、负值和NaN与敌人914有显著差别。

L1794–3628之后是source label的有序统计树和48B rolling history。静态字符串有直接原件字节依据：`area`、`boss spell`、`boss melee`、`mob spell`、`mob melee`、`elite`。ring字段为capacity968/pointer972/head976/count980；会丢弃过旧（严格 `<now-10`）或多于399的旧项，再追加当前项。记录含mode前后逻辑产生的残余伤害+28、absorbed+32、当时HP+36、maxHP+40等。raw4/raw5仅按原参数使用，不据名称猜tag。

L3629以后扫描尚未过期raw buff13，按顺序从-0累加+12。sum>0、sourceGUID非零、raw3非零时反击914：`damageStat1364 * (sum*(1+G1424))`，spell取**第一条raw13**的+20（该ID搜索没有重复expiry gate），school3。第一次914后还检查phase2579==1。

同组随后累加8B item向量中rawtag22，sum从-0开始；当mode-scaled amount>0且sum>0，暂存G774并设为3，以 `mode_amount*sum`、spell467、school3调用914，再恢复G774。这里使用的是armor与吸收**之前**但mode之后的amount，而不是残余HP伤害。随后构造两条984事件记录。sourceGUID为0或raw3为0时整组可跳过；事件的完整传递、反击死亡触发、RNG与包队列均pending。

最终再读HP：若G.u8(2570)非零，NaN改1，并取至少1，写回1528。仅在此后的HP<=0时进入下列有序链；NaN不会通过致死比较：

1. **当前能力raw effect12**：立即解引用 `G.ptr1256`；仅当definition.u32(0)==12且 `!(G1264>0)`，将HP暂置1，复制G1256..1332能力状态到栈上，调用完整922。返回0恢复原先致死HP；非零则成功分支跳过其余复活fallback。该分支的HP取决于922，不在此猜为固定恢复量。
2. 成功922分支把G1264写为select型maxNum的cooldown**下限**：一般0.25，精确ID `hellfire` 为0.5；`divine_shield` 为 `10-minNum(6,((definition68*1.4)*G1284)*G1324)`。再和 `(((definition52*1.4)*G1272)*G1312)*G1368` 取原select型maxNum。同时发cooldown与opcode309记录；完整包实现pending。
3. **第一条raw31**：若存在且 `!(G748>current_now)`，写 `G748=current_now+record.f32(4)`，HP=`record.f32(8)*G1360`。record.f32(12)>0时附加raw buff12 / spell1856 / expiry=`current_now+parameter12`，否则走另一消息/984分支。原件文本分别包含`%s cheats death!`与`%s refuses to fall!`；不据此替raw31命名。成功后跳过remaining-life fallback。
4. **剩余生命G1628**：0则HP写0并call5620；5620的开头直接写phase2579=4、G408=1、G412=当前时刻，后续按mode执行结束流程。非零则u32减1，HP=`G1360*0.5`；删除spell1020的旧buff并追加raw12/spell1020/expiry=`entry_now+2`，call1202。接着收集marker0且平面距离平方**严格<144**的单位，逐一以 `G1364*200`、spell15237、school1调用914，随后释放临时GUID数组。各914可有死亡副作用/RNG，并非单纯改玩家HP。

所有正常继续至末尾的路径将HP做NaN/负值→0、ceil、u32饱和编码，写G2468字段树的key22；maxHP1360直接ceil/u32饱和写key28。模型没有把这些字段map、缓冲区与发送队列冒充已独立实现。

1063本体无1712/1716/1720/1724直接RNG访问；这**不能证明完整1063保持RNG**，因为914、922、984以及5620的传递消费者尚未穷尽。

## 下一步受控full1063输入布局

以下是静态recipe，尚不算成功返回证据。应使用原件真实allocator分配并清零5000B G，不选自定heap地址。原件实例、宿主拒绝、deadline和仅export研究副本由完整harness另行验证。

| G字段 | nonfatal baseline |
| --- | --- |
| phase2579 u8 | 1 |
| time2344 f32 | 10 |
| maxHP1360 / HP1528 f32 | 100 / 100 |
| armor1392、保护2568、最低HP保护2570、mode2574 | 0 |
| units1784、buffs1708、items2024、modifiers2048 count | 0 |
| total1532、barrier1536、source1344/1348、reserve768 | 0 |
| RNG1712..1724 u32 | 1,2,3,4，便于观察callee是否推进 |
| call | `1063(G,10.0,0n,0,0,0)` |

空units跳过source定义registry；空统计根1112走分配；history四字段全0走55796扩容；字段map2468空根走3735插入。GUID0跳过914/984反击/事件组，HP90避免G1256解引用。对这条baseline未发现静态必然无效的容器分支，但需要完整原件实际返回才能确认。

先验收无盾非致死，再增加partial shield total50/barrier30/amount10、source=0/reserve=0；接着单独测试shield耗尽、source11426 remaining5/10/20，以及reserve回调。单位及buff/36B布局和精确观察字段全部在JSON。致死前必须先提供有效 `G1256` 能力记录指针，**不能把zero pointer当成无能力sentinel**；G1256在lives fallback之前就被解引用。

后续full fixture至少逐位比较HP、total/barrier/source/reserve、740/744、f64 total992、time1648、phase/lives、buff向量、包队列、history、field22/28与四字RNG；不同路径分别报告成功返回与宿主调用，不能仅比较prefix HP就算full1063重建。

## 复现与验证层级

```sh
python3 reverse-engineering/scripts/trace_incoming134.py
```

脚本执行静态原件/完整WAT/index身份复核、九个完整函数重新提取、33个region guards、barrier局部变量保守CFG reaching-definition检查、strict JSON写入/readback、24个独立Python边界断言。断言覆盖五单位阈值、距离边界、raw54首条选择、guard严格时限、负伤害、barrier消费、单组件cap与回调pending。它们是模型内部验证，**原件运行案例仍是0，不构成差分等价证明**。当前证据目录和script/model/所有函数hash见同名JSON。未运行WASM、游戏start、host/network、APK、存档；未commit/push。
