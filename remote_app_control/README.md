# ADB Emulator Control

这是“Python 服务端窗体 + ADB 直连模拟器”的控制方案。服务端不再依赖控制 APK，不需要在模拟器里安装 Remote App。

## 架构

```text
remote_app_control/
  python_server/    Python UI、HTTP API、多设备任务调度

emulator_bot/       ADB 客户端和 SGZZ 脚本逻辑
assets/templates/   SGZZ 图像识别模板
sgzz_accounts.txt   默认账号配置
```

核心流程：

1. 服务端通过 ADB 扫描已打开的模拟器。
2. 在窗体中手动绑定要控制的模拟器。
3. 每台模拟器启动独立脚本线程，互不阻塞。
4. 截图、点击、滑动、输入、启动游戏都直接走 ADB。

## 启动窗体服务端

推荐双击：

```text
remote_app_control\start_ui_silent.vbs
```

或者在 PowerShell 运行：

```powershell
cd .\remote_app_control
powershell -ExecutionPolicy Bypass -File .\start_ui.ps1
```

第一次启动会自动创建 `.venv` 并安装：

```text
flask
opencv-python
numpy
```

## 使用步骤

1. 先打开模拟器。
2. 在服务端 UI 点“扫描模拟器”。
3. 选中 ADB 在线设备，点“绑定选中模拟器”。
4. 可以先点“打开最新截图”或“发送点击”验证控制链路。
5. 再运行“点赞全流程”或节点任务。

首次运行前，在仓库根目录创建两个仅保存在本机的文件：

```text
sgzz_accounts.txt      每行填写 账号#密码
sgzz_like_target.txt   填写目标玩家编号
```

这两个文件及 `config.toml`、日志和打包目录均已加入 `.gitignore`，不会提交到 Git。

如果 ADB 设备没有自动出现，可以在“手动连接”里填：

```text
127.0.0.1:5555
```

然后点“连接并绑定”。多开时可用 `5557`、`5559`、`5561` 等端口。

## HTTP 接口

```powershell
curl http://127.0.0.1:8766/health
curl http://127.0.0.1:8766/api/devices
curl -X POST http://127.0.0.1:8766/api/devices/emulator-5554/bind
curl http://127.0.0.1:8766/api/devices/emulator-5554/latest
curl http://127.0.0.1:8766/sgzz/status
```

手动命令：

```powershell
curl -X POST http://127.0.0.1:8766/api/devices/emulator-5554/command -H "Content-Type: application/json" -d "{\"type\":\"tap\",\"x\":360,\"y\":900}"
curl -X POST http://127.0.0.1:8766/api/devices/emulator-5554/command -H "Content-Type: application/json" -d "{\"type\":\"keyevent\",\"keycode\":\"KEYCODE_BACK\"}"
```

SGZZ：

```powershell
curl -X POST http://127.0.0.1:8766/sgzz/start-game -H "Content-Type: application/json" -d "{\"device_id\":\"emulator-5554\"}"
curl -X POST http://127.0.0.1:8766/sgzz/run-node -H "Content-Type: application/json" -d "{\"device_id\":\"emulator-5554\",\"node\":\"daily_signin_like_gacha\"}"
curl -X POST http://127.0.0.1:8766/sgzz/run-account-batch -H "Content-Type: application/json" -d "{\"device_id\":\"emulator-5554\",\"max_cycles_per_account\":80,\"include_gacha\":true}"
curl -X POST http://127.0.0.1:8766/sgzz/stop -H "Content-Type: application/json" -d "{\"device_id\":\"emulator-5554\"}"
```

账号文件默认仍使用仓库根目录的 `sgzz_accounts.txt`。
