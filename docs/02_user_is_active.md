# 优化 #2：用户账号禁用功能

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models/user.py` | 修改 | 添加 `is_active` 字段 |
| `app/schemas/admin.py` | 修改 | UserOut 添加 `is_active` 字段 |
| `app/services/auth_service.py` | 修改 | 登录时检查 `is_active` |
| `app/services/admin_service.py` | 修改 | 添加 `toggle_user_active()` 函数 |
| `app/api/admin.py` | 修改 | 添加 `PUT /users/{id}/status` 接口 |
| `frontend/src/views/admin/Users.vue` | 修改 | 添加状态列和禁用/启用按钮 |

## 数据库变更

### 新增字段
```sql
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
```

### 字段说明
| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `is_active` | BOOLEAN | TRUE | 账号是否启用 |

## 新增接口

### `PUT /api/admin/users/{user_id}/status`

禁用或启用用户。

**参数：**
- `user_id` (路径参数)：用户ID
- `is_active` (查询参数)：true=启用, false=禁用

**权限：** 超级管理员

**响应示例：**
```json
{
  "id": 1,
  "username": "testuser",
  "role": "employee",
  "department_id": 1,
  "department_name": "技术部",
  "is_active": false,
  "created_at": "2024-01-01T00:00:00"
}
```

## 业务逻辑

1. **登录检查**：用户登录时检查 `is_active`，如果为 `false` 返回 403 错误
2. **自我保护**：超级管理员不能禁用自己
3. **数据保留**：禁用用户不会删除数据，只是阻止登录

## 前端变更

1. **状态列**：用户列表新增"状态"列，显示"正常"（绿色）或"已禁用"（红色）
2. **操作按钮**：新增"禁用/启用"按钮，根据当前状态动态显示
3. **二次确认**：禁用/启用操作需要二次确认

## 使用场景

1. **临时禁用**：员工离职但保留数据
2. **违规处理**：用户违规后临时封禁
3. **权限回收**：撤销用户访问权限

## 注意事项

1. **已登录用户**：禁用后，已登录的用户 token 仍然有效，直到过期
2. **数据安全**：禁用不会删除用户数据，只是阻止登录
3. **恢复启用**：可以随时启用用户，无需重新注册
