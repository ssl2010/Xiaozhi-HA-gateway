# Xiaozhi Home Assistant Gateway

小智 ESP32 终端与 Home Assistant 之间的本地语音网关。目标运行环境是
Proxmox CT 103（Debian 13，`192.168.3.188`，2 vCPU / 2 GB RAM）。

## 设计约束

- 唤醒词在 ESP32-C6 本地完成。
- 语音上传后由 Sherpa-ONNX Paraformer 中文 int8 模型本地识别。
- 家居控制使用白名单实体和确定性中文语法，不由大模型猜测。
- HA Token 只通过部署端 `.env` 注入，不进入镜像、源码或日志。
- 次卧空调尚无 HA 实体，任何相关控制都会明确拒绝。
- 未配置的显示字段不返回；已配置但状态为 `unavailable` 的字段返回离线状态。

## 支持的控制

- 主卧、客厅、书房空调：开关、16–30℃、风速、摆风。
- 主卧、次卧、客厅、书房灯：开关、亮度、效果模式。
- 支持用逗号分隔的多房间命令。

## 本地测试

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## 部署

1. 将 `.env.example` 复制为 `.env`，只在服务器填写 HA 长期访问令牌。
2. 将 `data/.config.yaml.example` 复制为 `data/.config.yaml`。
3. 下载 Sherpa-ONNX 中文小模型到 `deploy/models/`。
4. 运行 `./scripts/deploy.sh`。
5. 运行 `./scripts/verify-deployment.sh` 验证容器、OTA 地址、显示数据契约和令牌日志。

`server_overlay/Dockerfile` 默认使用已经验证并固定摘要的上游镜像。升级上游
小智服务器时，应先在测试环境重新构建和验收，再有意更新该摘要。

服务端口：

- `8000/tcp`：小智 WebSocket
- `8003/tcp`：小智 OTA 配置接口
- `8090/tcp`：ESP32 房间状态只读接口

生产服务器上的项目目录为 `/opt/Xiaozhi-HA-gateway`。部署脚本只读取该目录下
权限为 `0600` 的 `deploy/.env`，不会把 HA Token 写入镜像或 Git 仓库。
