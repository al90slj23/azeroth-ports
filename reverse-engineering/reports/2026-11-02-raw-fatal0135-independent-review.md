# 原始451资源到致死终态：异作者只读审查

**限定组合范围通过。** 本次独立读取和重算序列化字段，没有执行作者runner、bridge、生产模型或任何原件。

- 451个实际资源逐文件重新核对size/SHA，共67,281,330 B；453个声明条目中仅Spell.dbc与SpellIcon.dbc未加载。三份独立生成的terrain/navigation/secondary数据重新hash，与受控第四批使用的世界输入哈希一致。
- 当前与snapshot的121个源文件一致，其中117个生产文件；受控第四批113个gameplay生产文件逐字节同源。原始资源链额外4个生产文件列在机器报告。
- 完整读取1,072,504,103 B模型期待流及12,946行独立摘要，24类摘要逐行独立重算，0差异；另外核每行摘要内容hash、f32时钟、frames与selection计数。对应921帧、7选卡、44移动、972个动作。
- 终态36个直接投影字段，以及11个完整owner的22,720单元逐项比较；8,205个None原样保留。终态special/companions恰好activecount==capacity，因此此处能由实际导出的行完整重组；一般逐阶段采用完整backing指纹，不宣称所有Game字段均已导出。
- incoming48的capacity/head/count为128/48/72；空callback/aux owner、research空hero、motion已知/None mask、停机与通知均保持。phase4发生在AI，后续collect/claims/spawn/special/terminal五阶段继续投递；最终HP0、1条defeat通知、10条停机包。

这比较的是共享113个核心源的两次模型执行。第四批原件实验仅作为已有间接依据，本次不读取original-results，不增加原件案例、原件调用或原始资源逐阶段原件差分，也没有重新实现几何或整套游戏规则。

审查自身安装了任务输入open guard，禁止WASM/EXE/memory/WAT、原件results/CAS和历史预解析world文件；未发生禁止读取。作者原始执行没有单独的OS级read-audit收据，其零原件读取声明由冻结源码、provider路径/扩展名限制、输入hash和运行元数据支持。本次不把这些静态证据改写成追溯OS审计。

早先014848执行在921帧后因hero.utf8 bytes不能直接写JSON而退出1，无成功receipt；117个生产源与成功重跑一致，失败目录完整保留。旧460桥哈希未动，run-ledger默认关闭的条件路径已静态核对。实际allocator/header、完整17119返回、caller-scratch数值producer、自然App/device输入、完整一局/胜利/存档/渲染/UI/联机及最新139完整流程仍未完成。

独审证据：`evidence/raw-fatal135-independent-review-20261102T021836.494405Z/review.json`，SHA `67b6baaebffeb8254fdf3928f3f9c1be3920e2b59ff342e23eb08298f1d52b9c`。

独审脚本 SHA `eb1dda33e61fbdecc25526fefa23699ea0828957c09e1922544878d91cdf30a0`；owned收据 SHA `2a96804796eebbf4c9c38317a7c6923055f7729a7a1ed8e256cecea5b67224f7`。

机器报告 SHA `357a7984fc70ea3484c9883dace046d60ad8d949620bb76910e69f2a5539ec75`。
