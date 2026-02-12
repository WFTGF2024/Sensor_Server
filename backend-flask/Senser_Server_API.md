# Sensor Server API 文档

## 项目信息

- **框架**: Flask 3.0.0
- **数据库**: MySQL (pymysql)
- **缓存**: Redis
- **加密**: cryptography

---

## 认证机制

所有需要认证的API使用 Flask Session 进行身份验证。请求时需携带 session cookie。

**允许的跨域源**:
- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://10.8.0.24:5173`

---

## 标准响应格式

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "status": 400
  }
}
```

### 错误状态码
| 状态码 | 错误代码 | 说明 |
|--------|---------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 401 | AUTHENTICATION_ERROR | 未认证 |
| 403 | AUTHORIZATION_ERROR | 未授权 |
| 404 | NOT_FOUND | 资源不存在 |
| 405 | METHOD_NOT_ALLOWED | 方法不允许 |
| 409 | CONFLICT | 资源冲突 |
| 429 | RATE_LIMIT_EXCEEDED | 请求频率超限 |
| 500 | INTERNAL_SERVER_ERROR | 服务器内部错误 |

---

## API 端点

### 1. 认证模块 (`/api/auth`)

#### 1.1 用户注册

**请求**: `POST /api/auth/register`

**请求体**:
```json
{
  "username": "string (必填)",
  "password": "string (必填)",
  "email": "string (可选)",
  "phone": "string (可选)",
  "qq": "string (可选)",
  "wechat": "string (可选)"
}
```

**响应** (201):
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": 1,
  "username": "testuser"
}
```

---

#### 1.2 用户登录

**请求**: `POST /api/auth/login`

**请求体**:
```json
{
  "username": "string (必填)",
  "password": "string (必填)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "13800138000",
    "qq": "123456",
    "wechat": "wxid_xxxxx",
    "membership": {
      "level_code": "free",
      "level_name": "普通用户",
      "storage_used": 0,
      "storage_limit": 1073741824,
      "storage_used_formatted": "0 B",
      "storage_limit_formatted": "1 GB",
      "max_file_size": 104857600,
      "max_file_size_formatted": "100 MB",
      "max_file_count": 100
    }
  }
}
```

---

#### 1.3 用户登出

**请求**: `POST /api/auth/logout`

**响应** (200):
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

#### 1.4 更新用户资料

**请求**: `PUT /api/auth/profile`

**请求体**:
```json
{
  "email": "string (可选)",
  "phone": "string (可选)",
  "qq": "string (可选)",
  "wechat": "string (可选)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "newemail@example.com",
    "phone": "13900139000",
    "qq": "654321",
    "wechat": "wxid_yyyyy",
    "membership": {
      "level_code": "free",
      "level_name": "普通用户",
      "storage_used": 0,
      "storage_limit": 1073741824,
      "storage_used_formatted": "0 B",
      "storage_limit_formatted": "1 GB",
      "max_file_size": 104857600,
      "max_file_size_formatted": "100 MB"
    }
  }
}
```

---

#### 1.5 修改密码

**请求**: `PUT /api/auth/password`

**请求体**:
```json
{
  "current_password": "string (必填, 或使用 old_password)",
  "new_password": "string (必填)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

#### 1.6 删除账户

**请求**: `DELETE /api/auth/account`

**请求体**:
```json
{
  "password": "string (必填)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "Account deleted successfully"
}
```

---

#### 1.7 获取用户资料

**请求**: `GET /api/auth/user`

**响应** (200):
```json
{
  "success": true,
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "13800138000",
    "qq": "123456",
    "wechat": "wxid_xxxxx",
    "membership": {
      "level_code": "free",
      "level_name": "普通用户",
      "storage_used": 0,
      "storage_limit": 1073741824,
      "storage_used_formatted": "0 B",
      "storage_limit_formatted": "1 GB",
      "max_file_size": 104857600,
      "max_file_size_formatted": "100 MB"
    }
  }
}
```

---

### 2. 文件管理模块 (`/api/download`)

#### 2.1 上传文件

**请求**: `POST /api/download/upload`

**请求**: `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 文件 |
| file_permission | string | 否 | 文件权限 (private/public)，默认 private |
| description | string | 否 | 文件描述 |

