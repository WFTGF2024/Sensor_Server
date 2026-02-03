# Sensor_Flask

这是基于Python Flask框架构建的简易后端系统，由WSGI服务器部署。

## 主要功能

- **恶意调用检测**：实现请求频率限制
- **用户认证系统**：支持注册、登录、密码管理
- **文件管理**：支持文件上传、下载、权限管理
- **日志系统**：按日期分割的详细日志记录

## 环境配置

### 1. 安装依赖
```bash
conda env create -f environment.yml
conda activate sensor_flask
```

### 2. 配置环境变量
复制环境变量模板并配置：
```bash
cp .env.example .env
# 编辑 .env 文件，设置你的配置值
```

### 3. 环境变量说明
- `FLASK_ENV`: 运行环境 (development/production/testing)
- `FLASK_SECRET_KEY`: Flask应用密钥
- `DB_*`: 数据库连接配置
- `UPLOAD_ROOT`: 文件上传根目录
- `RATE_LIMIT_*`: 请求频率限制配置

## 运行应用

### 开发模式
```bash
python app.py
```

### 生产模式
```bash
python wsgi.py
```

## 项目结构
```
Sensor_Flask/
├── app.py              # 主应用文件
├── wsgi.py             # WSGI服务器启动文件
├── db.py               # 数据库连接配置
├── auth.py             # 用户认证模块
├── download.py         # 文件管理模块
├── config.py           # 配置管理
├── .env.example        # 环境变量模板
├── environment.yml     # Conda环境配置
├── log/                # 日志目录
└── __pycache__/        # Python字节码缓存
```

## 安全特性
1. 请求频率限制
2. 密码安全哈希
3. 文件安全处理
4. 会话管理
5. 权限控制

## 接口文档
对应的接口文档请查看毕业设计中的api.md文件