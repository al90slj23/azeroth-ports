# 独立 world cache 的静态只读复核

对 [world_cache135.py](../reconstruction/resource_spec/world_cache135.py) 的独立只读复核通过，绑定生产SHA `34bdcd7116dcf25ec300d5ac028ca97122dba8b2be64e91324e03a37cf89a762`。本次核对已声明的有效 canonical、nonflat／无primary路径；**新增原件执行0，不是完整world差分，也没有把root仍在运行的全资产历史比较标为通过**。

[最终复核收据](../evidence/world-cache0135-independent-review-20261101T111914.481057Z/review.json) SHA `a686b8a03b25b7954432c4765e2c14b26f472ad837123f1cfeb90f78d450fbb8`；[机器报告](2026-11-01-world-cache0135-independent-review.json)登记完整查询、字节窗口、源码闭包和范围。

## 实际重新读取的证据

[review_world_cache135.py](../scripts/review_world_cache135.py)从原固定90,959,080B WASM、只读SQLite和WAT重新取证：先核对WASM、642,973,696B索引与完整WAT的SHA，再按SQLite的精确byte范围seek七个函数 `6730 / 15374 / 9328 / 12375 / 18572 / 18670 / 84193`。每条查询参数、WAT位置／SHA与原WASM body位置／SHA都保存，未扫描整份WAT为文本或执行原件。

保存原6730的11个规则窗口：zone半径／primary选择、nav宽度、原点、无primary时ground、中心种子、边界迭代器、四邻BFS、最终raw byte OR、secondary宽度／几何、terrain筛选／最大值，以及没有更新时的absent结果。每段保存真实指令、行范围、SHA和实际命中的常量／调用tokens，供逐项复查。

zone0另由reviewer独立解析WASM data section重建152B初始静态数据，保留每个活跃segment的地址、原文件范围和SHA，以及原模块初始化的零隙。record SHA `aa7ace8cbc885786ee0752885198aa690e9482b91c77cdec6ebf0dee90828da7`；真实字段为中心(-9396,-633)、fallback68、heading1.6、radius120。byte148为0，所以6730即使读到polygon长度4，也选择primary长度0；没有用运行后内存快照推导这个入口域。

15份reviewer／生产传递依赖源码前后SHA一致并保存。生产函数未执行，原件内存快照未读取。

## 核对结论

| 模块行为 | 原件依据与复核范围 |
| --- | --- |
| grid | `radius+20`、逐步f32直径、ceil后的280／560宽度及center−extent原点一致。 |
| ground | 原无primary分支逐行调用18670，在一米cell中心采样；miss写canonical NaN。 |
| connectivity | 原15374枚举free边界，加free中心；四邻只经过raw byte为0的格子，最后执行原byte OR `(visited XOR 1)`，保留非boolean字节含义。 |
| secondary | 半米cell中心读取terrain，严格下界`terrain+0.1 < z`、包含上界`z <= terrain+3`，过滤后才检查候选索引；NaN／较小值才替换，全部拒绝时返回absent。 |
| placement衔接 | 明确按nav M2、nav WMO、secondary WMO三个有序pass执行，使用独立placement API的XYZ／Euler／scale／chain。 |

WMO分组预算使用reviewer自己的原始chunk／MOPY／u16索引解析重算，没有调用生产WMO parser。实际410文件中23root、387group全部重新读SHA；按原`flags & 4`过滤后共459,261顶点／1,051,449索引。最大group为Stormwind112的15,452顶点／30,603索引，387组全部满足冻结CollisionMesh的65,536／196,608预算，无需修改旧预算。

逐group处理与原root拼合的静态等价依据：原4464在每个group内独立去重并按原序append；18572对每个顶点使用相同固定pose矩阵、没有跨顶点浮点归约；9328的AABB／normal／400-step采样只依赖单个三角与同一ground，副作用仅为nav格写1；12375逐三角产生有序候选，最终6730合并规则保持。原group顺序和三角顺序保留，分组不会改变这些数值运算的次序。七个函数的完整证据另存，供检查这项推理。

这仍是与真实原指令逐项核对后的静态理由，不能替代完整world数组的实际对照。其它地图／模式、primary-present／flat／polygon路径、原VFS和Rc所有权、菜单／存档／UI／联机和完整一局均未由此验收。root的全资产历史world比较继续单列pending，完成后应以另一份不可变收据和只读wrapper登记结果。

复现：`python3 reverse-engineering/scripts/review_world_cache135.py`。不会启动浏览器、原游戏、EXE或修改生产代码、安装包及用户存档。
