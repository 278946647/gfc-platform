# Global Forwarding Control Plane (GFC)

全球转发控制平台：集中管理转发节点、客户线路、SOCKS 代理与告警；转发节点在 Ubuntu 裸机上以 sing-box + TPROXY 透明代理运行。

**GitHub:** https://github.com/278946647/gfc-platform

---

## 文档

| 文档 | 说明 |
|------|------|
| **[开局配置与迭代升级手册](docs/SETUP_AND_UPGRADE.md)** | **主文档** — Cursor/Git 同步、控制面/转发节点开局、在线升级 |
| [运维与故障排查](docs/OPS.md) | 架构、日志、`gfc-logs`、常见故障流程 |
| [转发节点部署](docs/NODE_DEPLOY.md) | 节点安装参数与产物说明 |
| [GitHub 部署 checklist](docs/DEPLOY_FROM_GITHUB.md) | 干净 VM 验证用简版步骤 |

---

## 仓库结构

| 目录 | 说明 |
|------|------|
| `control-plane/api` | 控制面 API（FastAPI）：节点激活、配置下发、统计与告警 |
| `web-ui` | Web 管理台（Vite + React） |
| `node-agent` | 转发节点 Agent：心跳、拉配置、渲染 sing-box/nftables |
| `deploy/control` | 控制面 Docker 安装与升级脚本 |
| `deploy/node` | 转发节点一键安装、修复、重配脚本 |

---

## 快速开局

### 控制平台（Ubuntu 22.04 + Docker）

```bash
sudo git clone https://github.com/278946647/gfc-platform.git /opt/gfc
cd /opt/gfc && sudo git checkout -B main origin/main
sudo bash deploy/control/install-docker.sh
```

- Web：`http://<IP>:5173`　API：`http://<IP>:8080`
- 首次安装自动生成 Bootstrap Token / Auth Secret / 管理员密码（见 Web **系统设置 → 平台安全**）

### 转发节点（Ubuntu 20.04+ 裸机）

```bash
sudo git clone https://github.com/278946647/gfc-platform.git /var/socks
cd /var/socks && sudo git checkout -B main origin/main
sudo bash deploy/node/install.sh
```

完整参数与验证见 [SETUP_AND_UPGRADE.md](docs/SETUP_AND_UPGRADE.md)。

---

## 已运行系统升级

```bash
# 控制平台（API + Web，保留数据库）
cd /opt/gfc && sudo bash deploy/control/upgrade-control.sh

# 仅 Web 前端
cd /opt/gfc && sudo bash deploy/control/redeploy-web.sh

# 转发节点
cd /var/socks && sudo git checkout -B main origin/main
sudo python3 deploy/node/repair_forward_node.py
```

日常请跟踪 **`main` 分支**；勿在 tag/detached HEAD 上 `git pull` 升级。

---

## 设计要点

- **控制面与数据面分离**：控制平台故障时，已下发配置仍在节点本地继续转发（sing-box、nft、路由持久化在节点上）。
- **平台安全**：Bootstrap Token 默认锁定只读；修改需解锁 + 双重确认；Token 变更可同步到在线节点。
- **规模建议**：≤10 节点可用 Docker 控制面；转发节点建议裸机（TPROXY / nftables）。

---

## 本地开发

**依赖：** Python 3.11+、Node.js 20+

```bash
# API
cd control-plane/api && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && uvicorn app.main:app --reload --port 8080

# Web
cd web-ui && npm install && npm run dev

# 演示 Agent
cd node-agent && pip install -r requirements.txt
python -m node_agent --server http://localhost:8080 \
  --bootstrap-token demo-bootstrap --node-name demo --region ap-southeast-1
```

Docker 本地/生产：`cp .env.example .env && docker-compose up -d --build`

---

## Web 功能

仪表盘、线路管理、流量、健康检查、代理配置（SOCKS 探测）、转发节点、回程路由、用户管理、操作日志、系统设置（平台安全 / SMTP 告警）。

---

## 许可与版本

MVP 阶段；节点认证为 bootstrap token → node token（mTLS 规划中，见 `deploy/pki/`）。
