# 真实开局、守卫出生及后续待机的连续组合

本批固定 **0.135.1 / `90898d5e3`**（旧八位alias `0898d5e3`），WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。独立默认Elwynn、human warrior、seed0、对象42、navigation false、静止玩家，保持“优先升级已有技能，否则第0张”的原选择策略。

**250帧、3次选择、3503阶段、3505完整原件入口，声明比较范围0差异。** 真实1089开局继续刷怪、顺劈斩/雷霆一击、死亡/拾取/升级；20秒时四个special产生守卫，再继续50帧。最终等级4，未将真实守卫当普通怪、清掉timer或跳过特殊对象。此结果不与旧120帧批相加。

[完整比较收据](../evidence/opening-combat0135-oracle-20261101T163251.935471Z/comparison.json) SHA `53fbae6e607171f2038dc675f658c343e4e26d336355a0a569a13458e660b675`；94源前后不变，含84生产文件。输入与独立预期在原件执行前冻结；原件只接收开局输入/动作，不读独立预期。

[最终独立复核通过](2026-11-02-opening-combat0135-250frame-independent-review.md)，收据SHA `556693d5bac9b86545dd89a57b042bdb54823e49d4f845b5547a3a978d7158c7`：14,167,242比较leaf、完整gzip/CRC/双SHA/顺序、严格未知mask及guardian GUID/timer绑定均核；5个篡改负例拒绝。静态声明另外按原WASM初始零页加全部active segments顺序重建并证明跨段零区间，不能将稀疏静态零洞和独立allocator未知字节混为一类。原件与生产模型均未由审阅器重跑。

## 本轮整合

- `headless135`接入已验证的`special2376_spawn135`。真实单位backing、special标记、RNG、counter与3timer独立owner持续保留；每次普通尸体压缩后按GUID重定位guardian owner。
- `guardian_ai135`处理当前实际到达的存活idle/返窝/移动中/锁定分支。U352共通近战timer按顺序处理，技能timer在未接战时保持；U68实际allocator pointer仍是模型的显式未知，不填零。交战、死亡、资源释放和910动作仍明确停止。
- 普通AI和guardian切片共享同一world、距离场和玩家状态。仅已验证的存活guardian免于普通尸体family守卫；其他未恢复family及死亡guardian不准入。
- guardian U68的四个未知字节不能掩盖timer内容：原件捕获真实唯一/非零/对齐timer allocation、完整capacity backing、当前3个timer、技能44B与header28B；投影按GUID及unit index逐项对照。

[上下文来源](2026-11-02-opening-context0135.md)另外确认G1092为guardian击杀计数，1560显式初始化0；本域没有guardian死亡，逐阶段仍为0。G404构造未写，保留None；仅endless胜利分支需要其实际producer值。G2540在当前mode0未被消费，保留未知，不拿其他字段代替。特殊生成组件相应只在真正消费时要求这些值，57组原2376回归0差异。

## 取证与比较范围

本批把独立预期和原件完整capture均改为流式gzip JSONL。单记录上限2MiB、原始流上限1GiB、压缩原件上限256MiB、1case、最多600动作/500帧；Node heap512MiB、WASM256MiB、owned PGID期限60秒。原始capture **785896500B**、压缩**99283327B**，最大记录477556B；raw与gzip双SHA及完整解压均校验。没有删去packet、rawG/App、物理backing或owner观察来压小日志。

声明比较沿用前批的状态/23派生字段/7个numeric keyed字段、能力/候选、普通单位与七个vector已知字节、HP/RNG/计数/序号/距离图；新增G1092/mode2582及guardian完整语义owner。未恢复的活跃队列在本域要求为空，不能只比较其count。

原件消息payload与其allocator/raw metadata完整保存，但整段runtime wire stream仍未独立预测，因此不宣称逐包验收。特殊生成组件169/548包有自己的隔离差分，不自动扩大为整段消息链已恢复。

原件继续使用声明的历史线性内存snapshot，包含已初始化world/locale/allocator；未恢复JS externref虚拟机。独立模型使用先前451资源producer产生的预解析world，本次组合差分没有重跑资产解析。时间仍由外部显式f32 scheduler更新G2352，然后调用14尾入口；不是完整880或Windows原生运行。

PID/PGID70978退出0且不存在；原件WASM峰值166395904B、878导入全拒绝、实际宿主调用0，公开入口栈全部恢复1048576。

## 单独保留的验证

- [Guardian组件](2026-11-02-guardian-ai0135-idle.md)：40case、115完整921调用、259单位更新，0差异；非空3timer owner及真实world，未覆盖交战/910。
- 原special首次到期组件57组以当前未读字段None契约重新回归，0差异。
- 旧显式phase1/zero128平地切片仍为8seed/1614帧/22607阶段/11选择、0差异；混合死亡拾取204case也0差异。它们是独立回归域，不加到新250帧数。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reverse-engineering/scripts/check_opening_combat135.py --phase full --frames 250
```

本机固定原件、snapshot、预解析独立world及Node是此原件差分命令的显式依赖；纯原始资源独立入口为`run_asset_combat135.py`，其模型自检单独留档。

原始资源入口[250帧模型自检收据](../evidence/asset-combat250-owned-20261101T163850.979737Z/model250/receipt.json) SHA `d6c46c50baaf2adf5afb2b15ae0fee5fd29ff5e13b45208361b3f57f0c3edff8`：451资源/67281330B、91源前后不变，未读原memory、WASM或预解析world；实际从资源生成world后运行250帧/3选择，level4/XP3。三份world查询产物与既有独立world一致；终态共同字段、五份backing、guardian owner及84共同生产源通过[衔接核对](../evidence/asset-combat250-owned-20261101T163850.979737Z/projection-bridge.json)。整个owned进程224.10秒、300秒预算、PID/PGID81217退出0且missing。

同一world/state由单独只读host observer保留引用后，再纯模型延伸129帧；资源请求数不变，没有重新解析地图。第379帧按原策略选中第四卡battle_shout，第380帧明确`pending_selected_ability`。[续跑收据](../evidence/asset-combat250-owned-20261101T163850.979737Z/continuation/receipt.json) SHA `0542e348868665e22884b60e194cf0f2508f9683c46a218e6bc23e67f8ad616b`。该续跑、资源模型自检和衔接核对都不是新增原件case，不把250帧验收扩大到379帧。

下一步恢复guardian交战/返窝重置/阈值/计时与910→915，并接普通Boss/终态/保存。0.137.0最新432B布局与伤害迁移单独验收。本批完整880、Windows原生执行与独立完整局数仍均为0；最终目标未完成。
