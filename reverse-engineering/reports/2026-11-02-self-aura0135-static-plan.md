# 0.135.1 self Aura1020 共存静态证据与后续计划

本轮只读定位固定 **0.135.1 / 90898d5e3** 的 kind0资源、正kind8和选卡保护 kind12/spell1020 共存处理；**新增原件执行、模型 case、动态差分均为0**。这份计划不是共存行为已经动态通过。

[trace收据](../evidence/self-aura0135-static-plan-20261101T215808.011168Z/trace.json) SHA256 `1d8451806b94ddf14fb2320406fb04e52160f23f7066b46f1acefd2af3a1618a`。从 SQLite 主键索引定点 seek 1202/2088/4600/1072/1512 五个函数，共读取539,183字节 WAT，另从对应原件 code body seek 核函数SHA；没有全文读取1.3GB WAT。SQLite文件实际mode0644，连接严格 `mode=ro` 和 `pragma query_only=on`；先前错误要求0444的准备失败目录保留，未改权限或数据库。

## 确定的指令规则

- **4600 L663..690**：删除已有spell1020后追加kind12/1020，expiry=now+1，+0..7=0，+8=12，+20=1020，+28=0；**+12与+16两个word未写**。L749..750随后调用1202。1072 L7063..7067先1512再4600。
- **1202 L51..57、L116..187、L199..313**：先按expiry>now过滤，再做正buff聚合；kind12不会被排除，dominance的default有效强度为0。只有kind8/9使用union magnitude作为有效值，因此1020的None word不应被材料化或作为数值消费。唯一保护1020进入正槽0..31。
- **1202 L330..350**：独立负live pass仅处理kind7。L608..713另有owned-definition-kind12生成6788/25771来源，不能与本次live.kind12/1020混为一谈，当前仍明确缺席。
- **2088 L134..171、L755..938**：不按kind做特殊过期；>=触发dirty，<稳定保留，接1512→1202。不能过滤kind12或先后调用旧/新prefix造成两次regen。
- **1512 L614..788、L1525..1533**：G1696/1700的8B passive tag13累加accumulator43，再写G1620。普通0/8/12来源不会自动使1620非零。

## 下一批最小扩域

root已封存baseline `7d26c325c780ce6dd4b32e578d64a164bfee213f`，但原resource_player37源独审尚未终态。在其放行前，保持consumer/aura/mixed/prefix执行源不变；不复制整套self生产组件。之后仅扩现有语义/Aura/prefix的kind12=1020分支，保留同一physical live32、48Aura、HP/RNG与App通知owner；其它kind12来源继续Pending。

新增fresh完整1202/2088对照将重放既有0/8域，并覆盖0资源/8Battle/12保护的遍历顺序、1/10/15秒严格边界、同时过期、NaN连带移除、全部backing/inactive/None、Aura keyed字段、速度226/action与单次regen。旧收据继续绑定旧源快照，不回填历史通过。

为避免3秒分支的空验证，另加显式合法8B passive13受控来源，由完整1512重新计算非零1620，再对elapsed<3、=3、>3、gate387>4与HP clamp组合做2088对照。这个typed输入证明的是consumer路径；App/profile/talent实际grant producer仍未追通，必须单列，不可称自然来源或全流程已闭合。

本任务不改headless、racial、registry或安装包/存档。trace脚本SHA256 `cae499c92c89bf029120487385bd49cc3e3dd0472de0e8fe727b3380fdced42f`。
