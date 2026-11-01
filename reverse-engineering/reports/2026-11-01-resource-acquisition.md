# Windows 基础资源包验收

用户最初提供的完整 `AzerothSurvivorsWindowsNew.rar` 实际保存在4T外盘下载目录。本次保留原文件，复制到研究原件区后，完成全包CRC提取与全部提取文件SHA复核：**754,921,096B RAR，8个文件，其中7个MPQ，展开共1,777,452,318B**。没有执行包内程序，也没有改动安装游戏或存档。模型、地图、音画和DBC的独立索引/加载尚待恢复；资源可用不等于资源管线已实现。

本地整包SHA-256为 `6cf1108db4e8bd7f55e214e24e976a6f24ab657a3eed86c16743ff76e6b85671`。此前从[官方资源地址](https://wow.aethus.pl/download/AzerothSurvivorsWindowsNew.rar)验证下载的69个块及严格HTTP206末尾4KiB，共289,411,072B，与这份本地完整文件对应偏移逐字节哈希一致。官方ETag为 `"6ad660ef-2cff2e88"`。这是“完整本地CRC＋官方部分字节比对”，不声称本次重新下载了整个包，也没有取得官方独立发布的整包SHA。

包内EXE仍是 **0.102.3 / f78e6fab**，139,691,008B，SHA `2c2f3926e1f8f8092809f5de0624ac8f2197bb341a2870d408ce0250f13f094a`。新版程序须另外按[官方更新清单](https://wow.aethus.pl/exe/latest.json)下载及校验。不能将这个旧基础包称为最新客户端，也不能仅凭资源相同推定新旧玩法一致。

原件、MPQ与逐文件清单仅在本机 `originals/official-acquisition-20261031T235700.049192Z/` 保存；相邻JSON记录文件元数据和验收收据哈希。全包验收结束后没有下载/重试后台进程，预备续传控制器未启动。
