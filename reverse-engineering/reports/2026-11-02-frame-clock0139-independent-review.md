# current139 owner clock：100B原始片段异作者独审

通过限定为片段级的只读独审。484组／500步是把884原始连续100B前缀放入微模块后的结果，不是完整884、原函数入口或Game2352分支执行；139 full原件target累计增加0。原件程序、作者模型／checker／builder均未由独审执行；独参PID2063，exit0，PID／PGID均已不存在，作者7件与13源不变。

从当前原WASM自行解析884完整139350B函数体和10B原locals，逐个解码前缀35条opcode与参数，核对每一个byte。微模块完整检查为原10B locals＋原100B连续prefix＋仅4B local.get156/end尾；只存在type/function/memory/global/export/code六个section、0 imports、1个函数、2MB固定内存，没有884其余body、调用、data／table／start或额外写入代码。原local156初始f32为+0，SP原样每次减10704，未加恢复指令。

独参自行再生全部484输入，不解析作者expected作为参考值。使用精确分数重算binary64减法及最近偶数舍入，再按原select顺序处理与0／f64(.1)的比较，最后独立舍入为binary32；没有调用作者clock API或照用宿主min/max。tag必须完整64位等于1才消费旧timestamp，120步首次不消费；无论首次与否都写tag1和当前timestamp。2次负零dt严格保留。815个非NaN IEEE值位级一致；109个dt NaN和76个timestamp NaN只核类别，payload／符号／quieting没有保证。有限上限先取f64(.1)，再demote为0x3dcccccd，不能把先用f32常量作比较当成同一规则。

全矩阵包括19×19的f64交叉、true64标签、负零、次正规数、最小正数、0.1相邻f64、最大有限数、Infinity、quiet/signaling NaN和连续timestamp恢复／抵消。500步的64000B canary逐字节匹配；8000B owner写范围与每步SP前后严格核对，其中NaN timestamp仍只按类别验收。runtime全部500次2MB域外SHA比较为true；独参审计了两段hash覆盖范围，并再生256种canary周期的期望hash。原件收据保存的是比较布尔值，没有原始hash pair／域外内存回读，因此不能把它说成独参另读回2MB原始内容。微模块静态证明仅两个store写owner16，进一步限定了可写范围。

Python API的u64类型／范围与tag1缺失旧timestamp守卫、JS的16位lowerhex／BigInt转换／输入大小与步数界限均作静态核查，正式输入也独立验证全为合法字符串。JS正则有ToString coercion，不能宣称它拒绝任意非字符串坏输入；这不改变已冻结正式484组的输入身份。NaN只分类的边界同样适用于跨JS→WASM参数转换。

2352加法单独分层：current884第34975行前guard读布局字段2588，第47950行前读2587；两处皆有f32(dt+G2352)，不能合并成同一Game2587路径。两分支本批原件运行均为0。25个额外Game clock arithmetic输出由独参另算一致，只是模型自检，不替代分支、owner可达性或完整主循环差分。上游timestamp单位／浏览器来源尚未验证；已有0.125／0.5／1等组件dt只是受控系统输入，不能据此宣称884实际采样会产生这些dt。

原件微模块PID75986，约0.920秒，exit0／组清；单实例、0 imports／host、2MB实际内存、CLI 4MB WASM上限。所有500条返回与连续SP下降一致，外部harness仅每组开始重置SP。先前6组／11步pilot保留排除；源13件／18边、全部静态body和微模块identity、预期先冻结与Python禁读原件audit均核对。第三份spec文档明确是捕获后的规格，不是新实验。

本验收不包含完整884／App启动／externref／rendering／Game2352真实分支／游戏行为／联机／存档／Windows原生或完整一局。研究结果与封装优化分开，目标未宣称完成。

详见[机器报告](2026-11-02-frame-clock0139-independent-review.json)。
