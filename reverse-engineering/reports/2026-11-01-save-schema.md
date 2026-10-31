# 0.126.0：账号存档结构、封装及职业地图解锁往返

已恢复当前核心的 **368B账号聚合、24种正常写出tag、旧`unlock`别名、无tag角色记录，以及未知行保留入口**。已静态闭合一条实际状态修改：**职业开放区域数更新 → 明文序列化 → RSE1封装 → 解封自检 → 浏览器存储 → 再读/解封 → 恢复同一进度向量**。

这已超出JS桥函数清单，但还不是完整存档实现验收。所有记录入口与布局在同名JSON中；角色部分字段的玩法含义、全部解析限制/迁移规则、导入确认和备份轮转仍需继续细化。没有读取真实用户存档，也没有执行原游戏或原件微WASM。

## 固定版本与复现

- 0.126.0 / `3e72472a`，原WASM 90,116,970B。
- SHA256：`067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c`。
- 完整WAT SHA256：`02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c`。
- 本轮成功运行保留33个完整函数、43条连续指令guard、25项静态已知tag表、26份格式模板、44条默认构造常量写入。
- 本机Evidence：`evidence/save-schema-20261031T230727.871372Z/`。每个函数均保留原二进制body范围/SHA256及完整WAT范围/SHA256。
- 同33个函数另经明确本地REA扩展绑定Evidence `ev_35611e6267c10e5a1e54f49b4bbd4eb95d3f52408471a41a2a80a728a559a583`，原版REA的大小限制未改；该Evidence保留函数身份，不表示自动恢复全部存档语义。

```sh
python3 reverse-engineering/scripts/trace_save_schema.py \
  --index reverse-engineering/evidence/wasm-index-20261031T213003.825753Z/index.sqlite
```

脚本只读已识别原WASM、原JS和SQLite索引；通过seek读取指定完整WAT函数。输出写到新建忽略证据目录，运行末尾复核WASM及三个JS原件。脚本中的独立RSE1模型只处理内置合成字节，4份合成输入完成模型自身往返和篡改tag拒绝；**这不是原件差分验证**。

另一次只读独立审查从原code/data节重新核对33个body、33份完整WAT、43条guard、25tag与44默认store，并核对原件、完整WAT、索引和JS前后身份稳定；未再次运行目标或合成模型。回执为证据目录中的`independent-review-2.json`。提取脚本自身末尾没有重验WAT/index，本次审查补齐了该轮输入稳定性核对。

## 格式与账号布局

核心980生成UTF-8逐行文本。字段用`|`，列表通常用`,`，列表内部键值用`:`或`=`；换行是LF。889按记录类别分别扫描输入，5361解析无tag角色行。没有发现JSON/RON序列化被用于这条账号存储链。

`A = G+3696`是此路径的账号聚合。Vec的三个u32依次为`capacity,pointer,length`；字段名为本轮分析命名，不是恢复出的Rust原标识符。

| A偏移 | 结构 | 内容/入口 |
| --- | --- | --- |
| 0..63 | 8×u64 | `stat`，依次kills/gold/guardians/bosses/runs/wins/caches/marks |
| 64 | u32 | `resets`，零时不写出 |
| 68..103 | 可选选择结构 | `pick`；+68为-1表示无选择，其余失活字节不要求初始化 |
| 104 | Vec，元素48B | 无tag角色记录 |
| 116 | Vec，元素8B | `open`：职业u8、+4开放数量u32；读入也接受`unlock` |
| 128 | Vec，元素4B | `items`，u32 ID |
| 140 | Vec，元素232B | `equip`与`look`，每职业装备及外观 |
| 152 | Vec，元素24B | `talent`，两个key字节和可选节点/等级组 |
| 164 | Vec，元素52B | `spec`，两个key字节和三组配置 |
| 176 | Vec，元素16B | `seen`，String及u8值 |
| 188 | Vec，元素4B | `ach`，u32 ID |
| 200 | Vec，元素24B | `achat`，String及+16的u64值 |
| 212 | Vec，元素8B | `beat`，职业u8及区域index u32 |
| 224 | Vec，元素4B | `coopbeat`，区域index u32 |
| 236 | Vec，元素16B | `perk`，String及+12的u8值 |
| 248 | Vec，元素4B | `tabard`，u32 ID |
| 260 | Vec，元素1B | `races`，u8 ID |
| 272 | Vec，元素4B | `pets`，u32 ID |
| 284 | Vec，元素8B | `hero`，三字节key和五字节数组 |
| 296 | Vec，元素8B | `marks`，职业u8及+4的u32值 |
| 308 | Vec，元素8B | `stars`，u32 key及+4的u8值 |
| 320 | Vec，元素8B | `pity`，u32 key及+4的u8值 |
| 332 | Vec，元素8B | `hbeat`，区域index u32及+4的职业u8 |
| 344 | Vec，元素8B | `glow`，职业u8及+4的u32值 |
| 356 | Vec，元素12B | 未知记录String，最后重新写出 |

