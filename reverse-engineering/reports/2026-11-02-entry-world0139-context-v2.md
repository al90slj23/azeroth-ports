# fixed139 world/opening上下文 v2：完整2945返回区

**v2原件2917→2945→6786→1108完整返回，2945的36B输出、40B显式返回区、双侧16B canary均核对通过。** 这份新采集用于替代旧夹具存在返回区尺寸缺陷的上下文；独立只读复核仍待完成。它仍是research App/profile输入上的原件观察，独立opening模型用例为0，没有自然App、独立world、native或完整游戏声明。

## 旧观察的真实缺口

异作者复核发现：原件1392945在output参数首次重绑定前，实际写入+0/+4/+8/+12、+16/+20/+24/+28和+32..35，因此返回区至少36B。旧browser fixture仅`alloc(16)`，超过声明的allocation。即使旧6786/1108返回、计数看起来一致，也不能据此把输入视为合法完整上下文。

旧[5d940收据](../evidence/entry-world139-probe-20261102T023815.931445Z/receipt.json)、两份旧memory、8个旧作者文件与报告全部保留原字节，降为受该已知fixture缺陷限制的观察。旧Rc20544640不得继续沿用为新输入。先前引用旧snapshot的NPC组件批次同样不能据此取得合法上下文验收；另外的新实例1600→5719无snapshot分支独立，不依赖这份错误夹具。

v2直接按本版完整2945 WAT1159..1198写集修复，并确认local0首次重绑定在1204，不以旧slot猜测返回长度。

## 新夹具与保护区

新函数仍是原件2945。分配72B，传`base+16`作为输出，明确40B返回区：

- 前16B固定C3，后16B固定D7，调用前后逐字相等。
- 完整36B返回保存；+36..39的4B仍为A5。
- 仅把返回前16B复制到selectedProfile224..239；这是明确的两个随从选择输入，其余profile仍属research输入。

实际allocation=14694088、output=14694104。完整36B为：

`00000000ffa5a5a500000000ffa5a5a50000000000000000000000000000000000000000`

两slot的pointer由原件写0，tag255由原件写入，三字节inactive padding仍A5。其余36B内实际写入字段保存为原件观察，不转成通用非空profile规则。完整canary、40B before/after和36B return均在runtime的`result.selection_output`以及新只读解析里保留。

## 新原件结果

正式[receipt.json](../evidence/entry-world139-v2-probe-20261102T030946.739944Z/receipt.json) SHA `36372f365f9831045a0dab80f1948f445ceda653992a145a03bc051255813eb8`。版本0.139.0 / `f79c5e2b4`，WASM SHA `71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299`；仍仅追加export7，原件函数与callee全部不改。

App14680072、G14685248，新Rc由actual App5116/Game2348动态读取为20544696，不能硬套旧20544640。新[动态只读解析](../evidence/entry-world139-v2-inspection-20261102T031038.882145Z/observations.json) SHA `42a5b6c17ffa0a51e947c1da972aa75521793a48e4f2f2a2540de7e1ae889162`，不以旧指针作输入。

| 阶段 | 内存文件 | 字节 | SHA256 |
|---|---|---:|---|
| 6786后phase0 | `after_real_world6786.memory` | 111,804,416 | `ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2` |
| 1108后phase1 | `after_real_begin1108.memory` | 177,078,272 | `5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0` |

phase0六种实体向量和消息/通知均空。phase1观察为4个Kobold Vermin、0随从、2个pickup、4个special、2个window、69个boundary，counter85，76个完整packet、1个start通知。所有记录与metadata/backing完整保存，观察不等同于独立模型输出。

原件4个组件入口加6个allocator共10次入口，stack全部从1048576恢复到1048576。882准确import中24种已限定资源/Storage语义允许，实际3396调用、16种id，无deny命中；561次loopback资源请求全部200。**这批有真实资源宿主调用，不是all882-denied Node差分。** 新origin三类Storage始终为空，没有用户profile、存档、外网或EXE执行。

Node24683、browser24686均exit0，Node PID/PGID均消失，24.9509秒；沿用明确的256MiB/90s浏览器/120s外层限制及1MiB capture chunk。prepare-only新目录`entry-world139-v2-probe-20261102T030857.153674Z`保留、原件执行0。

## 资源与剩余边界

继续使用已固定的新官方139资源集合及其三段获取收据链；未从旧135/138载入任何资源字节或snapshot。资源最终收据SHA `7aec47c1ce5b6d58f2374878e2f6877e95de4784aed7837a21a2075ecf97ea92`，454条resource-map SHA `3a794c2e35873852cc8f6661fb93ec9edae9a06626277ff123f1612495927ec2`，保留官方139/stamp一致性来源。资源获取的含空格路径失败和修复记录不覆盖。

账号由真正2917从空Storage生产，缺省随从由真正2945生产；App/profile其余研究输入仍未成为自然菜单/App producer。world/cache由原件6786生成，不写入伪造Rc或Once。locale20060→83304为原件路径；4562是Spell.DBC/spellID resolver。JS/externref表和销毁生命周期尚未证明可由线性内存恢复，消费者必须独立核自己的宿主边界。

下一步是新139资源到独立world/query的比较、NPC432/169独立模型和自然position采样，再逐项组合1108。v2只消除本次输出区大小缺陷，不扩大自然App、全locale、完整Game或完整游戏验收范围。