**响应** (201):
```json
{
  "message": "Upload successful",
  "file_id": 1,
  "file_name": "document.pdf",
  "file_permission": "private",
  "description": "重要文档",
  "file_hash": "a1b2c3d4e5f6...",
  "file_size": 1048576,
  "file_size_formatted": "1 MB",
  "uploaded_at": "2024-01-15T10:30:00"
}
```

---

#### 2.2 获取用户文件列表

**请求**: `GET /api/download/files`

**响应** (200):
```json
[
  {
    "file_id": 1,
    "file_name": "document.pdf",
    "file_permission": "private",
    "description": "重要文档",
    "file_hash": "a1b2c3d4e5f6...",
    "file_size": 1048576,
    "file_size_formatted": "1 MB",
    "uploaded_at": "2024-01-15T10:30:00"
  }
]
```

---

#### 2.3 获取公开文件列表

**请求**: `GET /api/download/public`

**响应** (200):
```json
[
  {
    "file_id": 2,
    "file_name": "public_doc.pdf",
    "file_permission": "public",
    "description": "公开文档",
    "file_hash": "f6e5d4c3b2a1...",
    "file_size": 524288,
    "file_size_formatted": "512 KB",
    "uploaded_at": "2024-01-15T11:00:00"
  }
]
```

---

#### 2.4 下载文件

**请求**: `GET /api/download/download/{file_id}`

**路径参数**:
- `file_id` (integer): 文件ID

**响应**: 文件下载流

---

#### 2.5 更新文件元数据

**请求**: `PUT /api/download/file/{file_id}`

**路径参数**:
- `file_id` (integer): 文件ID

**请求体**:
```json
{
  "file_name": "string (可选)",
  "file_permission": "string (可选, private/public)",
  "description": "string (可选)"
}
```

**响应** (200):
```json
{
  "message": "Update successful"
}
```

---

#### 2.6 删除文件

**请求**: `DELETE /api/download/file/{file_id}`

**路径参数**:
- `file_id` (integer): 文件ID

**响应** (200):
```json
{
  "message": "Delete successful"
}
```

---

### 3. 会员管理模块 (`/api/membership`)

#### 3.1 获取会员信息

**请求**: `GET /api/membership/info`

**响应** (200):
```json
{
  "success": true,
  "membership": {
    "level_code": "silver",
    "level_name": "银牌会员",
    "storage_used": 52428800,
    "storage_limit": 5368709120,
    "storage_used_formatted": "50 MB",
    "storage_limit_formatted": "5 GB",
    "max_file_size": 209715200,
    "max_file_size_formatted": "200 MB",
    "max_file_count": 500,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "end_date_formatted": "2024年12月31日"
  }
}
```

---

#### 3.2 获取会员等级列表

**请求**: `GET /api/membership/levels`

**响应** (200):
```json
{
  "success": true,
  "levels": [
    {
      "level_id": 1,
      "level_code": "free",
      "level_name": "普通用户",
      "storage_limit": 1073741824,
      "max_file_size": 104857600,
      "max_file_count": 100,
      "price_per_month": 0
    },
    {
      "level_id": 2,
      "level_code": "silver",
      "level_name": "银牌会员",
      "storage_limit": 5368709120,
      "max_file_size": 209715200,
      "max_file_count": 500,
      "price_per_month": 9.9
    },
    {
      "level_id": 3,
      "level_code": "gold",
      "level_name": "金牌会员",
      "storage_limit": 10737418240,
      "max_file_size": 524288000,
      "max_file_count": 1000,
      "price_per_month": 19.9
    },
    {
      "level_id": 4,
      "level_code": "diamond",
      "level_name": "钻石会员",
      "storage_limit": 53687091200,
      "max_file_size": 1073741824,
      "max_file_count": 5000,
      "price_per_month": 49.9
    }
  ]
}
```

---

#### 3.3 升级会员

**请求**: `POST /api/membership/upgrade`

**请求体**:
```json
{
  "level_id": 2,
  "duration_days": 30,
  "payment_method": "string (可选)",
  "transaction_id": "string (可选)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "会员升级成功，当前等级：银牌会员",
  "membership": {
    "level_code": "silver",
    "level_name": "银牌会员",
    "storage_used": 52428800,
    "storage_limit": 5368709120,
    "storage_used_formatted": "50 MB",
    "storage_limit_formatted": "5 GB",
    "max_file_size": 209715200,
    "max_file_size_formatted": "200 MB",
    "start_date": "2024-01-15",
    "end_date": "2024-02-14"
  }
}
```

---

