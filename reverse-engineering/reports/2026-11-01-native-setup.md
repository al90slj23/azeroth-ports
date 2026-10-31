# REA 原生分析提供方接入

2026-11-01（Asia/Taipei）。已在项目 `.toolchain/` 私有安装 Ghidra 12.1.4 与 Adoptium JDK 21.0.13+9 ARM64，保留系统 Java 与全局 MCP 配置。

NSA 官方 ZIP 和 Adoptium 官方 TAR.GZ 的大小与 SHA-256 均匹配发布元数据。当前 Ghidra 最新 12.2 要求 JDK25；本轮固定 REA 6.8.0 已验证的 12.1.4/JDK21 组合。

官方 ZIP 仅附 Linux/Windows 原生反编译器。本轮使用同一校验归档内的官方 C++ 源码，保持源码不变，以现有 Apple clang 21.0.0 和 Makefile 参数 `ARCH_TYPE=-arch arm64`、`OSDIR=mac_arm_64`、`ADDITIONAL_FLAGS=-mmacosx-version-min=11.0 -w` 编译本机反编译器；产物 SHA-256 为 `7434284fc5a6b46b3cb27ef2e8d3c4ea7f801ac1f0cca30e95eb27732c0c62f0`。

`REA doctor --provider ghidra --json` 已实际执行并 exit 0，显式 Ghidra 范围的 9 项检查全部通过，包括原生 Mach-O ARM64 头、完整64位 JDK、Java21版本和平台匹配。原始诊断保存在本地 `evidence/native-setup/doctor.json`。这只证明提供方前提就绪，不等于139MB原始游戏已经完成导入、自动分析或函数反编译。

可重复执行：

```sh
python3 reverse-engineering/scripts/setup_native.py
```

本机绝对环境位置保存在 `.toolchain/native-install.json`；其中的 `GHIDRA_INSTALL_DIR` 和 `JAVA_HOME` 可传给后续 REA 进程。编译命令、编译器和原生组件摘要保存在 `.toolchain/native-build.json`。

未打开或执行原始游戏，也未进行冷分析。后续应将原始 EXE 哈希与首个具体功能绑定后，使用一份持久 REA 会话完成导入并复用其结果。

详细脱敏记录：[2026-11-01-native-setup.json](2026-11-01-native-setup.json)。
