# 官方0.134.0候选生成与随机链

冻结原件 **0.134.0 / 983346a7**，SHA256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52`。SQLite以`mode=ro`连接，只按完整func range seek WAT；全部14个函数WAT/body、SHA、连续guards和绝对行号在`evidence/candidates0134-chain-20261101T022925.761395Z`。没有执行WASM/EXE/APK、联网、存档读写或应用写入。运行差分case数为0，本报告不能称为原件运行验收。

## kind0候选池

2159按kind低8位派发；1/2调用1708(G,0/0.25)，其余default走普通能力池。本独立模型只接受kind0，其他明确pending。owned80B向量来自G+1656/1660。owned数量>=6完全跳过新技能；数量<6按职业kit原顺序访问，排除已有ID、blocked借用ID向量2080/2084、banished字符串向量2092/2096。新技能weight为owned<3时f32(1.6)，否则f32(0.9)。职业byte360的2/3/4/5/7/8/9/11分别为paladin/hunter/rogue/priest/shaman/mage/warlock/druid；其他byte回退warrior。该映射来自实际1595872指针表，不是职业列表顺序猜测。

`demonic_empowerment`还有先于blocked列表的过滤：从effects2020/2024的8B项按顺序累加kind-byte32的f32值。sum>0时，summon2044/2048的36B项tag42要求pointer4指向对象的u8+41>4；sum不>0则要求>0。tag46/47总合格；tag45仅sum不>0合格。没有合格项就排除此新技能。独立模型使用显式Effect/Summon快照，默认空列表表示明确空的相关向量。

已有技能按owned原顺序，先用tier4收集可升级kind（29736→27375→25368），空列表不入池。再以`rank:{ability_id}`排除banished字符串，合格项weight f32(1.3)。这不是每kind一个独立pool项；每个owned能力最多一个项。blocked借用ID只过滤新技能，不直接过滤已有升级。

## 抽样与tier

flag275为0固定请求3卡；flag275非零时，flag2573的bit0为1请求3卡、为0请求4卡。此处两个select的栈顺序已用首轮pilot失败保留证据修正。每轮从剩余20B pool项按顺序累加f32权重，用32652抽[0,sum)，依次减权重取首个命中；命中项以memory.copy移除并保留其他项顺序。最多抽请求数或pool长度，因此同次普通池不会重复同一项。先抽完所有pool项，再按被抽出的顺序分别生成tier；不能交错pool抽样与tier随机。

令`x=f32(f32(G.f32[1404]+1)+min(f32(f32_u32(G.u32[1520])*.01),.3))`。tier权重是`[60,25*x,10*x²,4*x³,x⁴]`，全部按原指令次序f32舍入；x²先算、x⁴由x²*x²、4*x³由(x*x²)*4。tier单次range随机先减60，再减后续weight；越界舍入尾值回退tier0。新技能保留此tier。已有技能若此tier没有可升级kind，则按tier递增探测，最高4；pool先前已证明tier4至少有一项。

29736保留定义upgrade-byte列表顺序且不耗随机。1480对完整合格kind列表做Fisher–Yates洗牌，长度n..2；每次raw RNG乘n，`low32<=u32((n<<clz32(n))-1)`才接受，拒绝也推进RNG，index为乘积high32。tier0..3保留洗牌后1项，tier4保留最多2项。每张升级卡的洗牌在下一张tier roll之前完成。

32652 RNG位于G+1712的4×u32，是xoshiro128++：output=rotl(s0+s3,7)+s0，然后四word按完整body更新；高23位构造[1,2)的f32再减1，ordered f32缩放到range。四word全零是退化固定点，本模型不擅自补seed；seed初始化仍unknown。

## 过滤、fallback与刷新边界

非execution9/11的27375结构过滤：kind0要求definition.damage48>0；kind1允许；kind2要求definition.count64非零并满足execution bitset/radius条件且tier非0；kind3要求execution∈{2,3,4,8}或execution10且radius60>0；kind4要求execution∈{3,6,10}。每个kind都需25368>=f32(.005)。execution9/11的27375分支也已完整恢复：e9有effect-tag结构过滤及kind1/4的duration/有效cooldown饱和度；e11有redemption的76字段概率阈值、faerie_fire禁止cooldown以及六ID冷却floor。模型按原指令f32次序计算，derived cooldown显式取G1368。divine_shield的duration截到6、冷却floor=10-duration，hellfire floor=.5，其他默认.25。49338的bloodrage/seal_fate/soul_fire/lightwell/polymorph/hunters_mark下限分别8/2/3/6/3/2，其余0。新版25368与旧完整helper268行逐条比较，只允许16行header、五表和panic重定位；其余完全相同。五张新版表原始u32与独立upgrade_values.py逐项一致，diff也保存为证据。

空pool无随机draw，构造gold25的输入tag0x80000004、tier0作为唯一fallback候选。普通新/已有/gold三种候选不会进入G+1944的特殊历史记录追加dispatch，因此该历史不影响已规格域。再次调用2159从当前RNG重抽；2392只在末尾加1，不能把这个counter或历史向量误当作去重seed。实际reroll操作如何修改banish/flags/queues仍未在此独立实现。

候选80B中+60分派，+64/+68在新技能为ID ptr/len、已有为kind Vec ptr/len，+72为已有owned index，+76为tier。1480会另外生成+0..59显示payload；独立模型返回selection所需metadata并显式`ui_payload_pending=True`，不宣称已生成完整UI80B。2159替换1896/1900/1904后写kind2577、counter2392；第三参非零才置phase2579=2，mode2574=0时还执行35513世界副作用，随后1203/6310通知。这些副作用明确pending。

## Controlled2159入口

研究fixture先用kind0、第三参1、mode2574=1跳过世界副作用，2558=0使6310早退。设置class360=1为warrior、G1712四个非零u32，level1520=1、luck1404=0；owned1660=0，effects2024/summons2048/blocked2084/banished2096/history1952/candidate1904/notification1892均0，各空Vec的capacity0、ptr为合适对齐dangling指针。flag2573=1、flag275=0期望3卡；flag2573=0且flag275=1才请求4卡。生成顺序、候选ID/tier、RNG四word可与独立`generate_kind0_metadata`差分；展示文本、分配器地址不属于该函数返回的已实现域。

重现：`python3 reverse-engineering/scripts/trace_candidates134.py`。只新增trace、报告与core_spec/candidates134.py；没有改model/builder/host/docs，没有commit/push。
