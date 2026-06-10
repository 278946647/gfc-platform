## Global Forwarding Control Plane (MVP)

This repository contains:

- `control-plane/api`: Control plane API (FastAPI) for node activation, discovery, config orchestration, stats & alerts.
- `web-ui`: Web management UI (Vite + React).
- `node-agent`: Forward node agent that activates, heartbeats, pulls config and acks apply.
- `deploy`: VM/K8s deployment helpers (install script, systemd units, k8s manifests).

### 运维与故障排查

See [docs/OPS.md](docs/OPS.md) — 架构说明、日志保留、排查流程、`gfc-logs` 命令。

### Forward node (Ubuntu 20.04+ one-click)

See [docs/NODE_DEPLOY.md](docs/NODE_DEPLOY.md). After copying the repo to the node:

```bash
sudo bash deploy/node/install.sh                              # 交互填写控制平台 IP、网卡等
# 或: cp deploy/node/install.env.example deploy/node/install.env && 编辑后:
sudo bash deploy/node/install.sh --config deploy/node/install.env
```

### Web UI pages (reference-aligned)

- 仪表盘、线路管理（筛选/分页/详情）、流量、健康检查、代理配置、用户管理、操作日志、使用说明

### 服务端一键启动

**方式 A：脚本（开发/测试，推荐）— API + Web + NodeAgent 三合一**

```bash
cp /var/socks/scripts/gfc.env.example /var/socks/gfc.env
# 编辑 gfc.env：SERVER_URL、NODE_NAME、REGION 等

chmod +x /var/socks/scripts/start-all.sh
/var/socks/scripts/start-all.sh start    # 启动全部
/var/socks/scripts/start-all.sh status
/var/socks/scripts/start-all.sh stop
/var/socks/scripts/start-all.sh restart
```

日志：`/var/socks/logs/gfc-api.log`、`gfc-web.log`、`gfc-node.log`（安装 systemd 时自动配置 **约 1 天** logrotate，见 [docs/OPS.md](docs/OPS.md)）

**方式 B：开机自启（systemd）**

```bash
chmod +x /var/socks/deploy/systemd/install-systemd.sh
sudo /var/socks/deploy/systemd/install-systemd.sh
```

**方式 C：Docker Compose**

```bash
docker compose up -d --build
```

### Quick start (local dev)

Prereqs:
- Python 3.11+
- Node.js 20+

Start API:

```bash
cd control-plane/api
python -m venv .venv
. .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Start Web UI:

```bash
cd web-ui
npm install
npm run dev
```

Run a demo node agent:

```bash
cd node-agent
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m node_agent --server http://localhost:8080 --bootstrap-token demo-bootstrap --node-name demo-node --region ap-southeast-1
```

### Notes

- MVP security uses **bootstrap token -> node token**. mTLS is planned; see `deploy/pki/` placeholders.
- Data plane (transparent-to-socks) is scaffolded under `deploy/dataplane/`.

