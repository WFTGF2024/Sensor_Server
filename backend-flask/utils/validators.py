"""
Validators - 验证工具
"""
import re


def validate_password_strength(password: str, min_length: int = 6) -> tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password: 密码
        min_length: 最小长度
        
    Returns:
        (是否有效, 错误消息)
    """
    if len(password) < min_length:
        return False, f"密码长度不能少于 {min_length} 个字符"
    
    if not any(char.isupper() for char in password):
        return False, "密码必须包含至少一个大写字母"
    
    if not any(char.islower() for char in password):
        return False, "密码必须包含至少一个小写字母"
    
    if not any(char.isdigit() for char in password):
        return False, "密码必须包含至少一个数字"
    
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        (是否有效, 错误消息)
    """
    if not email:
        return True, ""  # 邮箱是可选的
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "邮箱格式不正确"
    
    return True, ""


def validate_phone(phone: str) -> tuple[bool, str]:
    """
    验证手机号格式
    
    Args:
        phone: 手机号
        
    Returns:
        (是否有效, 错误消息)
    """
    if not phone:
        return True, ""  # 手机号是可选的
    
    # 中国大陆手机号格式：1开头，11位数字
    pattern = r'^1[3-9]\d{9}$'
    if not re.match(pattern, phone):
        return False, "手机号格式不正确"
    
    return True, ""


def validate_username(username: str, min_length: int = 3, max_length: int = 20) -> tuple[bool, str]:
    """
    验证用户名格式
    
    Args:
        username: 用户名
        min_length: 最小长度
        max_length: 最大长度
        
    Returns:
        (是否有效, 错误消息)
    """
    if not username:
        return False, "用户名不能为空"
    
    if len(username) < min_length:
        return False, f"用户名长度不能少于 {min_length} 个字符"
    
    if len(username) > max_length:
        return False, f"用户名长度不能超过 {max_length} 个字符"
    
    # 只允许字母、数字、下划线
    pattern = r'^[a-zA-Z0-9_]+$'
    if not re.match(pattern, username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, ""


def validate_file_size(file_size: int, max_size: int) -> tuple[bool, str]:
    """
    验证文件大小
    
    Args:
        file_size: 文件大小（字节）
        max_size: 最大允许大小（字节）
        
    Returns:
        (是否有效, 错误消息)
    """
    if file_size > max_size:
        from .formatters import format_bytes
        return False, f"文件大小超过限制（最大 {format_bytes(max_size)}）"
    
    return True, ""
