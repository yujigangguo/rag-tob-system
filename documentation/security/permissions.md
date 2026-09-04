# 权限体系

## 📋 概述

本文档介绍 RAG 知识问答系统的权限体系设计。

---

## 🎯 角色定义

### 角色列表

| 角色 | 标识 | 说明 |
|------|------|------|
| 系统管理员 | `super_admin` | 拥有所有权限 |
| 部门管理员 | `dept_admin` | 管理本部门的用户和知识库 |
| 普通用户 | `user` | 使用知识库进行问答 |

---

## 🔐 权限矩阵

### 知识库权限

| 操作 | 系统管理员 | 部门管理员 | 普通用户 |
|------|------------|------------|----------|
| 查看所有知识库 | ✅ | ❌ | ❌ |
| 查看本部门知识库 | ✅ | ✅ | ✅ |
| 查看公开知识库 | ✅ | ✅ | ✅ |
| 创建知识库 | ✅ | ✅（本部门） | ❌ |
| 编辑知识库 | ✅ | ✅（本部门） | ❌ |
| 删除知识库 | ✅ | ✅（本部门） | ❌ |

### 文档权限

| 操作 | 系统管理员 | 部门管理员 | 普通用户 |
|------|------------|------------|----------|
| 上传文档 | ✅ | ✅（本部门） | ❌ |
| 删除文档 | ✅ | ✅（本部门） | ❌ |
| 编辑文档块 | ✅ | ✅（本部门） | ❌ |
| 查看文档 | ✅ | ✅ | ✅ |
| 预览文档 | ✅ | ✅ | ✅ |

### 用户管理权限

| 操作 | 系统管理员 | 部门管理员 | 普通用户 |
|------|------------|------------|----------|
| 查看所有用户 | ✅ | ❌ | ❌ |
| 查看本部门用户 | ✅ | ✅ | ❌ |
| 创建用户 | ✅ | ✅（本部门） | ❌ |
| 编辑用户 | ✅ | ✅（本部门） | ❌ |
| 删除用户 | ✅ | ❌ | ❌ |
| 重置密码 | ✅ | ✅（本部门） | ❌ |

### 部门管理权限

| 操作 | 系统管理员 | 部门管理员 | 普通用户 |
|------|------------|------------|----------|
| 创建部门 | ✅ | ❌ | ❌ |
| 编辑部门 | ✅ | ❌ | ❌ |
| 删除部门 | ✅ | ❌ | ❌ |

### 对话权限

| 操作 | 系统管理员 | 部门管理员 | 普通用户 |
|------|------------|------------|----------|
| 创建对话 | ✅ | ✅ | ✅ |
| 查看自己的对话 | ✅ | ✅ | ✅ |
| 删除自己的对话 | ✅ | ✅ | ✅ |
| 导出对话 | ✅ | ✅ | ✅ |

---

## 🏢 部门隔离

### 设计原理

```
部门A
├── 用户A1
├── 用户A2
└── 知识库A
    ├── 文档A1
    └── 文档A2

部门B
├── 用户B1
├── 用户B2
└── 知识库B
    ├── 文档B1
    └── 文档B2
```

### 隔离规则

1. **用户只能看到本部门的知识库**
2. **部门管理员只能管理本部门的资源**
3. **系统管理员可以看到所有资源**
4. **公开知识库对所有用户可见**

---

## 🔧 权限实现

### 后端权限控制

**文件**：`app/rbac.py`

```python
ROLE_SUPER_ADMIN = "super_admin"
ROLE_DEPT_ADMIN = "dept_admin"
ROLE_USER = "user"

def is_admin(user):
    return user.role in (ROLE_SUPER_ADMIN, ROLE_DEPT_ADMIN)

def is_super_admin(user):
    return user.role == ROLE_SUPER_ADMIN

def visible_department_ids(user):
    """获取用户可见的部门 ID 列表"""
    if user.role == ROLE_SUPER_ADMIN:
        return None  # 表示所有部门
    return [user.department_id]
```

### API 权限检查

**文件**：`app/deps.py`

```python
def get_current_user(...):
    """获取当前登录用户"""
    ...

def require_admin(user: User = Depends(get_current_user)):
    """要求管理员权限"""
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="无权限")
    return user

def require_super_admin(user: User = Depends(get_current_user)):
    """要求系统管理员权限"""
    if user.role != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="无权限")
    return user
```

### 使用示例

```python
@router.post("/knowledge-bases")
def create_kb(
    req: KBCreate,
    user: User = Depends(require_admin),  # 需要管理员权限
    db: Session = Depends(get_db)
):
    # 只能创建本部门的知识库
    if user.role == ROLE_DEPT_ADMIN:
        req.department_id = user.department_id
    ...
```

---

## 🛡️ 安全措施

### 1. JWT 认证

```python
# 生成 Token
def create_access_token(user_id: int, username: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=1440)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

# 验证 Token
def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
```

### 2. 密码安全

```python
# 密码哈希（bcrypt）
def hash_password(password: str):
    return bcrypt.hashpw(
        hashlib.sha256(password.encode()).digest(),
        bcrypt.gensalt()
    ).decode()

# 密码验证
def verify_password(plain: str, hashed: str):
    return bcrypt.checkpw(
        hashlib.sha256(plain.encode()).digest(),
        hashed.encode()
    )
```

### 3. 验证码

```python
# 生成验证码
def generate_captcha():
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    captcha_id = f"cap_{int(time.time() * 1000)}"
    set_captcha(captcha_id, code, 300)  # 5 分钟有效
    return captcha_id, render_image(code)

# 验证验证码
def verify_captcha(captcha_id: str, code: str):
    stored = get_captcha(captcha_id)
    return stored and stored.upper() == code.upper()
```

---

## 📋 权限配置

### 创建管理员账号

```bash
# 通过 API 创建
curl -X POST http://localhost:8000/api/admin/users \
    -H "Authorization: Bearer <admin_token>" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "admin",
        "password": "admin123",
        "role": "super_admin",
        "department_id": 1
    }'
```

### 修改用户角色

```bash
# 通过 API 修改
curl -X PUT http://localhost:8000/api/admin/users/1 \
    -H "Authorization: Bearer <admin_token>" \
    -H "Content-Type: application/json" \
    -d '{"role": "dept_admin"}'
```

---

## ❓ 常见问题

### Q1: 用户无法访问知识库

**可能原因**：
1. 用户不在知识库所属部门
2. 知识库未设置为公开
3. 用户权限不足

**解决方法**：
1. 检查用户部门设置
2. 设置知识库为公开
3. 调整用户角色

### Q2: 部门管理员无法管理知识库

**可能原因**：
1. 知识库不属于该部门
2. 用户角色不是部门管理员

**解决方法**：
1. 检查知识库所属部门
2. 确认用户角色

### Q3: 如何让所有用户都能访问某个知识库

**解决方法**：
1. 创建知识库时勾选"全公司可见"
2. 或编辑知识库设置为公开

---

## 📚 相关文档

- [安全配置](./security-config.md)
- [用户指南](../getting-started/user-guide.md)
