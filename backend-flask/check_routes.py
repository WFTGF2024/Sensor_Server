#!/usr/bin/env python3
"""
检查 Flask 路由配置
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app import create_app

    app = create_app()

    print("=" * 60)
    print("Flask 路由配置检查")
    print("=" * 60)

    # 获取所有路由
    rules = list(app.url_map.iter_rules())

    # 过滤出文件相关的路由
    file_routes = [rule for rule in rules if 'file' in rule.rule.lower() or 'download' in rule.rule.lower()]

    print(f"\n找到 {len(file_routes)} 个文件/下载相关的路由:\n")

    for rule in sorted(file_routes, key=lambda r: r.rule):
        print(f"路由: {rule.rule}")
        print(f"  方法: {', '.join(rule.methods)}")
        print(f"  端点: {rule.endpoint}")
        print()

    # 检查特定路由
    target_route = '/api/download/files'
    matching_rules = [rule for rule in rules if rule.rule == target_route]

    print("=" * 60)
    if matching_rules:
        print(f"✓ 找到目标路由: {target_route}")
        for rule in matching_rules:
            print(f"  方法: {', '.join(rule.methods)}")
            print(f"  端点: {rule.endpoint}")
    else:
        print(f"✗ 未找到目标路由: {target_route}")
        print("\n相似的路由:")
        similar = [rule for rule in rules if 'file' in rule.rule.lower()]
        for rule in similar:
            print(f"  {rule.rule} - {', '.join(rule.methods)}")

    print("=" * 60)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