正常写出入口如下。`u8/u32/u64`指已核对数字formatter位宽；原件formatter的间接表slot和相应完整函数也保留在证据中。没有给未追到玩法消费者的裸字节强加race/gender等语义。

```text
u64|string|u8|u8|u8|five-u8-csv|u32|u32|u32|u32
pick|u8|u8|u8|string|string|five-u8-csv|u8
open|class-u8|zone-id
items|u32-csv
equip|class-u8|slot:item-u32-csv
look|class-u8|slot:item-u32-csv
talent|u8|u8|node:rank-csv
spec|u8|u8|group0|group1|group2
seen|string:u8-csv
ach|u32-csv
achat|string=u64-csv
stat|name=u64-csv
beat|class-u8|zone-id-csv
coopbeat|zone-id-csv
perk|string:u8-csv
tabard|u32-csv
races|u8-csv
pets|u32-csv
hero|u8|u8|u8|five-u8-csv
marks|class-u8|u32
stars|u32:u8-csv
pity|u32:u8-csv
glow|class-u8|u32
hbeat|class-u8|zone-id-csv
resets|u32
```

`talent/spec`组内的可选节点标记和每个裸字段的合法值没有完成全分支规格；上面为已恢复的外围语法。`pick`的两个String位于+80和+68，五字节数组位于+95..99，末项是58403格式化的+100 u8十进制值。每个原始格式模板均有原始hex、内存地址和哈希，避免把摘要当成完整parser规则。

48B角色元素的十个字段依次读取：`+0 u64、+8 String、+36/+37/+38 u8、+39..43五个u8、+20/+24/+28/+32 u32`。5361要求至少10个`|`字段，解析数值后写回同一布局。+8的String是`capacity,pointer,length`，不是外部ID。

232B装备/外观元素的`+228`是职业字节。`equip`从`+152..227`读取19个u32槽位，零项不写出；`look`从`+0..151`读取19组`presence-u32,item-u32`，只有presence非零才写出`slot:item`。因此不能把`look`误读成另一份19个u32数组。

区域字符串来自12项地图表，顺序为：`elwynn,duskwood,wsg,ungoro,ab,feralas,arena,sm,av,brm,aq,naxx`。内存中通常保存区域index/开放数量，写出时才还原字符串。`stat`只在任一计数非零时写出，并按固定顺序生成八个`name=value`项。

## 一条实际解锁修改与往返

4801接收`G,classByte,zonePtr,zoneLen`。880在相应终局处理路径检查`G.u32(416)!=0`且`G.u8(2304)&1==0`后，以`G.u8(376)`和`G.ptr/len(200,204)`调用它。本轮只按已证明的原始guard陈述触发条件，没有把这两个未知字段直接命名成“已杀最终Boss”。

4801的持久部分可写成：

```text
若 G.u64(4312) == 16777215：退出
z = 38110(zoneId)                  # index0..11；未匹配也返回0
若 z > 10：退出                  # 最后一图没有下一张图
A = G + 3696
找到 A.Vec116 中 classByte 相同的元素
若已存在，且 min(oldOpenCount,12) > z+1：退出
若已存在：element.u32(4) = z+2
否则追加8B元素 {u8(0)=classByte, u32(4)=z+2}
3903(A)
```

例如`z=0(elwynn)`写开放数量2。980将其钳在1..12后取`zone[count-1].id`，所以文件行是`open|class|duskwood`，不是`open|class|2`。当前开放数量已足够时不重复保存。

写入继续经过以下真实消费者：

