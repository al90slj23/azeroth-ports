# 0.135.1 None-aware 424B records 与AI/corpse默认回归

`record_cells135.py` 已提供显式未知byte的物理行API；`ai135.py` 与 `ai_lifecycle135.py` 已改为按实际字段读写，未读padding保持 `None`。既有完整hex输入仍输出原hex格式，默认字段行为未变。

固定官方 `0.135.1 / 0898d5e3`，WASM SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。本批不构成0.136验收。

[最终收据](../evidence/record-cells-ai0135-20261101T143057.757089Z/comparison.json) 冻结17源，SHA256 `73409f0a763f9ac8ecc85bce399de33234fa53bcd638020f19fdae80a62a3a37`。结果：

| 验证 | 范围 | 结果 |
| --- | --- | --- |
| 已有AI完整hex默认回归 | 416组、1013次完整921阶段；原输入/预期未改 | 0差异 |
| 已有corpse完整hex默认回归 | 35组、35次完整921；仅传输ID重排，物理输入/预期不变 | 0差异 |
| None条件读取小检查 | 16项纯独立模型检查 | 通过 |

先将当前独立模型对旧封存输入/预期重放，再在现成quiet Node fixture重跑完整原件921；35组corpse不执行2088。未知行从未转换为0/poison、从未送入原件。None检查包含未读padding与inactive slow/weakness magnitude保留、active分支必须已知、movement duration/marker消费缺失拒绝，以及corpse marker0不读U4、marker1必须读U4、mode0不读owner、年轻corpse不读owner/GUID。

API保持root指定名称：`cells135`、`u32/i32/u64`、`put_u32/put_u64`、`encode_row`、`known_bytes`、`optional_u32/optional_u64`、`UnknownRecordRead135(offset,width,consumer)`。`cells135`返回新mutable list并验证长度、byte0..255/None；`encode_row`全已知时返回旧hex，含未知时返回immutable tuple。仅被读取的字段要求已知，optional读取只把未知返回None，其他错误仍抛出。

AI算法及原finite/ordinary/flat来源域未扩大。已知浮点仍接受原finite guard检查；未知词不会被该guard提前材料化，而由选中的真实读取分支明确要求。corpse保持stable all-matching GUID removal；无待删除GUID时不引入额外GUID读取。

两次受控Node分别耗时0.688秒和0.292秒，单进程60秒时限，32MiB上限，实际最高20,643,840B与14,680,064B。全部878个host导入拒绝、实际host调用0；两进程组已清空。只有export section变化，所有原内部callee保留；本批未动态导出栈，也没有运行原App、网络或用户存档。

没有修改headless、combat、unit adapter、cast、area或spawn系列。真实opening/world组合由root另验，本批不把None条件检查转计为新增原件接受域或完整游戏证明。
