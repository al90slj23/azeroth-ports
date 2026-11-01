# 部分App构造投影的独立静态复核

对 [app_state135.py](../reconstruction/core_spec/app_state135.py) 的独立静态只读复核通过，绑定生产SHA `4f1e4a3b048a9491ea8edae34ec9e1c97916d8f2e1ef06b6db12c1b9bb9fb1da`。所审是32组原4253直线窗口的本地重组，**新增WASM执行0／原件差分0**；`legal_full_app`始终False。root另行取得的真实App及880观察，不并入这32组静态计数。

作者最终[10源静态收据](../evidence/app-state0135-static-check-20261101T121056.399055Z/comparison.json) SHA `93c92bd3525979fe61ce187742eb7c763d7ed02be64150d338880ccc80f1d7c2`；[最终独审](../evidence/app-state0135-independent-review-20261101T121623.578791Z/review.json) SHA `e706357340af3af5bc7b01d375f4145d025c4af69a3fc9404ec646e94683f240`。[机器报告](2026-11-01-app-state0135-independent-review.json)保留源码、WAT查询／body SHA、逐byte写入trace、合同边界与来源。

## 独立解释与字节范围

[review_app_state135.py](../scripts/review_app_state135.py)没有导入生产模型或作者解释器。它重新从固定WASM／只读SQLite获取4253、880、1371、58521、83825、122123的精确WAT范围，核对原byte／body SHA；另直接解析WASM data section，重建16B空table头、13B `azeroth.local`与20B真实回调vtable，再重读element table确认slot4472／4473对应58521／83825。

reviewer另建逐byte内存和WAT解释器，App用0x70000、scratch用0x90000，与作者地址不同；源副本和目标均不依赖地址巧合。只有实际解码的静态16B／13B源区允许出现模块初始化已知零，其余未映射读取全部保留None。`store8`、`store32`、`store64`分别写1／4／8B，非对齐offset直接按字节处理；`memory.copy`先获取源byte快照再写目标，保留memmove／alias含义。

| 输入域 | 每份已知byte | 每份None | 本批组数 |
| --- | ---: | ---: | ---: |
| 无上游livecopy | 730 | 4,438 | 16 |
| 显式368＋48＋36B livecopy | 1,182 | 3,986 | 16 |

32组累计30,592B已知值和134,784个None位置，逐项与作者输出相同。每条真实写指令的宽度、目标、已知byte数和重叠数都另存：4148与4151的两次4B零写仅重叠1B，最终恰好7B；5163未对齐4B写到5166，5167仍None；13B server字节来自两次相差5B的8B写。history240与map128分别在3752..3991和3992..4119，4120之后其它字段未混入map。

Game2592、第二variant768、selected-profile376和party选项只按原store宽度写tag，inactive payload均保持None。三块livecopy只有明确输入时才写368／48／36B；这些字节没有冒称上游settings／profile producer已恢复。LCG来源和其他pointer／entropy也继续显式提供。32组4936计算的`select`条件均为0，另一分支只有静态表达式依据，本报告不把它记为新增case覆盖。

## 回调、所有权和来源闭包

真实5305816回调vtable及原83825支持纯指针合同：env+8读Rc，Rc+16为App；回调内部在borrow守卫下将秒参数传给880（原毫秒／1000），25ms interval设置另有原4253窗口。模型的helper仅解码实际受控vtable与显式memory provider，不能由算出一个地址就宣称App合法或拥有完整生命周期。

5184B Rc allocation、strong／weak／borrow位置和App+16布局与原owner窗口一致，padding9..15仍未知，最终holder数量不预言。Game的2592B安装只是一份move合同：旧tag非2时调用1627，前置24129和完整caller副作用未实现；复制本身不额外增加world Rc，源必须forget，不能把它误作clone。reviewer通过AST读取合同常量并结合原880／1371窗口核对，未调用这些原函数。

静态checker最初7源遗漏包入口导入的`upgrade_values.py`／`binary32.py`，作者已补为完整10源并重新本地重组。旧证据未改；input、expected、WAT窗口及每个None mask保持相同，仍是同32组静态案例。reviewer独立收集闭包并检查10源与snapshot前后SHA，再将自己的脚本及只读data解析依赖另行冻结。

真实cast的730B投影比较和真实App上的880调用是后继独立证据，本报告没有审入。完整可独立运行的App构造、上游copy／熵／分配器／所有权生产、24129／Game安装、游戏态880及整局仍待各自验收。复现：`python3 -Werror reverse-engineering/scripts/review_app_state135.py`，不会执行WASM、浏览器或修改安装包／存档。
