# 最新137资源对象1420独立实现与原件差分

固定 **0.137.0 / `d171b8f9f`**，Web/WASM SHA `20ec9a2b5182a72e13ca11668ff0aab17e9dc54a10b923b546708ab85e3fe1c8`。本批恢复完整原函数 **1420 的资源kind3/4/5分支**，不包含947调度、资源拾取消费者或完整游戏。

[最终新差分收据](../evidence/resource-pickup0137-oracle-20261101T182737.085717Z/comparison.json) SHA `1e9a748dd96d9c12b239c874067c943a344f96e9fb0eb94c8c3f42510690dba2`：**90 fresh instances / 90完整1420调用，0声明差异**，36源和冻结输入/产物/查询world前后不变。6例pilot单独保留，不与最终90相加，也不转记135资源64或137伤害80的计数。

独立只读审阅发现首90批的35-source冻结漏掉checker专用`initial_state135_data.py`（ZONE_ENTRIES），旧[182323收据](../evidence/resource-pickup0137-oracle-20261101T182323.787663Z/comparison.json)保留为诊断，不作完整source冻结验收。修复后逐文件核对Python AST/JS本地import闭合，36源包含该元数据和包初始化文件；预期生成前也冻结独立world的receipt与3个payload。本报告使用修复后新fresh90实例，不倒填旧收据或累加case。

## 可执行规则

独立模块为[`resource_pickup137.py`](../reconstruction/core_spec/resource_pickup137.py)，API `produce_resource_pickup137(ResourcePickupInput137(...),world)`。它不读原件二进制、memory、存档、文件或网络。复用纯binary32、RNG/actor169编码、56B向量和query接口；复用不是依靠版本号假定：12地图几何已从137新地址逐bit重提，资源分支[静态迁移](2026-11-02-resource-migration0137-static.md)与本批新完整原函数差分分别提供依据。

| kind | visual | display |
|---|---:|---:|
| 3 | 9006 | 5931 |
| 4 | 9007 | 5995 |
| 5 | 9008 | 5991 |

首先以对应地图中心和 `max(f32(radius-2),1)` 限制XY；越界时先执行一次height及必要nearest查询，再进入三个资源共同height分支。原输入Z被查询结果替代。primary不存在且height未命中时使用world+116；primary存在则尝试nearest。primary存在而nearest未命中的原kind参数低地址+116读取仍明确pending，不填造0。

actor使用scale1、kind21=5、flags9=0，消费实际角度RNG并递增wrapping计数，产生完整169。56B记录写marker0、kind+8、原样amount+12、GUID+16、aux(capacity0,pointer8,count0)、visual+36、XYZ+40/44/48和now+52。**+4到达时间不写，保留原槽的已知/未知字节。** amount只是opaque u32，不能按名字解释为经验或金币。实际1420并不执行947的资源数量cap，已有多资源也仍append；容量满时扩为`max(4,2*old)`，新未写字节保持None。

## 比较与原件运行

语料覆盖12地图×3kind×中心/越界72例，独立451资源产生的真实查询输入12例，受控primary直接height/nearest成功6例；共42次clamp。包括空向量、预留槽、容量增长、旧active与inactive完整字节、部分已知+4、marker99、零/高位amount、计数回绕和退化全零RNG。

比较17,418已知值、8,884显式未知字节、90个完整169包/9,269B；未知只准出现在物理56B backing的已声明位置。另逐case检查手工8192B Game输入中，除RNG1720:1736、pickup vector1868:1880、输出packet vector1880:1892、counter2408:2412以外累计733,320B完全不变；G2412和notifications也独立比较。完整before/after Game bytes均保留。

原件使用仅新增1420和global0导出的完整137 WASM，未修改任何callee/code/data、未调用start；私有模块SHA `3b03b60859bd1a286efeb9ee22b72464de1907d61ea9bc657c90566dd47c6299`，原1420 body SHA `5d9f5c8a129a1f74a86b0fd9c57179efbecc0b3daa61123ef6b3d3e923fcd5be`。expected先生成并冻结，runner输入没有expected。878宿主导入全部拒绝，实际0host；WASM32MiB、heap512MiB、owned60秒。PID/PGID97273退出0且missing，2.179秒，峰值20,578,304B，全部调用正常返回且stack恢复1048576。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reverse-engineering/scripts/check_resource_pickup137.py --phase full
```

## 输入身份和剩余缺口

Game8192和Rc124是为隔离1420手工构造的输入，不是原Game/World constructor。world包含两类：明确的flat/primary合成夹具；从135独立451资产producer保留的terrain/nav/secondary规范查询输入，经哈希核对后手工packed进入fresh137原件。后者有真实独立资源来源，但保留**135资产身份**，不声称137资产boot或完整world所有权已恢复。没有读取原件memory snapshot。

Windows同版本原生分支与visual/display、72B原生记录等静态互证见[独立迁移报告](2026-11-02-resource-migration0137-static.md)；Web56B不能套为Windows72B，WASM运行不等于Windows原生验证。

947完整调度/普通432B域接入、资源拾取效果、primary nearest miss、137独立boot与完整局、UI和网络仍待恢复。本批 **0完整947 / 0完整880 / 0 Windows执行 / 0完整游戏**。该限定组件域已通过[独立只读复核](2026-11-02-resource-pickup0137-independent-review.md)，复核收据SHA `e175290ea37ebd87c64b8d73067cc264b952e8bcc94c60d50eff6cac72478ef4`；完整backing、精确None写集、RNG/GUID/169和Game guard、36源及原件身份均核对，审阅新增原件/模型case均为0。当前组件通过不扩大成137主流程完成。
