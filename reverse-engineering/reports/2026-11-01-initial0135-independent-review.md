# 0.135.1 空profile构造器独立只读复核

最终 [055136 strict151 receipt](../evidence/full0135-oracle-20261101T055136.418672Z/initial135-comparison.json) 在声明域内通过。冻结生产模型从151个显式输入重放，预期和原件投影全部吻合；两个真实80B记录共24,160字节严格比较，没有mask或NaN放宽。40个object ID超过JavaScript安全整数范围，仍以u64字符串/原始字节完整保留。

独立解码原件raw2592，执行5,436组readback核对：包括候选count、racial80、23stats、HP/pools、RNG、GUID、phase0、sourcecounts、budget/timer、game_tag/member与byte flags。151份原始2592数据共391,392字节保留，但未投影物理指针不能据此声称全部重建。19源快照及执行包闭包、artifact哈希、原件非export字节与1560角色/body SHA均通过；当前19源均与最新39-role快照一致；此前053304收据和独审证据按其旧范围完整保留。新增G740/G744为0，G1652为f32(-10)，已在全部151份真实raw2592独立核对，修正组合时把lastHit默认为0的错误。

本次静态审查发现seed fallback判断漏掉一个 `|ab`：原WAT在最后&255前还合入ab低字节。作者确认并修正，同新增构造器scalar一起重跑最终151。抽象四word反例可说明遗漏，但本审查没有找到触发它的具体64位seed，也不把既有151的0diff当成稀有分支证明。候选列表原为literal[]，现runner先断言实际G1912为0，独立raw检查也确认151组均为0。

9职业starter、8种族racial、12区域及114条能力查找数据均与原data段核对。G1660首记录是class learned starter，G1256是非零effect的真实racial80，不能用任意支持的fireball替代。构造器返回phase0；输入为显式空376B selected-profile，未声称所有职业/种族组合都可在原UI选择。

上游account/character48/profile producer、初始App熵、完整world/asset注册及phase0->1进入链、非空装备/天赋/外观，以及完整racial执行仍属其他边界。审查未运行原件或修改作者源。完整证据与复算脚本见 [review.json](../evidence/initial0135-independent-review-20261101T060233.402311Z/review.json)。
