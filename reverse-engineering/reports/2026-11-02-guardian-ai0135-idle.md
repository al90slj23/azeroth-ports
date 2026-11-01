# 固定0.135.1：guardian idle与返窝消费者

新增独立生产模块[guardian_ai135.py](../reconstruction/core_spec/guardian_ai135.py)。40组受控输入、115次完整原921调用、259次守卫更新，在声明比较投影内**零差异**。核心源码SHA256：`fbf9fb16f6d58292986b1c84268b3c70bb36f4b31b59fc0c9a13fbf0c8199a16`。[机器报告](2026-11-02-guardian-ai0135-idle.json)保留API、源码闭包、输入与收据SHA；[前置静态链](2026-11-02-guardian-ai0135-static.md)中的交战/技能部分仍未验收，不能用本批idle结果代表完整guardian AI。

固定0.135.1/build90898d5e3，原WASM SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。只追加函数/只读stack导出，完整921和全部内部callee保持原样；没有替换guard、没有启动App或读取运行snapshot。

## 已完成的实际分支

- 四名守卫由独立`tick_special_spawn135`的20秒首次到期生产器生成，带真实Elwynn609/610/611声明和三项CD owner；当前连续stationary输入是原件前生成，不取原件输出做模型输入。
- 先保留U400锁定早退；未锁定时按原顺序执行共通U352=f32(U352-dt)。U92从special40取home，越界按原规则使用当前插值位置。
- 对U108=0、满血、非近战接触、没有进入玩家近窝激活条件的实际idle域，三项技能timer保持不变。已有返窝运动未结束时保留；距home<=2直接idle；其余按80447速度与原直接返窝路线设置316/328、340/344并返回移动输出。
- U68始终为None。owner以GUID绑定，unit_index可以重定位；header28、三条能力44、capacity和三项timer原样保留。原件侧单独用真实allocator建立有效3-f32 owner，只规范化其物理地址，未伪造0指针。
- `guardian_cleanup_admitted135()`允许调用者保留上述精确存活域；它不执行清理、不释放timer，dead guardian返回False。

完成状态累计：idle214、idle_return12、idle_inflight30、locked3。覆盖home距离2/2.01/3/4、连续40帧、三类CD owner、负/零近战timer、未来/相等U400、已有移动、home越界fallback及不同未知字节poison。另有6项pure-model拒绝检查，独立于40组原件差分。

## API与接入义务

`GuardianContext135`接收now/dt、playerXYZ、special40完整backing/count、独立world、mode/local_peer/phase和明确的其他源缺失声明。`step_guardian_unit135(record,owner,context,unit_index=...)`返回record、cooldowns、status、movements和movement_geometry；本批attacks/planned_actions为空。

root调用者继续拥有全局distance-map刷新、所有单位的原顺序、攻击/动作队列和transport。本模块没有改headless、ordinary AI、corpse消费者或组合checker。将guardian错误地归入ordinary追玩家、抹除U64/68/72或删除family guard均不属于本实现。

## 验证与边界

65项生产/检查源码在独立预期生成前记录SHA，执行前复制完整闭包，执行后全部一致；fixture/expected/module/world输入亦保持一致。40个fresh instance，每个32MiB上限，峰值20,774,912B；878个host imports全拒绝，实际host调用0；stack全部回到1048576。原件PGID66582，60秒期限，实际1.207秒，退出0且PID/PGID均缺失。

严格比较90,878个已知叶与三项timer；23,828个未知cell明确不预测数值，其中除allocator地址外的原始unknown字节还断言逐帧不变。比较包括完整已知424B、实际header/能力静态字节、special/inactive backing不变、RNG、HP、incoming累计、序号/包数、distance-map与时钟、movement221几何/时长/ms/序号。未覆盖完整wire编码或全部Game字段；“完整921调用”表示原函数实际完整返回，不表示全部Game状态已恢复。

最终证据目录：`evidence/full0135-oracle-20261101T163019.002977Z/`。主收据`guardian-ai135-comparison.json` SHA256：`4a48e8bd184a2bc44ef19493e29b51db639de8c7319371ff4efffb211133177d`。初轮`162938.958222Z`保留：原件正常返回，但比较器将Python tuple与JSON list误记为6项坐标类型差异；只修检查器序列化，随后全量通过，没有据此修改模型数值规则。

受伤/近窝玩家激活、已engaged/leash、HP阈值、timer规划和任何910动作明确抛`PendingGuardianAi135`；没有输出动作后假装消费完成。guardian死亡/资源释放、完整1073、880和完整游戏仍未完成。本批是原件差分115次，不与既有120帧组合成果合并为新的完整游戏帧数。
