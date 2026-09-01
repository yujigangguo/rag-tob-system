# 多镜像源配置说明

## 配置概览

### Python (pip/uv) 三镜像源

| 优先级 | 镜像源 | URL |
|--------|--------|-----|
| 1️⃣ | 阿里云 | `https://mirrors.aliyun.com/pypi/simple/` |
| 2️⃣ | 腾讯云 | `https://mirrors.cloud.tencent.com/pypi/simple/` |
| 3️⃣ | 清华大学 | `https://pypi.tuna.tsinghua.edu.cn/simple/` |

### npm 镜像源

| 镜像源 | URL |
|--------|-----|
| 淘宝 npm | `https://registry.npmmirror.com` |

---

## 工作原理

### 1. 主源优先
默认使用阿里云镜像（速度最快）

### 2. 自动切换
如果主源超时或失败，自动尝试腾讯云和清华镜像

### 3. 重试机制
- npm: 最多重试 5 次，超时 60-120 秒
- uv: 超时时间 120 秒

---

## 配置文件位置

### 后端 (Python)
- **Dockerfile**: 三镜像源配置
- **/etc/pip.conf**: pip 镜像源配置
- **环境变量**: uv 镜像源配置

### 前端 (Node.js)
- **Dockerfile**: npm 镜像源配置
- **frontend/.npmrc**: 本地开发镜像源

---

## 验证配置

### 检查镜像源可用性

```bash
chmod +x check-mirrors.sh
./check-mirrors.sh
```

### 构建时查看日志

```bash
docker compose up -d --build 2>&1 | tee build.log
```

---

## 故障排除

### 问题: 所有镜像源都超时

**解决方案**:
```bash
# 使用离线预下载方案
./docker-prebuild.sh
docker compose up -d --build
```

### 问题: 特定包下载失败

**解决方案**:
```bash
# 手动下载该包
uv pip download package-name -d ./offline-packages
```

---

## 推荐配置

### 国内服务器（默认）
```dockerfile
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV UV_EXTRA_INDEX_URL="https://mirrors.cloud.tencent.com/pypi/simple/|https://pypi.tuna.tsinghua.edu.cn/simple/"
```

### 海外服务器
```dockerfile
ENV UV_INDEX_URL=https://pypi.org/simple/
ENV UV_EXTRA_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
```

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `Dockerfile` | 后端三镜像源配置 |
| `frontend/Dockerfile` | 前端 npm 镜像源配置 |
| `check-mirrors.sh` | 镜像源健康检查脚本 |
| `MULTI_MIRROR_CONFIG.md` | 本文档 |
