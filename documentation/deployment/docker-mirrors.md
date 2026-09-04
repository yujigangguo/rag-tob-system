# Docker 镜像源优化

## 📋 问题描述

在国内使用 Docker 时，拉取镜像速度较慢，需要配置国内镜像源加速。

---

## 🔧 配置方法

### 方法1：系统级配置（推荐）

编辑 Docker 配置文件：

```bash
sudo mkdir -p /etc/docker
sudo vim /etc/docker/daemon.json
```

添加以下内容：

```json
{
  "registry-mirrors": [
    "https://docker.1panelproxy.com",
    "https://mirror.aliyuncs.com",
    "https://docker.m.daocloud.io",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://docker.mirrors.sjtug.sjtu.edu.cn",
    "https://docker.nju.edu.cn"
  ]
}
```

重启 Docker：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 方法2：项目级配置

在 `docker-compose.yml` 中指定镜像源：

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 🐍 Python 镜像源

### pyproject.toml 配置

```toml
[tool.uv]
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

### pip 配置

```bash
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
```

### Dockerfile 中配置

```dockerfile
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📦 npm 镜像源

### 项目级配置

在 `frontend/` 目录创建 `.npmrc`：

```ini
registry=https://registry.npmmirror.com
```

### 全局配置

```bash
npm config set registry https://registry.npmmirror.com
```

---

## 🔍 验证配置

### 检查 Docker 镜像源

```bash
docker info | grep -A 5 "Registry Mirrors"
```

### 检查 pip 镜像源

```bash
pip config list
```

### 检查 npm 镜像源

```bash
npm config get registry
```

### 测试拉取速度

```bash
# 测试 Docker
time docker pull hello-world

# 测试 pip
time pip install requests

# 测试 npm
time npm install lodash
```

---

## 📊 国内镜像源列表

### Docker 镜像源

| 镜像源 | 地址 |
|--------|------|
| 阿里云 | `https://mirror.aliyuncs.com` |
| 腾讯云 | `https://mirror.ccs.tencentyun.com` |
| 华为云 | `https://repo.huaweicloud.com` |
| DaoCloud | `https://docker.m.daocloud.io` |
| 1Panel | `https://docker.1panelproxy.com` |
| 网易 | `https://hub-mirror.c.163.com` |
| 百度 | `https://mirror.baidubce.com` |
| 上海交大 | `https://docker.mirrors.sjtug.sjtu.edu.cn` |
| 南京大学 | `https://docker.nju.edu.cn` |
| 中科大 | `https://docker.mirrors.ustc.edu.cn` |

### PyPI 镜像源

| 镜像源 | 地址 |
|--------|------|
| 清华大学 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple` |
| 腾讯云 | `https://mirrors.cloud.tencent.com/pypi/simple` |
| 豆瓣 | `https://pypi.douban.com/simple` |
| 中科大 | `https://pypi.mirrors.ustc.edu.cn/simple` |
| 华为云 | `https://repo.huaweicloud.com/repository/pypi/simple` |

### npm 镜像源

| 镜像源 | 地址 |
|--------|------|
| 淘宝 | `https://registry.npmmirror.com` |
| 腾讯云 | `https://mirrors.cloud.tencent.com/npm` |
| 华为云 | `https://repo.huaweicloud.com/repository/npm` |

---

## 🛠️ 镜像源检查脚本

```bash
#!/bin/bash
# check-mirrors.sh

echo "=== 检查镜像源可用性 ==="

mirrors=(
    "阿里云|https://mirror.aliyuncs.com"
    "腾讯云|https://mirror.ccs.tencentyun.com"
    "DaoCloud|https://docker.m.daocloud.io"
)

for item in "${mirrors[@]}"; do
    IFS='|' read -r name url <<< "$item"
    echo -n "检查 $name ... "
    if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        echo "✅ 可用"
    else
        echo "❌ 不可用"
    fi
done
```

---

## 💡 最佳实践

1. **优先使用阿里云和腾讯云**：稳定性最好
2. **配置多个镜像源**：一个不可用时自动切换
3. **定期检查镜像源**：确保可用性
4. **使用项目级配置**：避免影响其他项目

---

## ❓ 常见问题

### Q1: 配置后仍然很慢

```bash
# 检查配置是否生效
docker info | grep "Registry Mirrors"

# 尝试其他镜像源
sudo vim /etc/docker/daemon.json
```

### Q2: 某些镜像拉取失败

```bash
# 使用原生镜像源
docker pull docker.io/library/python:3.11-slim

# 或指定完整路径
docker pull registry.cn-hangzhou.aliyuncs.com/library/python:3.11-slim
```

### Q3: npm 安装失败

```bash
# 清除缓存
npm cache clean --force

# 使用其他镜像源
npm config set registry https://registry.npmmirror.com
```
