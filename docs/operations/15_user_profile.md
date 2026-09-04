# 优化 #15：用户头像 & 个人资料

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models/user.py` | 修改 | 添加 `nickname`, `email`, `avatar_url` 字段 |
| `app/api/auth.py` | 修改 | `/me` 返回个人信息，新增 `PUT /profile` 接口 |
| `frontend/src/stores/auth.ts` | 修改 | 添加个人信息状态 |
| `frontend/src/main.ts` | 修改 | 同步用户信息 |
| `frontend/src/views/Layout.vue` | 修改 | 显示昵称和头像 |

## 数据库变更

### 新增字段
```sql
ALTER TABLE users ADD COLUMN nickname VARCHAR(64) NULL;
ALTER TABLE users ADD COLUMN email VARCHAR(128) NULL;
ALTER TABLE users ADD COLUMN avatar_url TEXT NULL;
```

### 字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| `nickname` | VARCHAR(64) | 用户昵称，优先显示 |
| `email` | VARCHAR(128) | 邮箱地址 |
| `avatar_url` | TEXT | 头像URL（base64或链接） |

## 接口变更

### `GET /api/auth/me`（更新）

新增返回字段：
```json
{
  "id": 1,
  "username": "admin",
  "role": "super_admin",
  "department_id": 1,
  "department_name": "技术部",
  "nickname": "管理员",
  "email": "admin@example.com",
  "avatar_url": "data:image/png;base64,..."
}
```

### `PUT /api/auth/profile`（新增）

更新当前用户的个人信息。

**参数：**
- `nickname` (可选)：昵称
- `email` (可选)：邮箱
- `avatar_url` (可选)：头像URL

**响应：**
```json
{
  "message": "个人信息更新成功"
}
```

## 前端变更

### 显示逻辑
1. **头像**：优先显示 `avatar_url`，无则显示用户名首字母
2. **名称**：优先显示 `nickname`，无则显示 `username`

### 状态管理
auth store 新增字段：
- `nickname`：昵称
- `email`：邮箱
- `avatarUrl`：头像URL
- `displayName`：计算属性，返回昵称或用户名

## 使用场景

1. **个性化**：用户设置自己的昵称和头像
2. **识别**：在对话和管理界面更容易识别用户
3. **专业性**：企业环境使用真实姓名更专业

## 注意事项

1. **头像大小**：建议限制头像大小（如 1MB），避免数据库过大
2. **头像格式**：支持 base64 或 URL 链接
3. **昵称唯一性**：当前不强制唯一，可按需添加
