# 官方0.134.0：拾取XP、等级/pending与选卡入口

本报告固定 **0.134.0 / 983346a7**，原件SHA-256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52`。使用新版完整WAT/SQLite，数据库只读；全程仅解析字节，没有实例化WASM、调用游戏入口、联网、读取存档或修改APK。完整函数WAT/body与连续指令guard保存在 `evidence/progression0134-chain-20261101T010336.314496Z`。运行时样例数为 **0**。

## 已恢复的真实链

`2862(G) → 4630(G, amount) → 每级1513(G) → 27959解析level_up原因 → 10847治疗 → 1453副作用 → 末尾真实守卫 → 2159(G,0,1)`。

历史3231职责由新版**4630**承担；历史2098职责由新版**2159**承担。这是新原件调用、字段和连续指令所建立的角色对应，不是编号算术平移，也不声称整函数等价。新版round **85718(f32)→f32** 的68B body哈希与历史85387相同。

2862按G+1864/1868遍历56B拾取记录，从record+8读kind、+12读amount，先保存amount再调用31731移除拾取。`kind-1`的无符号br_table默认臂使kind0进入函数行1099之后的XP分支，脚本实际解析嵌套block终点核对。普通mode0令局部倍数为1；随后按原顺序计算 `round85718((G.f32(1388)*f32.u32(base_amount))*modeMultiplier)`，NaN选择1、再取至少1、最后trunc_sat_u32，传入4630。mode的多人调整和完整拾取几何没有做独立数值规格。

4630签名是 `(param i32 i32)`，参数0为G，参数1为XP增量的u32位解释，返回void。**入口没有phase限制**，先写 `G.u32(1524)=wrap_u32(oldXP+amount)`。循环读取 `G.u32(1520)`，阈值保持每步f32原顺序：

```text
n = u32_to_f32(level - (level != 0))
threshold = trunc_sat_u32(R85718((n*4+5)+(n*f32(0.35))*n))
while level <=u 119 and XP >=u threshold:
    level = wrap_u32(level+1)
    XP = wrap_u32(XP-threshold)
    pending2368 = wrap_u32(pending2368+1)
    原属性重算、keyed state、消息和治疗等副作用
    重新读取XP