1. 3903调用980，把这个账号结构生成明文；980从`A+120/+124`取得开放进度元素指针/数量，按8B遍历并渲染`open`行。
2. 3903把明文ptr/len送4427，获得`RSE1:`文本；又把封装文本送27429，验证解封后长度相同并通过81718字节比较。正常分支调用51776写封装文本；自检失败时输出明确日志并让51776写明文。
3. 51776获取Window/localStorage，以地址1800780、长度16的固定键`rogue.characters`调用93274。93274最终调用WASM import649；原`wenilla.js`的匹配函数调用`storage.setItem(key,value)`。
4. 2883通过47324读相同固定键；65427最终调用import641，原JS对应`storage.getItem(key)`。
5. 封装文本经27429还原UTF-8；明文与旧未封装文本均进入889。889接受`open`或旧`unlock`，解析职业与区域；同职业重复项合并取最大开放数，最后将临时Vec的capacity/pointer/length分别写回`A+116/+120/+124`。

43条连续指令guard覆盖上述链的关键调用、字节比较、真实字段写入和导入函数。它们证明静态路径和版本身份，不证明某台设备localStorage在运行时真的写入成功。51776会处理并丢弃浏览器存储异常，没有把持久成功结果一路返还调用者。

## RSE1封装的具体结构

4427、27429、18819、3640和1436一起给出：

```text
RSE1: + standard_padded_base64(nonce16 || ciphertextN || tag20)

K = 原始静态内存[1744646 : 1744688]       # 42字节，公开二进制内嵌常量
pad_i = HMAC-SHA1(K, "ks" || nonce16 || LE64(i))
ciphertext = plaintext XOR pad_0 || pad_1 || ...   # 每块20字节
tag = HMAC-SHA1(K, "tag" || nonce16 || ciphertext)
```

这里并没有把WASM调用名称猜成某个加密库：3640保留了64B key块、`0x36`内pad和`0x5c`外pad；1436保留SHA1的轮常量/32位旋转及20B输出；18819按初始零值u32计数器扩为LE64、每20B递增后对输入逐字节XOR。封装和解封使用同一个18819。4427从95651的RNG状态取得16字节nonce，本轮没有完整重建该RNG。

27429先通过18163做Unicode两端trim，再依次处理前缀、base64、至少36B长度、tag三段比较、XOR和UTF-8校验，失败返回-1。脚本模型当前只实现严格前缀/base64子集，未复现外层Unicode trim及全部base64容错，不能替代完整原parser。JSON只记录静态key的范围与SHA256，不复制此常量到报告正文。脚本模型从已验证原件的该范围取值，生成合成fixture，不接收用户存档路径。

## 缺省、旧记录与未知内容

2883的无可用账号路径用44条常量store构造默认聚合：八个统计和`resets`为零，`pick`为None，所有Vec长度为零。Vec的4/8/1等非零指针值是空分配哨兵，不能据此推导初始解锁玩法。失活的`pick`载荷等区域没有完整初始化；JSON明确记录未写范围，零填投影只用于可复跑比较，不能宣称这些未写字节在原件中必为零。

原件兼容处理不止“读成功/否则清零”：2883含`.legacy`、备份及不可读内容保存分支；本轮完整保留该函数，但没有把每个分支升级成可实现的迁移规格。

已完整识别的未知行保留入口在30934：它取每行第一个`|`字段，排除ASCII数字开头的角色记录，再与静态25项已知tag表比较。表恰为24种正常tag加`unlock`。其余记录保留成String写入`A.Vec356`；980在所有已知记录之后追加这些行和LF。**已知tag即使其记录内容无效，也不会因此转入未知行保存。**未来未知tag并非直接丢弃。

## JS文件桥与边界

原`saves.js`不解释存档内容：`download(text)`以octet-stream Blob生成`.sav`下载；`pick()`让玩家选`.sav/.txt`，读取为`{name,text}`并增加`state.rev`；`take()`只返回一次并清空。`rogue.js`也存在以`rogue.characters`或`rogue.characters.backup.1`导出文本的启动失败救援按钮。这里没有读取浏览器存储、调用文件选择或实际下载任何玩家数据。

还需继续的具体部分：

- 角色/pick/hero每个裸字段的玩法名称、合法值和缺省迁移。
- 889所有tag的数值上下界、重复项策略、无效ID过滤、未知/损坏输入处理。
- `talent/spec`可选组完整语法、装备/外观项目对应全部目录及真实消费。
- 1160导入校验/确认/替换流程，以及3903/2883的全部自动备份、轮转、恢复和`.legacy`策略。
- 独立存档模型、原件隔离差分与跨端文件互通；当前仅有静态规则和合成模型自检。
