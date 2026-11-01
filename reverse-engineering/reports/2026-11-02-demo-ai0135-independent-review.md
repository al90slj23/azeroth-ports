# Demo AI135 独立只读审阅

**声明域通过。** 最终58 fresh cases /66 full921 stages 的[原件收据](../evidence/full0135-oracle-20261101T205618.153296Z/comparison.json) SHA256 `01c93350943b0f20956298fdf1908ae7ee2b66c40d902b7eac817cdf2657b07e` 与实际文件名相符。独审新增原件、模型、checker执行均为0；没有把其它回归或旧批相加。

最终[独审收据](../evidence/demo-ai135-independent-review-20261101T210610.715719Z/review.json) SHA256 `8a1ad29df94cf2d0c53be6075fb4924da723a6fe9bae5f7846ae8b2859616795`。审阅器：[review_demo_ai135.py](../scripts/review_demo_ai135.py)，SHA256 `f7db9f68e1c60107330c8aabbbb64c491787ce7caa1e1ddd9fb5ca8c079edd1e`。独审worker PID/PGID2978 exit0、PID/PGIDmissing，6.467s/60s；5个审阅源码另存快照。早先独审在另批world唯一结构性`distance_map:null`处过严停止，失败收据保留；修正后只允许同null且精确限定1处，58/66物理域仍不允许None。

## 独立核对内容

- 48个生产/取证源码与前后SHA及snapshot全部一致，37 production无运行时文件/原件I/O；145条Python/JS本地import边独立AST复核。`demo_ai135` SHA256 `43391909719bbf953eee678ff49d0a4957bfcc90013ea7af479eeb83b7a6893c`，`ai135` `42ed540a36ec00b93a64c1094117178296e12d46b8a6f06bcf8783449b0ef551`，`ai_world135` `ed30c5165b1af95b8b4002c0ce285c5da8f72709e701a90e25db25d2330cc69e`。闭包不含root headless集成文件。
- 原WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。私有模块只追加section7的完整921与原global0导出，所有其它section逐字节相等，没有替换callee。921签名`(i32,f32)->void`、body SHA `5c2c1cdc75e805e7d4e7ed51f5dddde34eda6331617c9ea8ee2a26da90329a37`；6个静态函数经RO index/有限WAT seek与原body交叉核。
- 使用独立`struct` f32/f64运算重算 **28,408B完整424B记录**、timer、位置/单次movement、主/备弱化选择与物理写集，再同actual和冻结expected逐项比较。共61 contact：primary24、backup10、无弱化27；60次实际incoming HP/f64累加，1次phase guard。四RNG word、HP、护盾等12标量、Game992 f64、序号、全部16 Aura slots、GUID和duration均逐stage绑定原始Game/record观察。
- 132严格`>now`才选primary；否则140严格`>now`才消费backup。到期选择同规则，选中deadline `<=now`清360。128/132/136/140与364从未被“清理”或重排。28次到期中，一例没有Aura，故产生27条新169。U400冻结样本仍先清360，再保持timer/运动不变。
- 完整原921的普通近战incoming队列在late4543前处理；66stage的完整packet active metadata、payload长度/容量/指针、累计前缀和新增顺序均重新绑定。每stage非169先于169，27条169与expected逐字节相等，解码GUID及对应移除slot/field，二单位owner未串绑。1条movement独立核数值/序号；其全部wire与incoming-hit wire仍仅raw观察，未扩大为独立编码验收。

## 类型准入与作者边界

`known_demo_statuses=()`保留旧360非零拒绝。新准入须以唯一现有GUID绑定`DemoDebuff135`，逐项核physical marker、128..140、360/364、16slots和U240；只接受live ordinary、spell1160/已清状态和空ability，拒绝其它/重复Aura与remote owner域。没有清零源字段来绕过旧guard。6项拒绝产物已核SHA与源码门控，独审未重跑这些模型测试。

审阅者是cast组件`demo_shout135._aura`作者，本轮独立核AI的状态消费、清理、owner与排序；对复用encoder只核依赖SHA及actual/expected payload身份，**不声称再次独立恢复自己的Aura算法**。cast180/207已由AI作者另行只读独审；[异作者依赖收据](../evidence/demo-shout135-independent-review-owned-20261101T210700.766545Z/review/review.json) SHA256 `33211f76462dc3708d29df764da5cff006ac64d6fcfbb40e505be768069b0f0e` 已实读核验，绑定同一冻结cast源并独立核119条实际Aura payload。该收据仅作依赖引用，不增加AI58/66计数。

## 运行边界与其它证据层

原件PID/PGID81297 exit0、missing，2.824s/60s；878 imports deny，实际host0，WASM peak20,578,304B/32MiB，heap512MiB，298次栈守卫全部恢复1048576。输入/expected各8MiB、单行2MiB、输出32MiB均核，实际stdout1,210,426B。未加载original snapshot、未App start、未访问save或network。

另批[真实预解析world默认20/45](../evidence/full0135-oracle-20261101T205735.949915Z/ai-world135-comparison.json) SHA `c19b3d1e512923bea71c1d9cc8d2f8ba864b6a4e78cd3ad0d6d206303f6de8e7` 全expected重新严格比较，world三文件SHA及source/host/stack/进程终态均核。它是独立fresh回归，不加进58/66。[flat416/1013](../evidence/ai-world0135-flat-regression-20261101T205733.699998Z/comparison.json) 只保留历史expected模型重比/0新原件身份。独立opening的516未知byte属于其纯模型层，未塞进本批全已知原件记录。

首个58-case heap失败批[205455](../evidence/full0135-oracle-20261101T205455.500232Z/comparison.json) exit-6，仅34行、无runtime，实际host数未知，保留为失败。最终批input/expected/labels/module与其逐SHA相同；只变checker的GC启动参数与runner不再保留整host对象，预算未增加。该批与3-case pilot不计正例。

结论仅限固定0.135.1、真实build90898d5e3（历史alias0898d5e3）、显式手工普通424B记录与受控flat query world。原constructor、资源world所有者、非空NPC能力、其它CC/Aura、remote模式、完整880/native/自然750流程均不在本独审验收中。未改生产源、旧证据、主报告或registry；未stage/commit。
