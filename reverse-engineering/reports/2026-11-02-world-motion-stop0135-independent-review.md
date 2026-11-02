# fixed135 非平坦world停止：56例异作者只读独审

本批在声明输入域内通过。原作者 `stats138_review` 的56个完整17119调用，冻结期待与实际原件输出全部由独立读取器重算。新增原件调用0，production导入/执行0，没有运行作者checker、builder或原件，没有更改冻结源、primary、registry或shared headless；完整游戏目标仍未完成。

原批：`evidence/world-motion-stop135-oracle-20261102T000919.144127Z/comparison.json`，SHA256 `8a49cd52bcaaf2b8fbd803ab0476f1dce459e7c837a57ac6b4c16bb83a983e99`。独审：`evidence/world-motion-stop135-independent-review-owned-20261102T001613.577948Z/review/review.json`，SHA256 `344b098c6b1513831a96ca28aa6c2982a5c5cc0567b73441b1a0e177be89e65d`。读取器为 `scripts/review_world_motion_stop135.py`；其源码及所用早期独立world读取器由同名JSON逐项绑定。

## 核验结果

- 固定135原件SHA `c62c85f5…`重新校验，私有模块仅改export section7，原始代码与其余section逐字相同。重新解析8个相关函数的签名、body及WAT，涵盖17119/17217/16340、29631、23181、45845、18670、46295；作者manifest的6个body guard全部匹配。
- 逐项恢复NPC marker/duration/截止时间、aux duration/截止时间、claim `not now>=start+duration` 的短路读取和三域稳定顺序。binary32先算ratio并clamp再逐坐标插值；claim非正duration只读取destination。原件29631(worldRc+8,XY)成功时替换Z；失败且primary存在才可能走23181，成功也只替换Z。本批primary不存在，因此miss保留插值Z，未使用world fallback字段替代。
- 完整比较145,152个Game fixture字节和82,544个三域backing字节，包含未激活记录和未使用capacity。仅2412、1880/1884/1888允许变化；54个新packet-vector指针字明确属于实际分配地址观察。Game2348保持真实Rc26204808，phase、action、pause等字段均不改变。
- 165个新增221包的完整有效载荷共3,243字节及各capacity均匹配：NPC54、aux55、claim56。覆盖GUID零/高位/重复、先递增再编码的共享sequence环绕、稳定顺序和向量扩容。旧prefix的3条记录共48字节metadata逐字保持，旧payload/capacity同样保持；完整prefix并未简化为opcode列表。
- 150个world命中与15个miss的Z值独立从真实snapshot输入重算，并与原件backing和完整包逐字匹配；有1个claim只读destination、3个负ratio clamp。`world29631/interpolated` 是独立参考路径诊断，原件未对height来源插桩。审查器共169次参考查询，其中4次来自稀疏投影；47个不同XY、8次secondary抬高均为参考诊断，不增加原件调用。
- 从snapshot原始Rc/header、9张terrain tile、2,304个chunk及secondary560网格独立重建2,318个查询输入范围，共5,950,608字节；包括地址与长度的digest为 `eecd1162f7c3bb61abf16cfa556c910cd4a12036f3f638c5d97f2be880c1dd4f`，与冻结输入及每例原件前后digest均一致。这仅证明声明查询范围稳定，不等于整个world所有权/生命周期恢复。
- 对既有case0/2/3，依照原件谓词独立构造稀疏输入、执行审查器自己的惰性解释器；216个已知字节与原件实际值匹配，3,080个None保持未知。该投影与2个作者负向guard均不增加原件样例，未执行作者模型自检。

## 来源与边界

17个冻结源、10个production源、34条本地import边全部独立核对；before/after/prepared/snapshot/current一致。期待在原件进程启动前冻结，input无expected。原件进程96231在5.680秒内exit0、PID/PGID消失；56个fresh实例恢复已观察的166,395,904B snapshot，host调用0/878deny，277次stack guard通过，256MiB上限。内部17217/16340调用数仅由静态链推断，未冒称插桩计数。独审首轮进程8190在0.622秒内exit0、PID/PGID消失。

本批使用显式恢复的world/allocator输入与独立Game fixture，不是fresh world producer、实际AI/incoming/玩家死亡同状态续接、自然App或完整880。primary实际缺席，23181最近点Z-only分支只有静态/接口恢复，没有本批动态信用。没有恢复externref表、联网、用户存档或执行Windows原件。下一组合仍须通过真实世界适配调用这个已验证消费者，不能把56个组件样例计为新的完整游戏帧。
