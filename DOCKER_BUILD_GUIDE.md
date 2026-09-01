# Docker 构建网络问题解决方案

## 问题描述
构建时出现 `ConnectionTimeoutError`，无法连接到 PyPI 镜像源。

---

## 解决方案

### 方案1：使用阿里云镜像（已修改）

我已经修改 Dockerfile 使用阿里云镜像源：

```dockerfile
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV UV_TRUSTED_HOST=mirrors.aliyuncs.com
ENV UV_REQUEST_TIMEOUT=120
```

**直接构建：**
```bash
docker compose down
docker builder prune -a
docker compose up -d --build
```

---

### 方案2：离线预下载（推荐，彻底解决网络问题）

#### 步骤1：在宿主机预下载依赖

```bash
# 确保已安装 uv
pip install uv

# 运行预下载脚本
chmod +x docker-prebuild.sh
./docker-prebuild.sh
```

或者手动下载：
```bash
mkdir -p offline-packages
uv pip download \
    -r pyproject.toml \
    --python-version 3.11 \
    -d ./offline-packages \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyuncs.com
```

#### 步骤2：构建 Docker 镜像

```bash
docker compose down
docker builder prune -a
docker compose up -d --build
```

Dockerfile 会自动检测 `offline-packages` 目录，如果存在则使用离线安装。

---

### 方案3：更换其他镜像源

如果阿里云镜像也不稳定，可以尝试其他源：

| 镜像源 | URL |
|--------|-----|
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple/` |
| 豆瓣 | `https://pypi.douban.com/simple/` |
| 中科大 | `https://pypi.mirrors.ustc.edu.cn/simple/` |
| 华为云 | `https://repo.huaweicloud.com/repository/pypi/simple/` |

修改 `Dockerfile` 第10、15行即可。

---

## 验证构建

```bash
# 查看构建日志
docker compose up -d --build 2>&1 | tee build.log

# 检查服务状态
docker compose ps

# 查看后端日志
docker compose logs backend
```

---

## 常见问题

### Q1: 离线包目录在哪里？
A: 在项目根目录下 `./offline-packages`

### Q2: 离线包需要更新吗？
A: 只有当 `pyproject.toml` 中的依赖版本变更时才需要重新下载

### Q3: 两个方案哪个更稳定？
A: **方案2（离线预下载）最稳定**，完全不依赖容器内网络

---

## 推荐流程

```bash
# 1. 先尝试方案1（阿里云镜像）
docker compose up -d --build

# 2. 如果仍然超时，使用方案2（离线预下载）
./docker-prebuild.sh
docker compose up -d --build
```