#### 3.4 续费会员

**请求**: `POST /api/membership/renew`

**请求体**:
```json
{
  "duration_days": 30,
  "payment_method": "string (可选)",
  "transaction_id": "string (可选)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "会员续费成功，有效期至：2024年02月14日",
  "membership": {
    "level_code": "silver",
    "level_name": "银牌会员",
    "storage_used": 52428800,
    "storage_limit": 5368709120,
    "storage_used_formatted": "50 MB",
    "storage_limit_formatted": "5 GB",
    "max_file_size": 209715200,
    "max_file_size_formatted": "200 MB",
    "start_date": "2024-01-15",
    "end_date": "2024-02-14",
    "end_date_formatted": "2024年02月14日"
  }
}
```

---

#### 3.5 获取存储统计

**请求**: `GET /api/membership/storage-stats`

**响应** (200):
```json
{
  "success": true,
  "stats": {
    "total_files": 15,
    "total_size": 52428800,
    "total_size_formatted": "50 MB",
    "storage_used": 52428800,
    "storage_limit": 5368709120,
    "usage_percentage": 0.98,
    "files_by_type": {
      "pdf": 5,
      "jpg": 8,
      "png": 2
    },
    "largest_file": {
      "file_id": 10,
      "file_name": "large_file.pdf",
      "file_size": 10485760,
      "file_size_formatted": "10 MB"
    }
  }
}
```

---

#### 3.6 获取会员权益

**请求**: `GET /api/membership/benefits`

**响应** (200):
```json
{
  "success": true,
  "level_name": "银牌会员",
  "level_code": "silver",
  "benefits": [
    {
      "benefit_id": 1,
      "description": "5GB 存储空间"
    },
    {
      "benefit_id": 2,
      "description": "单文件最大 200MB"
    },
    {
      "benefit_id": 3,
      "description": "最多 500 个文件"
    },
    {
      "benefit_id": 4,
      "description": "文件分享功能"
    }
  ]
}
```

---

### 4. 监控管理模块 (`/api/monitor`)

#### 4.1 系统健康检查

**请求**: `GET /api/monitor/health`

**响应** (200):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "components": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

---

#### 4.2 获取请求统计

**请求**: `GET /api/monitor/stats/requests`

**查询参数**:
- `time_window` (integer, 可选): 时间窗口（秒），默认 3600

**响应** (200):
```json
{
  "success": true,
  "data": {
    "total_requests": 1250,
    "successful_requests": 1200,
    "failed_requests": 50,
    "avg_duration": 0.125,
    "p95_duration": 0.25,
    "p99_duration": 0.5,
    "requests_by_endpoint": {
      "/api/auth/login": 300,
      "/api/download/files": 400,
      "/api/membership/info": 150
    },
    "requests_by_method": {
      "GET": 800,
      "POST": 400,
      "PUT": 50
    }
  }
}
```

---

#### 4.3 获取缓存统计

**请求**: `GET /api/monitor/stats/cache`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "application_cache": {
      "hits": 850,
      "misses": 150,
      "hit_rate": 85.0,
      "size": 1000
    },
    "redis": {
      "enabled": true,
      "hits": 5000,
      "misses": 500,
      "hit_rate": 90.9,
      "keys": 2500,
      "memory_used": 52428800,
      "memory_used_formatted": "50 MB"
    },
    "monitoring": {
      "hits": 200,
      "misses": 50,
      "hit_rate": 80.0
    }
  }
}
```

---

#### 4.4 获取数据库统计

**请求**: `GET /api/monitor/stats/database`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "total_queries": 5000,
    "avg_query_time": 0.015,
    "slow_queries": 10,
    "connections": {
      "active": 5,
      "idle": 3
    },
    "tables": {
      "users": 1000,
      "files": 5000,
      "memberships": 1000
    }
  }
}
```

---

#### 4.5 获取系统统计

**请求**: `GET /api/monitor/stats/system`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-01-15T10:30:00",
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_usage_percent": 60.3,
    "process_memory_mb": 256.5,
    "active_threads": 8,
    "uptime_seconds": 86400
  }
}
```

---

#### 4.6 获取所有统计

**请求**: `GET /api/monitor/stats/all`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "requests": {
      "total_requests": 1250,
      "successful_requests": 1200,
      "failed_requests": 50,
      "avg_duration": 0.125
    },
    "database": {
      "total_queries": 5000,
      "avg_query_time": 0.015
    },
    "system": {
      "cpu_percent": 25.5,
      "memory_percent": 45.2,
      "disk_usage_percent": 60.3
    },
    "cache": {
      "application": {
        "hits": 850,
        "misses": 150,
        "hit_rate": 85.0
      },
      "redis": {
        "enabled": true,
        "hits": 5000,
        "misses": 500,
        "hit_rate": 90.9
      }
    }
  }
}
```

