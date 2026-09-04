# 安全配置

## 📋 概述

本文档介绍 RAG 系统的安全相关配置。

---

## 🔐 认证配置

### JWT 配置

```python
# config/settings.py
secret_key: str = "change-me-in-production-please"  # 必须修改！
access_token_expire_minutes: int = 1440  # Token 有效期 24 小时
```

**生产环境必须修改：**
```bash
# .env
SECRET_KEY=使用 openssl rand -hex 32 生成
```

### 密码安全

```python
# 使用 bcrypt + SHA256 双重哈希
password_hash = bcrypt.hashpw(
    hashlib.sha256(password.encode()).digest(),
    bcrypt.gensalt()
)
```

---

## 🛡️ CORS 配置

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**生产环境建议：**
```python
allow_origins=[
    "https://your-domain.com",
    "https://www.your-domain.com",
]
```

---

## 🔒 验证码配置

```python
# 生成验证码
code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
captcha_id = f"cap_{int(time.time() * 1000)}"
set_captcha(captcha_id, code, 300)  # 5 分钟有效
```

---

## 🚦 限流配置

### Nginx 限流

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
```

### 应用层限流

```python
# 可选：使用 slowapi
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

---

## 🔐 HTTPS 配置

### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### Nginx 配置

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... 其他配置
}
```

---

## 🧱 防火墙配置

```bash
# 安装 UFW
sudo apt install ufw

# 配置规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用
sudo ufw enable
```

---

## 📋 安全检查清单

- [ ] 修改默认密码
- [ ] 修改 SECRET_KEY
- [ ] 配置 CORS 域名白名单
- [ ] 启用 HTTPS
- [ ] 配置防火墙
- [ ] 配置请求限流
- [ ] 修改数据库默认密码
- [ ] 修改 Redis 密码
- [ ] 配置日志审计

---

## 📚 相关文档

- [权限体系](./permissions.md)
- [部署方案](../deployment/README.md)
