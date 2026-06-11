# 从 GitHub 干净开局部署（简版）

> **完整手册（开局 + 升级 + Git 同步）请阅：[SETUP_AND_UPGRADE.md](SETUP_AND_UPGRADE.md)**

适用于恢复 VM 后从零验证控制平台 + 转发节点。

## 快速步骤

### 1. 控制平台

```bash
sudo git clone https://github.com/278946647/gfc-platform.git /opt/gfc
cd /opt/gfc && sudo git checkout -B main origin/main
sudo bash deploy/control/install-docker.sh
```

验证：`curl -fsS http://127.0.0.1:8080/healthz`  
Web：`http://<IP>:5173`（`admin`，密码见 **系统设置 → 平台安全**）

### 2. 转发节点

```bash
sudo git clone https://github.com/278946647/gfc-platform.git /var/socks
cd /var/socks && sudo git checkout -B main origin/main
sudo bash deploy/node/install.sh
```

验证：`sudo bash deploy/node/verify-node.sh`（需见 `fwmark 0x1 lookup 100`）

### 3. Web UI 业务

代理配置 → 客户线路 → 回程路由 → 下联 PC 测试

### 4. 在线升级

```bash
# 控制面
cd /opt/gfc && sudo bash deploy/control/upgrade-control.sh

# 转发节点
cd /var/socks && sudo git checkout -B main origin/main
sudo python3 deploy/node/repair_forward_node.py
```

## 常见问题速查

| 现象 | 处理 |
|------|------|
| detached HEAD / `git pull` 失败 | `git fetch && git checkout -B main origin/main` |
| `ContainerConfig` 错误 | 勿 `--force-recreate`；见 [SETUP_AND_UPGRADE.md §6](SETUP_AND_UPGRADE.md) |
| 平台安全 UI 未更新 | `sudo bash deploy/control/redeploy-web.sh` |

详见 [SETUP_AND_UPGRADE.md §9](SETUP_AND_UPGRADE.md)。