```

**新版自然升级上限为120，旧版是99。** 已大于上限的输入不会夹回120；amount0仍可消费已有XP，XP和pending加法仍绕回。旧模型的阈值公式与helper算法可以作为迁移起点，但`level<=98`、99级边界和旧运行时数字不能作为新版验收。

每级先写level1520、XP1524、pending2368，再更新key34并调用1513。重算前快照maxHP1360、damage1364、regen1396和计数1428，随后生成16B消息到G+1872/1876/1880。之后从静态descriptor1588144解析 `level_up / system / known / Level Up / Spell_Holy_HolyBolt`，以重算后maxHP的20%请求10847治疗；10847更新currentHP1528，再以实际治疗差值调用1453。循环外仍更新key716(XP)和717(新阈值)。这些副作用仅追踪并保留原body，未独立重建。

末尾调用2159的完整守卫：

```text
pending2368 != 0
&& phase2579 == 1
&& !(byte2568 & 1)
&& (byte2564 != 1 || (byte2565 & 1))
→ 2159(G, 0, 1)
```

2564要求精确等于1；2568/2565只看bit0，非规范字节2不能统一当true。2159参数1按低8位分发选择种类，参数2非零时在生成后的路径写phase2579=2；同时写selection_kind2577与增加counter2392。本报告保存2159完整body和守卫，**没有实际生成候选，也没有验收候选内容**。

## 阶段3受控fixture的静态迁移边界

可复用原分配器分配合成G、清空辅助容器、禁止host imports、直接调用XP核心的方式。新版应从已验证导出91940分配，或采用后续harness允许的internal106890；建议沿用现有新版fixture的8192B分配额度。class/race读取仍在byte360/361；player GUID已是u64 **G+1336**；level/XP/pending改为1520/1524/2368，phase改为byte2579。消息Vec是1872/1876/1880，owned是1652/1656/1660，items是2020/2024，modifiers是2044/2048，keyed-state树是2468/2472。

把phase2579设为3，只会通过4630末尾真实守卫阻断2159；XP循环、1513、消息、keyed state、10847/1453仍然执行。后续比较字段可以限定为level1520、XP1524、pending2368和phase2579，但这不能声称覆盖其他副作用。需要把120级停止、119级阈值前/等于/后、120级及更高输入、加法/pending绕回、多级升级、零增量纳入新版语料。selectors=1/1、GUID=1及空辅助状态只是待运行提案，本轮未验证可执行性或host调用数。

## 完整提取函数及身份

| 函数 | 新版WAT签名 | body字节 | body SHA-256 |
| ---: | --- | ---: | --- |
| 2862 | `(func (;2862;) (type 3) (param i32)` | 3179 | `502221f3e34228e0a37970e55505d1506f323d2c5f81510b707d8d8e414122ef` |
| 4630 | `(func (;4630;) (type 0) (param i32 i32)` | 2001 | `4bd68b70d90f63e0a25b63378f10a9a68adcaf275fdffd489462aa7541d1a110` |
| 85718 | `(func (;85718;) (type 55) (param f32) (result f32)` | 68 | `3f9127d30eefb0c9bad49101460ed45df1f6069e63c42d87e351ffbb67151c36` |
| 2159 | `(func (;2159;) (type 1) (param i32 i32 i32)` | 4377 | `555c0ff77e67864d3af4b149f1fb3d24f82e96a777d6537c32c6170ade8398dd` |
| 1513 | `(func (;1513;) (type 3) (param i32)` | 4748 | `e978d8b2c80f495f3c669c957444b4392368fe87dc92104b297482163c3b419e` |
| 10847 | `(func (;10847;) (type 154) (param i32 f32 i32 i32 i32)` | 1050 | `bbee12cd6ad1947b45d47cbd5dc4e90b39a140e7b58f60f96f5c0c312a860393` |
| 1453 | `(func (;1453;) (type 154) (param i32 f32 i32 i32 i32)` | 5872 | `a3f6a6f5ff104ca462767cf4159a98ac001c8b20ad30aa8284784661333f87e2` |
| 27959 | `(func (;27959;) (type 1) (param i32 i32 i32)` | 507 | `a1a32b5151d543adc27d759c42749931632125b7f8675e010620ecd36bdd1059` |
| 3735 | `(func (;3735;) (type 0) (param i32 i32)` | 2092 | `a74c80160cb7cd545f993cbf932d40c9bcf9e4e692251615487da71fed6b4b7b` |
| 65323 | `(func (;65323;) (type 3) (param i32)` | 109 | `2aa59e719779d28fd832bff816892902f6518c260fdd1b5cac023e65fe060802` |
| 91940 | `(func (;91940;) (type 6) (param i32 i32) (result i32)` | 49 | `a2bd06e7d00364b8cbc8c90ad97ef66d56ac33189f4371b17ac181efaf669392` |
| 106890 | `(func (;106890;) (type 6) (param i32 i32) (result i32)` | 24 | `1782ebdd04fb0487495727392c4ff80dafbfbd6c4886aade5aaac14e0ac68575` |

原件SHA-256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52`；profile manifest `952e2cd4c1fdb0bbf62cf44d6cf4f265ae15120a1572facaad23b43ff4fc51b9`；完整WAT `6014dab110e40ae279a6450ae15dcc0d84727c31e2da71f18f2cab1f21ec8422`；SQLite `f131b4454ac1a8754f5b0417e4192efbaada6478df737e09490154c71fd340f9`。JSON还包含每个函数的二进制与WAT起止偏移、完整WAT行号、所有guard命中位置和直接调用位置。

复现：`python3 reverse-engineering/scripts/trace_progression134.py`。该命令只做静态解析与忽略目录证据写入，不运行原WASM。输出的JSON和本报告仅说明静态恢复范围；实际候选生成、UI、存档、APK和新版full original fixture均未验收。
