"""
Formatters - 格式化工具
"""


def format_bytes(bytes_value: int) -> str:
    """
    格式化字节数为人类可读格式
    
    Args:
        bytes_value: 字节数
        
    Returns:
        格式化后的字符串
        
    Examples:
        >>> format_bytes(1024)
        '1.00 KB'
        >>> format_bytes(1048576)
        '1.00 MB'
        >>> format_bytes(1073741824)
        '1.00 GB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"


def format_datetime(dt, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        
    Returns:
        格式化后的字符串
    """
    if dt is None:
        return '永久'
    return dt.strftime(format_str)


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    格式化百分比
    
    Args:
        value: 百分比值（0-100）
        decimals: 小数位数
        
    Returns:
        格式化后的字符串
    """
    return f"{value:.{decimals}f}%"
