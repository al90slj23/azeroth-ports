# 0.135.1：真实菜单到运行态 Game

本轮用原版菜单点击和真实 W 输入，观察到自然 Game 安装、phase0→1、世界内生成以及运行时钟推进。[机器摘要](2026-11-01-game-entry0135-probe.json)与[独立复核](2026-11-01-game-entry0135-independent-review.md)分别保存。**这是受控原版行为观察，新增独立模型用例和独立主循环帧均为0；完整独立一局仍未实现。**

## 身份与实验方式

2026-11-01T13:26:11Z重新获取[官方更新清单](https://wow.aethus.pl/exe/latest.json)，仍为0.135.1。现有Windows EXE147,797,504B的SHA重新计算后与清单`71e5f1767279db4bd428d1cd9c5d50d37759b72295386a69f9e3f6e70bc59249`一致；没有执行Windows程序。

Web固定0.135.1 / 0898d5e3、原WASM SHA`c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。私有模块仅追加global0导出，36→37 exports；函数、表、memory、data逐节不变，WABT验证通过。global0本身仍mutable，宿主只读取其值，没有写入栈、借用标志、App、Game、profile、world、Once或命令。

原4253构造App，经cast867/vtable5305816得到真实闭包；原25ms interval持续运行。独立Chrome/Apple Metal-3环境中先点击“进入艾尔文森林”，等真实素材请求稳定，再点击画布并按住W。DOM记录8条`isTrusted=true`输入事件。所有原878浏览器绑定仍委托官方实现，研究桥只追加在原JS完整前缀之后。

## 实际观察

| 项目 | 本轮结果 |
|---|---|
| 完整880返回 | 603次，借用标志和实际读取的stack均恢复 |
| 自然Game安装 | 第16帧，tag0、phase0、真实worldRc24229960 |
| 运行态返回 | 第595..602帧，共8次；7次时钟递增 |
| 游戏时钟 | 0.0260000005→0.2659000158秒 |
| 末态对象 | 7个units424、2个pickups56；无active companion；另有真实special/window/boundary状态 |
| 资源 | 2418个唯一MPQ文件、164,823,373B，逐文件SHA复核 |
| HTTP与页面 | 4522次200，2次favicon404；游戏素材无失败，0 page error |
| 保存 | 同步复制1,378,877,440B未共享memory，完整上传并重算SHA |

快照SHA为`c461b2f5efb1399127d22c04fbe5efed15f8b8411ceeefe22a05b4dce45bfd15`。小型完整观察先保存为`observation-before-upload.json`，SHA`751c4d251eeea95b6211069f295ac251ff9bb83cc78147255fcdb739f34071cb`，随后才上传大快照。

此时已执行开局后的正常880工作，不能把7个units与“1089刚返回”的4NPC状态直接比较。完整帧入口时间、前后App/Game字段、首运行态检查点、实际向量容量与active字节均保留。默认角色是class1/race1；实际owned为cleave、execution5，旧headless尚不支持这一入口。

pre-poll Vec232只捕获到tags30/31/33及11。Start按钮的精细producer、peer消息和内部投递链仍未完全定位；不能把此前静态raw23候选当作本轮已观察到的命令。

## 保存边界与宿主隔离

本轮新增下载、解包、研究临时文件、缓存、profile、素材和证据均在4T目录；现有Chrome、Python与Playwright按实际安装路径和所述SHA绑定，未重新下载或迁移。未使用用户浏览器或游戏存档。独立不转发代理、DNS和CSP共同限制外发。CSP实际阻止presence请求；代理还记录若干来源未归属到游戏页面的浏览器进程请求，不能声称“没有联网尝试”。没有真实联机交付或Windows跨端验收。

此宿主采用2GiB WASM上限、768MiB JS heap、8192文件/512MiB解码素材预算、240秒inner/270秒outer时限。完整冻结副本是额外分配，以上不是总RSS上限；旧32/128/256/512MiB实验政策没有改变。

复制memory后，才取消原import507实际观测到的919个RAF handles，避免渲染继续占用导出资源。保存了来源、数量和顺序，未保存逐handle清单；不声称析构、Rc生命周期或后续渲染等价。此文件是线性内存快照，不是JS、externref、GPU或完整VM检查点。

node、worker和Chrome均结束，独审再次确认所有所属PID/PGID消失。12份研究源、声明的程序和工具身份及配置前后校验通过；Playwright包元数据hash不是完整node_modules或OS镜像闭包。

## 已保留的失败与未完成项

四个先行实验原样保留，各有`post-exit-diagnosis.json`：代理归属误判、过短状态读取期限、2048文件预算/渲染边界，以及首次全量导出超时。最后一项只写入867,172,352/1,355,153,408B，不是完整快照；其8次运行态状态不能替代最终603帧的逐帧证据，也不重复增加覆盖。

[只读采集接口](2026-11-01-game-entry0135-capture-schema.md)现拒绝底层仍可变的readonly memoryview，避免同次采集得到相互矛盾字段。原版padding仍作观测值；独立开局中的None不因此变成可预测字节。

下一步是把真实输入、独立world/opening和战斗接到同一实现：保留实际容量、先行NPC、kind2、special、window、边界与未知字节，恢复真实活跃消费者和cleave execution5。独立headless的固定128槽、NPC字段提前读取、平地假设、完整880前段与所有权仍是明确缺口。旧14尾切片、44个已验独立domain及共享52角色计数保持原身份，未因本轮原版观察而增加。

实际running快照的[只读投影与交接清单](../evidence/game-entry0135-running-capture-20261101T135831.387639000Z/notes.md)完整读出6,120,808B声明范围，无boundary。当前claims、hits等为空，不把它们列为此case的即时阻断；special4/protection0、非flat world、真实capacity及phase1交接仍需恢复。
