# 从 GitHub 干净开局部署（Ubuntu 22.04）

适用于恢复 VM 后从零验证控制平台 + 转发节点。

## 0. 前置

- 控制平台 VM：Ubuntu 22.04，能访问 GitHub 与外网
- 转发节点 VM：Ubuntu 22.04+，能访问控制平台 API 端口
- GitHub 仓库已包含本版本修复（见文末「本版修复清单」）

## 1. 开发机：提交并推送到 GitHub

在 Windows / Cursor 项目目录：

```powershell
cd C:\Users\哈哈\Developer\global-forwarding-control-plane

git status
git add .
git commit -m "fix: production docker, tproxy policy, control plane install"
git push origin main

# 打版本标签（服务器建议 checkout 此 tag）
git tag -a v0.2.1 -m "Clean deploy: docker install, tproxy fix, curl probe"
git push origin v0.2.1
```

## 2. 控制平台（干净 VM）

```bash
sudo apt update
sudo apt install -y git

# 公开仓库
sudo git clone https://github.com/278946647/gfc-platform.git /opt/gfc
cd /opt/gfc
sudo git checkout v0.2.1

# 一键安装 Docker + 启动（或已 clone 后执行）
sudo bash deploy/control/install-docker.sh
```

**私有仓库**：用 PAT 或 SSH clone，见 README。

### 配置生产密钥

```bash
cd /opt/gfc
sudo cp .env.example .env
sudo nano .env
```

修改：

- `GFC_BOOTSTRAP_TOKENS` — 转发节点激活用，记住此值
- `GFC_ADMIN_DEFAULT_PASSWORD` — Web 登录密码
- `GFC_AUTH_SECRET` — 随机长字符串（`openssl rand -hex 32`）

应用：

```bash
cd /opt/gfc
sudo docker-compose up -d --build
# 或: sudo docker compose up -d --build
```

### 验证控制平台

```bash
curl -fsS http://127.0.0.1:8080/healthz
docker-compose exec api printenv GFC_BOOTSTRAP_TOKENS
docker-compose exec api curl -fsS https://api.ipify.org
```

浏览器：`http://<控制面IP>:5173`，用户 `admin`，密码为 `.env` 中配置。

## 3. 转发节点（干净 VM）

```bash
sudo apt update
sudo apt install -y git

sudo git clone https://github.com/278946647/gfc-platform.git /var/socks
cd /var/socks
sudo git checkout v0.2.1
```

### 方式 A：交互安装（推荐）

```bash
cd /var/socks
sudo bash deploy/node/install.sh
```

按提示填写：

| 项 | 示例 |
|----|------|
| 控制平台 IP | `103.78.41.16` |
| API 端口 | `8080` |
| Bootstrap Token | 与 `.env` 中 `GFC_BOOTSTRAP_TOKENS` **完全一致** |
| NODE_NAME | `hka-node-one` |
| TPROXY 网卡 | VyOS/客户流量入向网卡，如 `ens224` |

### 方式 B：配置文件

```bash
cp deploy/node/install.env.example deploy/node/install.env
sudo nano deploy/node/install.env
sudo bash deploy/node/install.sh --config deploy/node/install.env --yes
```

### 验证转发节点

```bash
sudo bash deploy/node/verify-node.sh
ip rule list | grep fwmark
sudo gfc-logs agent -n 30
```

**必须看到：** `fwmark 0x1 lookup 100`

## 4. Web UI 业务配置

1. 登录控制平台
2. **代理配置**：添加 SOCKS，点探测应显示 `exit_ip=...`（非 curl skipped）
3. **客户线路**：选节点 + SOCKS + 源 IP 段（如 `10.10.10.0/30`）
4. **回程路由**（以太网模式）：前缀 `10.10.10.0/30`，下一跳 VyOS IP，设备 `ens224`

## 5. 下联 PC 测试

- PC 源 IP 落在线路 `source_cidrs` 内
- 流量从配置的 TPROXY 网卡进入转发节点
- PC 上网 / DNS 正常

## 6. 常见问题

| 现象 | 处理 |
|------|------|
| `docker-compose-plugin` 找不到 | 用 `apt install docker-compose`，命令写 `docker-compose` |
| `export GFC_*` 不生效 | 改 `/opt/gfc/.env` 后 `docker-compose up -d` |
| Bootstrap 403 | 控制面 token 与节点 `BOOTSTRAP_TOKEN` 不一致 |
| DNS 不通但 SOCKS curl 正常 | `ip rule list` 无 fwmark → `force-reapply.sh` 或重启 agent |
| 代理探测 curl skipped | 重建 API 镜像：`docker-compose up -d --build api` |

## 本版修复清单（v0.2.1）

- Web UI Docker 生产构建（nginx）
- API 镜像内置 curl（SOCKS 探测）
- `docker-compose` 读取 `.env` 配置密钥
- PKI 持久化目录 `/data/pki`
- TPROXY 策略路由 `fwmark 0x1` 修复与开机补全
- 控制面 `deploy/control/install-docker.sh` 一键脚本
- `.gitignore` 防止密钥入库
