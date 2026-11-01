# 0.135.1 地形组件独立复核

独立只读复核通过。[主审查证据](../evidence/terrain0135-independent-review-20261101T082110.575507Z/review.json) SHA `c0babbe9f8802eb21a90afc26ed390f4d8c6907834e0ba2e44cd598087fdc4fe`；[机器报告](2026-11-01-terrain0135-independent-review.json)关联冻结源码、原件角色及[真实 MPQ 再读回补充](../evidence/terrain0135-independent-review-20261101T082110.575507Z/provenance.json)。没有重跑原件、联网或修改作者源码、收据和旧失败证据。

最终 080051 收据 SHA `45a2501da4ceef05fa66992bf45df30f5aaa2c4502e0dc9e22c94a12b8ca5be7`。14 份源码快照前后与当前一致，resource/core 两个包入口及完整生产闭包齐全；5 个角色绑定 1446、5795、46295、18670、29631 的签名、本体边界与 SHA 均按原始 code section 独立验证。原模块所有非 export section 逐字节不变，原 export 保留、仅追加批准角色；manifest/module 与收据 SHA 再次核对。

107 份完整 ADT、153,802,039B 全部重新从真实 MPQ 解码，逐字节等于本批 actual-assets。两份 archive 完整 SHA、解密表 SHA 与已有 StormLib 验证索引一致，每个链名唯一归属，长度及 payload SHA 对应一致。该检查不把旧基础资源等同于 0.135.1 全部最新资产。

从冻结生产模块重新解析和生成每个 expected、包围盒、采样输入与 56 项矩阵，与已固定 fixture 严格一致；再逐项比较所有保存原件输出，无 mask、无 NaN 分类放宽。27,392 块、3,971,840 个顶点的 **47,662,080B 完整 XYZ** 与原件 sidecar 逐字节相同，洞标记包含 213 个非零块。另 7,231,488B 原始 264B 记录身份、145 顶点计数与洞字段读回一致；其余物理字段没有冒称已独立重造。

3,650 个实际地形点 × 5 层消费者，加 56 项受控洞/栅格矩阵及 107 次完整解析，共 18,413 次已保存原件调用复比较一致。地形 found 为 3,586，not-found 为 64。主缓存 NaN 不回退、次缓存只抬高已有地面、无效返回附带 word 与直接块定位后不二次扫描的边界均保留。

纯本地组合批 080701 的 9 源快照也独立复核：重新执行 WDT→ADT 规划与地形构造，12 zone、120 次 provider 读取、114 份不同资源和中心采样与原 replay 一致。没有执行原件，也没有将这 12 区重放追加到 107 差分组数。模型地板、碰撞、导航、两套缓存 producer、完整 116B world/1089 入口仍未知；SM 的地面高度不能替代建筑地板。

审查脚本的当时完整源码保存在证据目录 `reviewer-source.py`，其 SHA 与主 review 记录相同。之后几何审查对同名工作脚本增加了初始 Boss 消息前缀处理；本审查按保存版本可复核，补充 `provenance.py` 保存了 manifest/module 与真实 archive 读回的独立检查。没有用工作脚本新 hash 冒充本次历史版本。
