"""
Web Controller - 前端页面控制器
处理所有前端页面的渲染和路由
"""
from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from services.auth_service import AuthService
from services.file_service import FileService
from services.membership_service import MembershipService
from errors import AuthenticationError, ValidationError, NotFoundError
from utils.formatters import format_bytes

web_bp = Blueprint('web', __name__)

auth_service = AuthService()
file_service = FileService()
membership_service = MembershipService()


@web_bp.route('/')
def index():
    """首页"""
    return render_template('index.html')


@web_bp.route('/test')
def test():
    """测试页面"""
    return render_template('test.html')


@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    # 如果已登录，重定向到仪表盘
    if 'user_id' in session:
        return redirect(url_for('web.dashboard'))

    if request.method == 'POST':
        data = request.get_json() or request.form.to_dict()

        try:
            user = auth_service.login(
                username=data.get('username'),
                password=data.get('password'),
                ip_address=request.remote_addr
            )

            # 设置session
            session['user_id'] = user['user_id']
            session['username'] = user['username']

            flash('登录成功！', 'success')
            return redirect(url_for('web.dashboard'))

        except AuthenticationError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash('登录失败，请重试', 'error')

    return render_template('login.html')


@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    # 如果已登录，重定向到仪表盘
    if 'user_id' in session:
        return redirect(url_for('web.dashboard'))

    if request.method == 'POST':
        data = request.get_json() or request.form.to_dict()

        try:
            result = auth_service.register(
                username=data.get('username'),
                password=data.get('password'),
                email=data.get('email'),
                phone=data.get('phone'),
                qq=data.get('qq'),
                wechat=data.get('wechat')
            )

            # 设置session
            session['user_id'] = result['user_id']
            session['username'] = result['username']

            flash('注册成功！', 'success')
            return redirect(url_for('web.dashboard'))

        except ValidationError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash('注册失败，请重试', 'error')

    return render_template('register.html')


@web_bp.route('/logout')
def logout():
    """登出"""
    if 'user_id' in session:
        user_id = session['user_id']
        auth_service.logout(user_id)
        session.clear()
        flash('已成功退出登录', 'success')
    return redirect(url_for('web.index'))


@web_bp.route('/dashboard')
def dashboard():
    """用户仪表盘"""
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('web.login'))

    user_id = session['user_id']

    try:
        # 获取用户信息
        user = auth_service.get_profile(user_id)

        # 获取文件统计
        files = file_service.list_files(user_id)
        files_count = len(files)

        # 获取会员信息
        membership = user.get('membership', {})

        # 计算存储使用情况
        storage_used = membership.get('storage_used', 0)
        storage_limit = membership.get('storage_limit', 0)
        usage_percentage = round((storage_used / storage_limit * 100), 2) if storage_limit > 0 else 0

        # 格式化数据
        stats = {
            'files_count': files_count,
            'storage_used': storage_used,
            'storage_used_formatted': format_bytes(storage_used),
            'storage_limit': storage_limit,
            'storage_limit_formatted': format_bytes(storage_limit),
            'usage_percentage': usage_percentage,
            'membership_level': membership.get('level_code', 'free'),
            'membership_name': membership.get('level_name', '普通用户'),
            'max_file_size': membership.get('max_file_size', 0),
            'max_file_size_formatted': format_bytes(membership.get('max_file_size', 0)),
            'max_files_count': membership.get('max_file_count', 0)
        }

        return render_template('dashboard.html', stats=stats)

    except NotFoundError as e:
        flash('用户不存在', 'error')
        return redirect(url_for('web.login'))
    except Exception as e:
        flash('获取信息失败', 'error')
        return redirect(url_for('web.login'))


