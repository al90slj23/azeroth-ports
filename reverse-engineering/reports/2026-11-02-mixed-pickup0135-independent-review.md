# Mixed pickup135 独立只读审阅

**声明域通过。** 最终[原件收据](../evidence/mixed-pickup0135-oracle-20261101T210401.228175Z/comparison.json) SHA256 `19e28a54b2dc6a306dca5fd6d3bd17f16e24524f858ccb1e9265829128e48e3e` 对应60 fresh cases、61次完整2862，0差异。独审新增原件/生产模型/checker/builder执行均为0，不与旧pilot、resource独立组件或750轨迹相加。

最终[独审收据](../evidence/mixed-pickup135-independent-review-20261101T215029.875027Z/review.json) SHA256 `5387f7daec547d6a65208f87640554d4942b2d629ea44b458f323fb5fa453089`。新增[审阅器](../scripts/review_mixed_pickup135.py) SHA256 `6648ee0cd581e52fc5998b50b1892e79ccb75e40c01ce986b5af20c94792cd3f`；独审worker PID/PGID76518 exit0、双missing，1.398s/60s。8份审阅源码另存快照。早先07d355...只读通过收据保留；最终新增有限候选/RNG独立重建与三个notification writer窗口，未增加原件调用。

## 源、原函数与过程

52源码/44production/189条本地Python/JS依赖边，前后SHA、当前文件与source-snapshot全部相等。生产AST未发现原件/资产/文件/进程I/O。完整2862及18个静态函数的body、有限WAT和RO索引交叉核；私有模块仅新增section7的10298、2862和原global0导出，其余section逐字节相等，没有替换callee或执行App/EXE。

原件固定0.135.1/build90898d5e3，0898d5e3保留为历史alias；WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。原件PID/PGID94374 exit0、双missing，2.959s/60s；878 imports deny、实际host0，peak20,578,304B/32MiB、heap512MiB。243次含malloc的栈守卫恢复1048576。validator94165 exit0/missing，7.047s。input/expected各4MiB、单行2MiB、stdout16MiB有界；实际stdout2,442,473B。

原comparison封存input/expected/module；本独审另外给stdout/runtime/terminal/prepared等原产物计算当前SHA。后者是审阅时绑定，未倒填或改写旧收据。

## 独立语义复算

先用入口radius、XY/time扫描attraction，再固定eligible indices，严格逆序despawn→即时消费。仅1条attraction写marker/+4；arrival是f32距离/24或/32后下限0.12。本次选择列表不受后续level-up/radius或phase2反向影响。选中的189条为XP63、coin56、kind3×16、kind4×30、kind5×24；全部56B稳定memmove以及inactive尾行保留。

独立重建当前level/23derived、HP、shared live/aura、金币/earned、XP/coin原amount forwarding queues、counter/action/sequence及每条事件。当资源4先于XP时，增长基于带buff的old/new差；资源5按当时maxHP与387门限治疗；XP逐级1512→20%或半量heal，再检查下一threshold。共70个逐级growth与1个DOT提示。累计物理比较pickup backing17,752B、live backing5,888B、aura backing35,328B。

36,342 known值与31,264 unknown byte cells的写掩码同独立重建逐项一致。继承的pickup None额外按输入非零A5/5A材料化观察逐字节追踪，marker/+4与memmove后仍严格保留；未把None补0。新live未写+12/+16和未用capacity、inactive aura的未写字段继续按真实producer掩码保留None。

31次choices里93个实际候选全部为new。独立复算本批有限warrior kit、0或1条默认cleave/rend owner的weighted pool、三次无放回挑选及五档tier采样，186个RNG步骤和所有metadata精确匹配。没有导入生产candidate函数或用actual填expected。upgrade-kind/shuffle/gold及任意owned域不由这次有限复算验收。

30次mode0 `choice_pause`均位于对应XP后；31次`choice_notification_pending`保留消费当时的level、gold、offer、kind/tier及完整candidate metadata，随后继续当前已经固定的选择列表。没有活动NPC/aux motion的受控fixture使原35514动作循环为空；它不证明未来移动actor暂停已接通。

## Wire、通知和App owner

416条实际已声明wire分别为170×189（1,512B）、306×70（1,540B）、226×16（160B）、150×141（12,927B），逐字节及先后次序重建。150中70条Rune/type6、71条逐级growth+DOT/type10分开记录，不拿累计观察数冒新消息。其它包，包括XP221，完整raw保留但编码仅观察。

Rune70条英文JSON全字节预测；choices31条只比较`type/offer/why/level/gold/kind/tier`已知envelope与完整metadata。原choices title/description/icon等呈现JSON全量raw保留，未喂expected，也未冒称全部UI验证。队列active完整payload与Game计数/容量和原始顺序交叉核；allocator/BTree形状与未知队列地址仅观察。

WASM静态image（初始零加全部active段顺序覆盖）证明14340336冷初值1。RO精确常数访问仅23581、42920、44447；独立保存每条oldID→u32++的writer窗口，44447另可委托42920。这是共享App级owner。Node只assert入口输入1，未写该绝对地址或Once，并跨同一fresh实例的多次operation保留。App先前聊天、装备、Boss等通知历史未知时必须pending，不能每帧/每Game任意reset1。

## 接线前的必要边界

当前headless只有active32与unknown word marks，没有完整live capacity/backing、player48aura与App nextID owner。旧prefix支持7/8/9/12，新resource prefix与现resource bridge只支持0/8；select又会追加12=1020，而AI旧guard拒绝kind0。直接塞入context会撞到真实共存缺口。

最小正确路径是建立单一physical live/aura owner，让所有cast、select、expiry和incoming消耗保持同一backing；level仍唯一持有HP/derived/time/RNG。prefix和collect入口才构造临时context，验证active语义视图，返回后原子回写live/aura/action/App owner并丢弃临时context。只运行一次联合2088 prefix，不能old/new各跑一次regen，不能过滤1020绕guard。World正在另做0/8/12=1020的fresh域，尚不转记为本批通过。

collect须按ordered_effects原位应用actor pause和wire；mixed XP效果已携growth150，不能再调用末尾aggregate `_growth_banners`重复发送；despawn170同样只能发送一次。保留同一reverse选中列表，不在phase2时中断当前调用。自然ContextNone静止750捕获，无论源码包含mixed与否，都不证明资源近身混合消费执行。

本审未改生产源、主报告、registry、原证据或750依赖，未stage/commit。near kind2、其它外部stat/aura/claim/aux producer、非英文、完整choices呈现、完整880/native仍明确pending。
