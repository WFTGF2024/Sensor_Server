# Sensor Flask - 文件存储和管理系统

一个基于 Vue3 + Flask 的前后端分离文件存储和管理系统，提供用户认证、文件管理、会员分级、Redis缓存和性能监控等功能。

## 项目结构

```
Sensor_Flask/
├── backend-flask/              # Flask 后端 API
│   ├── app.py                 # 应用入口
│   ├── config.py              # 配置管理
│   ├── controllers/           # 控制器层
│   ├── services/              # 业务逻辑层
│   ├── repositories/          # 数据库接口层
│   ├── models/                # 数据模型层
│   ├── utils/                 # 工具类
│   ├── database/              # 数据库迁移
│   ├── tests/                 # 测试
│   └── README.md              # 后端文档
│
├── frontend-vue/              # Vue3 前端应用
│   ├── src/
│   │   ├── api/               # API 接口层
│   │   ├── components/        # 公共组件
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # 状态管理（Pinia）
│   │   ├── utils/             # 工具函数
│   │   ├── views/             # 页面组件
│   │   ├── App.vue            # 根组件
│   │   └── main.js            # 入口文件
│   ├── package.json
│   ├── vite.config.js
│   └── README.md              # 前端文档
│
├── VUE3_MIGRATION_GUIDE.md    # Vue3 迁移指南
└── README.md                  # 项目说明（本文件）
```

## 快速开始

### 前提条件

- Python 3.9+
- Node.js 16+
- MySQL 5.7+
- Redis 6.0+

### 1. 后端设置

```bash
# 进入后端目录
cd backend-flask

# 创建并激活 Conda 环境
conda env create -f environment.yml
conda activate sensor_flask

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库、Redis等配置

# 启动后端服务
python app.py
```

后端服务将运行在 `http://localhost:5000`

### 2. 前端设置

```bash
# 进入前端目录
cd frontend-vue

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将运行在 `http://localhost:5173`

### 3. 访问应用

打开浏览器访问 `http://localhost:5173` 即可使用应用。

## 功能特性

### 用户系统
- ✅ 用户注册和登录
- ✅ 个人信息管理
- ✅ 密码修改
- ✅ 账户删除

### 文件管理
- ✅ 文件上传（支持进度显示）
- ✅ 文件下载
- ✅ 文件列表查看
- ✅ 文件信息编辑
- ✅ 文件删除
- ✅ 权限管理（公开/私有）

### 会员系统
- ✅ 四级会员（普通、白银、黄金、钻石）
- ✅ 会员升级
- ✅ 存储容量管理
- ✅ 会员特权展示

### 性能优化
- ✅ Redis 缓存
- ✅ 请求性能监控
- ✅ 系统资源监控
- ✅ 缓存命中率统计

## 技术栈

### 后端
- **Python 3.9+**
- **Flask** - Web 框架
- **PyMySQL** - MySQL 数据库驱动
- **Redis** - 缓存和会话存储
- **Flask-CORS** - 跨域支持

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **Vue Router** - 路由管理
- **Pinia** - 状态管理
- **Axios** - HTTP 客户端
- **Element Plus** - UI 组件库
- **Vite** - 构建工具

### 数据库
- **MySQL** - 主数据库
- **Redis** - 缓存数据库

## 部署

### 开发环境

后端和前端分别运行，使用 Vite 代理转发 API 请求。

### 生产环境

1. **构建前端**：
   ```bash
   cd frontend-vue
   npm run build
   ```

2. **部署前端**：
   将 `frontend-vue/dist` 目录部署到 Web 服务器（如 Nginx）

3. **部署后端**：
   使用 Gunicorn/uWSGI 部署 Flask 应用

4. **Nginx 配置示例**：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       # 前端静态文件
       root /path/to/frontend-vue/dist;
       index index.html;

       # 前端路由
       location / {
           try_files $uri $uri/ /index.html;
       }

       # API 代理
       location /api/ {
           proxy_pass http://localhost:5000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

## 文档

- **[后端文档](backend-flask/README.md)** - Flask 后端 API 文档
- **[前端文档](frontend-vue/README.md)** - Vue3 前端文档
- **[迁移指南](VUE3_MIGRATION_GUIDE.md)** - Vue3 迁移指南

## 会员等级

| 等级 | 代码 | 存储容量 | 单文件大小 | 文件数量 | 特权 |
|------|------|----------|------------|----------|------|
| 普通用户 | free | 1GB | 50MB | 100个 | 基础文件存储 |
| 白银会员 | silver | 5GB | 100MB | 500个 | 文件分享 |
| 黄金会员 | gold | 10GB | 200MB | 1000个 | 公开链接、每日下载100次 |
| 钻石会员 | diamond | 50GB | 1GB | 10000个 | 每日下载1000次、每日上传500次 |

## 测试

### 后端测试
```bash
cd backend-flask
python -m pytest tests/
```

### 前端测试
```bash
cd frontend-vue
npm run lint
```

## 常见问题

### 1. CORS 错误
确保后端已配置 CORS 支持，检查 `backend-flask/.env` 中的 `CORS_ORIGINS` 配置。

### 2. 数据库连接失败
检查 `backend-flask/.env` 中的数据库配置是否正确。

### 3. Redis 连接失败
确保 Redis 服务正在运行，或在 `.env` 中设置 `REDIS_ENABLED=false`。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目仅供学习和研究使用。
