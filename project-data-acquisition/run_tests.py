#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
测试运行脚本
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", verbose=False, coverage=False):
    """运行测试"""
    project_root = Path(__file__).parent.absolute()
    
    # 基础命令
    cmd = [sys.executable, "-m", "pytest"]
    
    # 选择测试类型
    if test_type == "unit":
        cmd.append("tests/unit")
    elif test_type == "integration":
        cmd.append("tests/integration")
    elif test_type == "collector":
        cmd.extend(["-m", "collector"])
    elif test_type == "utils":
        cmd.extend(["-m", "utils"])
    else:
        cmd.append("tests")
    
    # 添加选项
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend([
            "--cov=apps",
            "--cov-report=term-missing",
            "--cov-report=html:tests/reports/htmlcov"
        ])
    
    # 其他选项
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--junit-xml=tests/reports/junit.xml"
    ])
    
    print(f"🔧 运行测试命令: {' '.join(cmd)}")
    print(f"📁 项目根目录: {project_root}")
    print()
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return 1

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行项目测试")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "collector", "utils"],
        default="all",
        help="测试类型"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告"
    )
    
    args = parser.parse_args()
    
    # 创建报告目录
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 运行测试
    exit_code = run_tests(args.type, args.verbose, args.coverage)
    
    if exit_code == 0:
        print("✅ 测试通过")
    else:
        print(f"❌ 测试失败，退出码: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())