---

#### 4.7 获取监控配置

**请求**: `GET /api/monitor/config`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "monitoring": {
      "enabled": true,
      "sample_rate": 0.1,
      "metrics_retention": 86400
    },
    "cache": {
      "redis_enabled": true,
      "redis_host": "localhost",
      "redis_port": 6379,
      "cache_ttl": 3600
    },
    "logging": {
      "log_level": "INFO",
      "log_dir": "./log"
    }
  }
}
```

---

#### 4.8 清除缓存

**请求**: `POST /api/monitor/cache/clear`

**响应** (200):
```json
{
  "success": true,
  "message": "Cache cleared successfully",
  "data": {
    "application_cache_cleared": 100,
    "redis_cache_cleared": 500,
    "total_cleared": 600
  }
}
```

---

#### 4.9 获取系统告警

**请求**: `GET /api/monitor/alerts`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "level": "warning",
        "type": "high_cpu_usage",
        "message": "CPU usage is high: 85%",
        "value": 85
      },
      {
        "level": "info",
        "type": "low_cache_hit_rate",
        "message": "Cache hit rate is low: 45%",
        "value": 45
      }
    ],
    "count": 2
  }
}
```

---

#### 4.10 获取 Prometheus 指标

**请求**: `GET /api/monitor/metrics`

**响应** (200, text/plain):
```
http_requests_total 1250
http_request_duration_seconds_avg 0.125
http_request_duration_seconds_p95 0.25
http_request_duration_seconds_p99 0.5
cache_hits_total 5850
cache_misses_total 650
cache_hit_rate 90.0
system_cpu_percent 25.5
system_memory_percent 45.2
system_disk_usage_percent 60.3
system_process_memory_mb 256.5
system_active_threads 8
```

---

### 5. 用户管理

#### 5.1 获取所有用户列表

**请求**: `GET /users`

**响应** (200):
```json
[
  {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "13800138000",
    "qq": "123456",
    "wechat": "wxid_xxxxx",
    "membership": {
      "level_code": "free",
      "level_name": "普通用户",
      "storage_limit": 1073741824,
      "max_file_size": 104857600,
      "max_file_count": 100
    }
  }
]
```

---

### 6. Web 页面路由

| 路由 | 方法 | 说明 | 需要认证 |
|------|------|------|---------|
| `/` | GET | 首页 | 否 |
| `/test` | GET | 测试页面 | 否 |
| `/login` | GET/POST | 登录页面 | 否 |
| `/register` | GET/POST | 注册页面 | 否 |
| `/logout` | GET | 登出 | 否 |
| `/dashboard` | GET | 用户仪表盘 | 是 |
| `/files` | GET | 文件管理页面 | 是 |
| `/membership` | GET | 会员中心页面 | 是 |
| `/profile` | GET | 个人资料页面 | 是 |

---

## 附录

### 文件权限类型

| 权限值 | 说明 |
|--------|------|
| private | 私有文件，仅上传者可访问 |
| public | 公开文件，所有用户可查看和下载 |

### 会员等级

| 等级代码 | 等级名称 | 存储空间 | 单文件大小 | 文件数量 |
|---------|---------|---------|-----------|---------|
| free | 普通用户 | 1 GB | 100 MB | 100 |
| silver | 银牌会员 | 5 GB | 200 MB | 500 |
| gold | 金牌会员 | 10 GB | 500 MB | 1000 |
| diamond | 钻石会员 | 50 GB | 1 GB | 5000 |

### 常见错误示例

#### 400 参数验证失败
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required fields: username, password",
    "status": 400,
    "details": {
      "missing_fields": ["username", "password"],
      "required_fields": ["username", "password"]
    }
  }
}
```

#### 401 未认证
```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Authentication required",
    "status": 401
  }
}
```

#### 404 资源不存在
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "status": 404
  }
}
```

#### 409 资源冲突
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "Username already exists",
    "status": 409
  }
}
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2024-01-15 | 初始版本 |