@web_bp.route('/files')
def files():
    """文件管理页面"""
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('web.login'))

    user_id = session['user_id']

    try:
        # 获取文件列表
        files = file_service.list_files(user_id)

        # 获取用户信息
        user = auth_service.get_profile(user_id)
        membership = user.get('membership', {})

        # 计算存储使用情况
        storage_used = membership.get('storage_used', 0)
        storage_limit = membership.get('storage_limit', 0)
        usage_percentage = round((storage_used / storage_limit * 100), 2) if storage_limit > 0 else 0

        # 格式化文件大小
        for file in files:
            file['file_size_formatted'] = format_bytes(file.get('file_size', 0))

        stats = {
            'files_count': len(files),
            'storage_used': storage_used,
            'storage_used_formatted': format_bytes(storage_used),
            'storage_limit': storage_limit,
            'storage_limit_formatted': format_bytes(storage_limit),
            'usage_percentage': usage_percentage,
            'max_file_size': membership.get('max_file_size', 0),
            'max_file_size_formatted': format_bytes(membership.get('max_file_size', 0))
        }

        return render_template('files.html', files=files, stats=stats)

    except Exception as e:
        flash('获取文件列表失败', 'error')
        return redirect(url_for('web.dashboard'))


@web_bp.route('/membership')
def membership():
    """会员中心页面"""
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('web.login'))

    user_id = session['user_id']

    try:
        # 获取用户信息
        user = auth_service.get_profile(user_id)
        membership = user.get('membership', {})

        # 计算存储使用情况
        storage_used = membership.get('storage_used', 0)
        storage_limit = membership.get('storage_limit', 0)
        usage_percentage = round((storage_used / storage_limit * 100), 2) if storage_limit > 0 else 0

        # 获取会员权益
        benefits_data = membership_service.get_benefits(user_id)
        benefits = benefits_data.get('benefits', [])
        privileges = [benefit['description'] for benefit in benefits if benefit.get('description')]

        # 如果没有权益信息，添加默认权益
        if not privileges:
            if membership.get('level_code') == 'free':
                privileges = ['基础文件存储']
            elif membership.get('level_code') == 'silver':
                privileges = ['基础文件存储', '文件分享功能']
            elif membership.get('level_code') == 'gold':
                privileges = ['基础文件存储', '文件分享功能', '公开链接', '每日下载100次']
            elif membership.get('level_code') == 'diamond':
                privileges = ['基础文件存储', '文件分享功能', '公开链接', '每日下载1000次', '每日上传500次']

        # 当前会员信息
        current_membership = {
            'level_code': membership.get('level_code', 'free'),
            'level_name': membership.get('level_name', '普通用户'),
            'storage_limit': membership.get('storage_limit', 0),
            'storage_limit_formatted': format_bytes(membership.get('storage_limit', 0)),
            'max_file_size': membership.get('max_file_size', 0),
            'max_file_size_formatted': format_bytes(membership.get('max_file_size', 0)),
            'max_files_count': membership.get('max_file_count', 0),
            'storage_used': storage_used,
            'storage_used_formatted': format_bytes(storage_used),
            'usage_percentage': usage_percentage,
            'privileges': privileges
        }

        # 可升级的会员等级
        all_levels = membership_service.get_all_levels()
        available_levels = []

        for level in all_levels:
            available_levels.append({
                'level_code': level['level_code'],
                'level_name': level['level_name'],
                'storage_limit': level['storage_limit'],
                'storage_limit_formatted': format_bytes(level['storage_limit']),
                'max_file_size': level['max_file_size'],
                'max_file_size_formatted': format_bytes(level['max_file_size']),
                'max_files_count': level['max_file_count']
            })

        return render_template('membership.html',
                             current_membership=current_membership,
                             available_levels=available_levels)

    except Exception as e:
        flash('获取会员信息失败', 'error')
        return redirect(url_for('web.dashboard'))


@web_bp.route('/profile')
def profile():
    """个人资料页面"""
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('web.login'))

    user_id = session['user_id']

    try:
        user = auth_service.get_profile(user_id)
        return render_template('profile.html', user=user)

    except NotFoundError as e:
        flash('用户不存在', 'error')
        return redirect(url_for('web.login'))
    except Exception as e:
        flash('获取用户信息失败', 'error')
        return redirect(url_for('web.dashboard'))
