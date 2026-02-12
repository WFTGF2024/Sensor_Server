"""
User Controller - 用户控制器
"""
from flask import jsonify
from db import get_db
from services.user_service import UserService

user_service = UserService()


def list_users():
    """
    GET /users
    获取所有用户列表
    
    Returns:
        JSON response with user list
    """
    users = user_service.get_all_users(include_membership=True)
    return jsonify(users)
