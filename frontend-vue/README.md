# Sensor Flask - Vue3 前端项目

这是 Sensor Flask 项目的 Vue3 前端实现，采用前后端分离架构。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vue Router** - 官方路由管理器
- **Pinia** - 状态管理库
- **Axios** - HTTP 客户端
- **Element Plus** - Vue 3 组件库
- **Vite** - 下一代前端构建工具

## 项目结构

```
frontend-vue/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口
│   │   ├── auth.js       # 认证相关API
│   │   ├── file.js       # 文件相关API
│   │   ├── membership.js # 会员相关API
│   │   └── index.js      # API导出
│   ├── assets/           # 资源文件
│   │   └── css/          # 样式文件
│   ├── components/       # 公共组件
│   │   ├── Navbar.vue   # 导航栏
│   │   ├── Footer.vue   # 页脚
│   │   ├── StatCard.vue # 统计卡片
│   │   └── StorageProgress.vue # 存储进度条
│   ├── router/           # 路由配置
│   │   └── index.js     # 路由定义
│   ├── stores/           # 状态管理
│   │   ├── user.js      # 用户状态
│   │   ├── file.js      # 文件状态
│   │   └── membership.js # 会员状态
│   ├── utils/            # 工具函数
│   │   └── request.js   # Axios封装
│   ├── views/            # 页面组件
│   │   ├── Home.vue     # 首页
│   │   ├── Login.vue    # 登录页
│   │   ├── Register.vue # 注册页
│   │   ├── Dashboard.vue # 仪表盘
│   │   ├── Files.vue    # 文件管理
│   │   ├── Membership.vue # 会员中心
│   │   ├── Profile.vue  # 个人资料
│   │   └── NotFound.vue # 404页面
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── .eslintrc.cjs         # ESLint配置
├── .gitignore            # Git忽略文件
├── .prettierrc           # Prettier配置
├── index.html            # HTML模板
├── package.json          # 项目配置
└── vite.config.js        # Vite配置
```

## 快速开始

### 1. 安装依赖

```bash
cd frontend-vue
npm install
```

或使用 yarn：

```bash
yarn install
```

### 2. 配置后端地址

编辑 `vite.config.js` 中的代理配置：

```javascript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:5000',  // Flask后端地址
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

### 3. 启动开发服务器

```bash
npm run dev
```

或使用 yarn：

```bash
yarn dev
```

访问 `http://localhost:5173` 查看应用。

### 4. 构建生产版本

```bash
npm run build
```

或使用 yarn：

```bash
yarn build
```

构建产物将在 `dist` 目录中。

### 5. 预览生产构建

```bash
npm run preview
```

或使用 yarn：

```bash
yarn preview
```

## 功能特性

### 用户认证
- 用户注册
- 用户登录
- 用户登出
- Session管理

### 文件管理
- 文件上传
- 文件下载
- 文件列表
- 文件编辑
- 文件删除
- 权限管理

### 会员系统
- 会员信息查看
- 会员等级升级
- 会员特权展示
- 存储使用情况

### 个人资料
- 基本信息编辑
- 密码修改
- 账户删除

## API接口

前端通过以下API与后端通信：

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/user` - 获取用户信息
- `PUT /api/auth/user` - 更新用户信息
- `PUT /api/auth/password` - 修改密码
- `DELETE /api/auth/account` - 删除账户

### 文件相关
- `POST /api/files/upload` - 上传文件
- `GET /api/files` - 获取文件列表
- `GET /api/files/:id` - 获取文件详情
- `GET /api/files/:id/download` - 下载文件
- `PUT /api/files/:id` - 更新文件信息
- `DELETE /api/files/:id` - 删除文件

### 会员相关
- `GET /api/membership/info` - 获取会员信息
- `GET /api/membership/levels` - 获取所有会员等级
- `POST /api/membership/upgrade` - 升级会员
- `GET /api/membership/benefits` - 获取会员权益
- `GET /api/membership/logs` - 获取会员日志

## 环境变量

可以在项目根目录创建 `.env` 文件来配置环境变量：

```bash
VITE_API_BASE_URL=http://localhost:5000
```

## 代码规范

项目使用 ESLint 和 Prettier 进行代码规范检查：

```bash
# 检查代码规范
npm run lint

# 格式化代码
npm run format
```

## 部署

### 开发环境

前端运行在 `http://localhost:5173`，通过 Vite 代理转发到后端 `http://localhost:5000`。

### 生产环境

1. 构建前端项目：

```bash
npm run build
```

2. 将 `dist` 目录部署到 Web 服务器（如 Nginx）：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/dist;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理到Flask后端
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. 确保Flask后端已配置CORS支持。

## 浏览器支持

- Chrome (最新版)
- Firefox (最新版)
- Safari (最新版)
- Edge (最新版)

## 常见问题

### 1. CORS错误

确保Flask后端已正确配置CORS，参考 `../app.py` 中的配置。

### 2. 登录后刷新页面丢失登录状态

这是因为使用Session认证，需要确保后端和前端在同一域下，或配置正确的CORS凭证。

### 3. 文件上传失败

检查：
- 文件大小是否超过会员限制
- 文件类型是否被允许
- 后端上传目录是否有写权限

### 4. 构建失败

尝试删除 `node_modules` 和 `package-lock.json`，重新安装依赖：

```bash
rm -rf node_modules package-lock.json
npm install
```

## 技术支持

如有问题，请参考：
- [Vue 3 文档](https://vuejs.org/)
- [Vue Router 文档](https://router.vuejs.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Vite 文档](https://vitejs.dev/)

## 许可证

本项目仅供学习和研究使用。
