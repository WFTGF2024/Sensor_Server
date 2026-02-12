#!/usr/bin/env python3
"""
验证所有 repository 文件是否已正确适配 SQLite
"""

import os
import re

def verify_file(filepath):
    """验证单个文件"""
    print(f"\n{'='*60}")
    print(f"验证文件: {os.path.basename(filepath)}")
    print('='*60)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # 移除注释以便检查 SQL 语句
    content_no_comments = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    
    # 检查是否还有 %s 占位符（排除注释中的）
    if re.search(r'%s', content_no_comments):
        issues.append("❌ 发现 MySQL 的 %s 占位符")
    
    # 检查是否还有 with db.cursor() as cur
    if re.search(r'with\s+db\.cursor\(\)\s+as\s+cur', content):
        issues.append("❌ 发现 with db.cursor() as cur 语句")
    
    # 检查是否还有 TRUE/FALSE（在 SQL 中，排除注释）
    sql_true_false = re.findall(r'["\'].*?\b(TRUE|FALSE)\b.*?["\']', content_no_comments)
    if sql_true_false:
        issues.append(f"❌ 发现 SQL 中的 TRUE/FALSE: {sql_true_false}")
    
    # 检查是否还有 DATE_FORMAT（排除注释）
    if re.search(r'DATE_FORMAT', content_no_comments):
        issues.append("❌ 发现 DATE_FORMAT 函数")
    
    # 检查是否还有 GREATEST（排除注释）
    if re.search(r'GREATEST', content_no_comments):
        issues.append("❌ 发现 GREATEST 函数")
    
    # 检查是否还有 ON DUPLICATE KEY UPDATE（排除注释）
    if re.search(r'ON\s+DUPLICATE\s+KEY\s+UPDATE', content_no_comments, re.IGNORECASE):
        issues.append("❌ 发现 ON DUPLICATE KEY UPDATE")
    
    # 检查是否有正确的 SQLite 语法
    sqlite_features = []
    if re.search(r'\?', content):
        sqlite_features.append("✅ 使用 ? 占位符")
    
    if re.search(r'cur\s*=\s*db\.cursor\(\)', content):
        sqlite_features.append("✅ 手动管理 cursor")
    
    if re.search(r'strftime', content):
        sqlite_features.append("✅ 使用 strftime")
    
    if re.search(r"datetime\('now'\)", content):
        sqlite_features.append("✅ 使用 datetime('now')")
    
    if re.search(r'\b[01]\b', content):
        sqlite_features.append("✅ 使用 1/0 代替 TRUE/FALSE")
    
    if re.search(r'INSERT\s+OR\s+REPLACE', content, re.IGNORECASE):
        sqlite_features.append("✅ 使用 INSERT OR REPLACE")
    
    if re.search(r'MAX\s*\(', content):
        sqlite_features.append("✅ 使用 MAX 代替 GREATEST")
    
    # 输出结果
    if issues:
        print("\n发现的问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ 所有检查通过！")
        
        if sqlite_features:
            print("\nSQLite 适配特性:")
            for feature in sqlite_features:
                print(f"  {feature}")
        
        return True

def main():
    """主函数"""
    repo_dir = "/home/wft/Sensor_Server/backend-flask/repositories"
    
    # 获取所有 .py 文件（除了 __init__.py 和验证脚本本身）
    py_files = [
        os.path.join(repo_dir, f)
        for f in os.listdir(repo_dir)
        if f.endswith('.py') and f not in ['__init__.py', 'verify_sqlite_adaptation.py']
    ]
    
    print("="*60)
    print("SQLite 适配验证工具")
    print("="*60)
    print(f"\n检查 {len(py_files)} 个文件...")
    
    all_passed = True
    for filepath in sorted(py_files):
        if not verify_file(filepath):
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有文件都已成功适配 SQLite！")
    else:
        print("❌ 部分文件需要进一步修改")
    print("="*60)

if __name__ == "__main__":
    main()
