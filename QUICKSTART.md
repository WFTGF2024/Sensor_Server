# Sensor_Flask 快速开始指南

## 快速启动

### 1. 环境准备

```bash
# 进入项目目录
cd Sensor_Flask

# 创建并激活 Conda 环境
conda env create -f environment.yml
conda activate sensor_flask
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的配置
nano .env
```

**重要配置项**：
```bash
# 生产环境必须修改
FLASK_SECRET_KEY=your-secure-random-secret-key-here
DB_PASSWORD=your-database-password

# 可选配置
FLASK_ENV=production
FLASK_PORT=5000
```

### 3. 启动应用

**开发模式**：
```bash
python app.py
```

**生产模式**：
```bash
python wsgi.py
```

### 4. 运行测试

```bash
# 运行所有测试
./run_tests.sh

# 运行单元测试
./run_tests.sh unit

# 运行集成测试
./run_tests.sh integration

# 生成覆盖率报告
./run_tests.sh all coverage
```

## API 测试

### 注册用户

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepass123",
    "email": "test@example.com"
  }'
```

### 登录

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepass123"
  }' \
  -c cookies.txt
```

### 获取用户信息

```bash
curl -X GET http://localhost:5000/auth/user \
  -b cookies.txt
```

### 登出

```bash
curl -X POST http://localhost:5000/auth/logout \
  -b cookies.txt
```

## 项目结构

```
Sensor_Flask/
├── app.py                    # 主应用文件
├── wsgi.py                   # WSGI 服务器
├── config.py                 # 配置管理
├── errors.py                 # 错误处理
├── db.py                     # 数据库连接
├── auth.py                   # 认证模块
├── download.py               # 文件管理
├── .env.example              # 环境变量模板
├── environment.yml           # Conda 环境配置
├── README.md                 # 项目说明
├── API.md                    # API 文档
├── IMPROVEMENTS.md           # 改进总结
├── QUICKSTART.md             # 快速开始（本文件）
├── run_tests.sh              # 测试脚本
└── tests/                    # 测试目录
    ├── conftest.py
    ├── README.md
    ├── unit/
    └── integration/
```

## 常见问题

### 1. 数据库连接失败

检查 `.env` 文件中的数据库配置：
```bash
DB_HOST=localhost
DB_USER=zjh
DB_PASSWORD=your-password
DB_NAME=modality
```

### 2. 测试失败

确保已安装测试依赖：
```bash
pip install pytest pytest-cov pytest-mock
```

### 3. 端口被占用

修改 `.env` 文件中的端口：
```bash
FLASK_PORT=8080
```

### 4. 权限错误

确保文件上传目录存在且有写权限：
```bash
mkdir -p /root/pythonproject_remote/download/
chmod 755 /root/pythonproject_remote/download/
```

## 下一步

- 阅读 [API.md](API.md) 了解完整的 API 文档
- 阅读 [IMPROVEMENTS.md](IMPROVEMENTS.md) 了解项目改进详情
- 阅读 [tests/README.md](tests/README.md) 了解测试框架

## 技术支持

如遇问题，请检查：
1. 环境变量配置是否正确
2. 数据库连接是否正常
3. 目录权限是否正确
4. 依赖包是否完整安装

## 许可证

本项目仅供学习和研究使用。