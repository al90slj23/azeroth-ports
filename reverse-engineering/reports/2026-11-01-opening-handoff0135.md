# 固定0.135.1空account companion生产与opening交接

已恢复显式空account flags→两条tag255 absent companion→完整独立opening→保留所有owned state的交接。固定原件为0.135.1／0898d5e3，SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。本报告不将结果转记为其他版本通过。

最终[receipt](../evidence/opening-handoff0135-20261101T143030.053754Z/report.json) SHA256 `02b744c72090393b0ec721f052278b450c09ed7ef2cacfa0e91654a9dc350baf`：16个受控case、594个模型断言、0差异；完整6730调用16次、完整1089调用16次，0次新增完整880帧、0次fresh App bootstrap。52个来源文件前后相同。原件全部878个导入被拒绝，实际host调用0，未读写用户存档或安装封装。

## 独立slot255来源

[静态trace](../evidence/profile-companions0135-static-20261101T142845.620902Z/trace.json) SHA256 `94fe72c1c55a3a9311d0bd4dd195c7151a810688cd4b1ed794f9c98cd9638d0a`保存6个完整函数、18段逐字校验的指令及原始body范围/hash。分析前校验固定官方WASM及完整WAT SHA；未执行原件。

1. 2922读取account+240/+244的16B flags向量。显式count0使两条companion entitlement布尔保持0；函数行590..600将local11和local10置255并在definition查询前离开，行1168..1176写输出+12/+4。
2. 880将2922的36B结果经临时4648、1488复制到App+3600；相应slot tag为App+3604/+3612。行6386..6389明确设置local111=App+3600，行13416..13435执行复制。
3. 6730将App+3600/+3608重排至selected376+224/+232，tag为+228/+236；1560将selected376复制到Game+16，得到Game+240/+248两slot，tag为Game+244/+252。
4. 1744遍历Game240..256的两条8B记录；在解引用definition及增加counter之前跳过tag255。1089先调用1744，再产生四个NPC、两个kind2和边界对象。

新模块[profile_companions135.py](../reconstruction/core_spec/profile_companions135.py)只承诺这段空flags分支。`EmptyCompanionProfile135(())`明确声明来源；`AbsentCompanionSlot135`只写语义tag255，未消费的pointer/entry/display/scale保留None。非空account、权益、选中definition及其余profile字段尚未独立生产。

## 独立producer与受控原件差分

独立expected只读取既有451个真实资源产出的、逐hash校验的terrain/nav/secondary查询产物。没有读取任何原件memory或原件输出作为独立opening生产输入。输入和expected先写入并固定hash，再启动原件进程。

私有[oracle runner](../scripts/run_opening_handoff135_oracle.mjs)只在真正App上声明两条输入tag255，完整执行6730，验证constructor输出Game244/Game252仍为255，随后完整执行1089。没有在constructor后修改phase、counter、RNG、向量或保护位。此动态测试覆盖完整6730/1089，但2922仅有上述静态证明，未被该oracle执行。原件仅使用历史已解析world快照恢复，不是fresh完整App启动。

复用旧`check_opening135.compare`，对六类vector的count/capacity、所有known backing字节、RNG/counter、XYZ、全部opening packets/notification逐项比较。16case共严格比较31,472个known bytes、1,216个packet／129,792B及16个start通知。9,152个active unwritten bytes和9,552个inactive allocator bytes仍明确None；原件实际非零值分别8,085／7,724，均保留在独立的原件raw结果中，未用零值伪造独立分配器。None掩码没有放宽。

seed0、class1/race1、GUID0时：phase1、clock0、counter85；NPC GUID低24位11..14，kind2为15/16，边界17..85。RNG为`3253128260,1876369536,2014361798,3839958702`。开局76个packet／8,112B。

| 物理向量 | count | capacity | active未知字节 | inactive未知字节 |
|---|---:|---:|---:|---:|
| companion88 | 0 | 0 | 0 | 0 |
| unit424 | 4 | 4 | 516 | 0 |
| pickup56 | 2 | 4 | 8 | 112 |
| special40 | 4 | 4 | 48 | 0 |
| window8 | 2 | 4 | 0 | 16 |
| boundary8 | 69 | 128 | 0 | 472 |

历史`initialize_empty_opening`默认两条zero-slot实验身份保持；旧fixture未覆写，seed0旧独立产物逐项回归相同。新路径是独立命名的`initialize_absent_companion_opening`，或显式`companion_slots`输入，不能混记成旧16case的新结论。

## 交接与剩余消费者

[opening_handoff135.py](../reconstruction/core_spec/opening_handoff135.py)提供：

```python
profile = EmptyCompanionProfile135(())
handoff = initialize_absent_companion_handoff(
    value, world, companion_profile=profile,
    title_utf8=title, subtitle_utf8=subtitle)
# 或 from_opening(opening, world)
```

结果保留opening/world原引用及所有六类物理backing、真实capacity/count、None byte、完整InitialState、creates、packets、start通知、draw统计和pending。`collection.level`就是opening最终phase1/RNG owner；death context使用最终counter、真实pickup capacity及两条现存kind2记录。pickup+4保持`arrival_bits=None`，原physical mask及已知部分字节始终由opening vector持有。实际必读字段未知会明确pending；不将构造phase0改写为1，不经`from_initial`重建或补128个零slot。

594个断言包含六vector非标准capacity、已知stale tail/部分None mask的无损保留，以及未知必读pickup字段拒绝。投影为全量dataclass字段，不调用会硬编码constructor空向量的旧projection。

这里尚未执行headless消费者。companion生命周期、kind2靠近后的真实回调、special2376同状态续接、window schedule、boundary lifetime/transport、world向各placement/movement调用贯穿，均以明确pending obligation交给组合层。其他agent可恢复组件；组合层仍须把结果回写到唯一canonical state。

自然running副本第595帧返回已经clock0.026／7NPC，不能与本time0／4NPC开局强比；它的window3和后继counter88也不能据此修改这里独立seed0输出。本轮未将该副本导入producer，未宣称完整游戏完成。
