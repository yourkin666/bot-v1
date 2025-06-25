#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告生成器
生成详细的测试报告和统计信息
"""

import subprocess
import json
import datetime
import os
import sys
from pathlib import Path


def run_command(command: str) -> dict:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "命令执行超时",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


def generate_test_report():
    """生成测试报告"""
    print("🚀 开始生成测试报告...")
    
    # 创建报告目录
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 测试类型配置
    test_configs = [
        {"name": "单元测试", "command": "python3 -m pytest tests/test_unit.py -v --tb=short"},
        {"name": "API测试", "command": "python3 -m pytest tests/test_api.py -v --tb=short"},
        {"name": "性能测试", "command": "python3 -m pytest tests/test_performance.py -v --tb=short"},
        {"name": "安全测试", "command": "python3 -m pytest tests/test_security.py -v --tb=short"},
        {"name": "边界测试", "command": "python3 -m pytest tests/test_edge_cases.py -v --tb=short"},
    ]
    
    # 运行测试并收集结果
    test_results = {}
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for config in test_configs:
        print(f"📋 运行 {config['name']}...")
        result = run_command(config['command'])
        
        # 解析测试结果
        output = result['stdout']
        
        # 提取测试统计信息
        passed = output.count(' PASSED')
        failed = output.count(' FAILED')
        skipped = output.count(' SKIPPED')
        errors = output.count(' ERROR')
        
        test_results[config['name']] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "total": passed + failed + skipped + errors,
            "success_rate": (passed / (passed + failed + errors)) * 100 if (passed + failed + errors) > 0 else 0,
            "output": output[:2000] if output else "无输出",  # 限制输出长度
            "command": config['command']
        }
        
        total_tests += passed + failed + skipped + errors
        total_passed += passed
        total_failed += failed + errors
        total_skipped += skipped
        
        print(f"   ✅ 通过: {passed}, ❌ 失败: {failed + errors}, ⏭️ 跳过: {skipped}")
    
    # 生成HTML报告
    html_report = generate_html_report(test_results, total_tests, total_passed, total_failed, total_skipped)
    
    # 保存HTML报告
    html_file = reports_dir / "test_summary.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    # 生成JSON报告
    json_report = {
        "generated_at": datetime.datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "success_rate": (total_passed / total_tests) * 100 if total_tests > 0 else 0
        },
        "test_results": test_results
    }
    
    json_file = reports_dir / "test_summary.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)
    
    # 打印总结
    print("\n" + "="*60)
    print("📊 测试报告总结")
    print("="*60)
    print(f"总测试数量: {total_tests}")
    print(f"✅ 通过: {total_passed}")
    print(f"❌ 失败: {total_failed}")
    print(f"⏭️ 跳过: {total_skipped}")
    print(f"🎯 成功率: {(total_passed / total_tests) * 100:.1f}%" if total_tests > 0 else "成功率: 0%")
    print(f"\n📋 详细报告已保存到:")
    print(f"   - HTML: {html_file.absolute()}")
    print(f"   - JSON: {json_file.absolute()}")
    
    return json_report


def generate_html_report(test_results: dict, total_tests: int, total_passed: int, total_failed: int, total_skipped: int) -> str:
    """生成HTML报告"""
    
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多模态聊天机器人测试报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f7;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .summary {{
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .summary-card {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .summary-card.total {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }}
        .summary-card.passed {{
            background: #e8f5e8;
            border-left: 4px solid #4caf50;
        }}
        .summary-card.failed {{
            background: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .summary-card.skipped {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 2em;
            font-weight: 600;
        }}
        .summary-card p {{
            margin: 0;
            color: #666;
        }}
        .success-rate {{
            margin: 20px 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4caf50, #8bc34a);
            transition: width 0.3s ease;
        }}
        .test-results {{
            padding: 0 30px 30px;
        }}
        .test-category {{
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        .test-category-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-category-header h3 {{
            margin: 0;
            color: #333;
        }}
        .test-stats {{
            display: flex;
            gap: 15px;
            font-size: 0.9em;
        }}
        .stat {{
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .stat.passed {{ background: #e8f5e8; color: #2e7d32; }}
        .stat.failed {{ background: #ffebee; color: #c62828; }}
        .stat.skipped {{ background: #fff3e0; color: #ef6c00; }}
        .test-output {{
            padding: 20px;
            background: #f8f9fa;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85em;
            line-height: 1.4;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }}
        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 多模态聊天机器人</h1>
            <p>测试报告 - 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>{total_tests}</h3>
                <p>总测试数</p>
            </div>
            <div class="summary-card passed">
                <h3>{total_passed}</h3>
                <p>通过测试</p>
            </div>
            <div class="summary-card failed">
                <h3>{total_failed}</h3>
                <p>失败测试</p>
            </div>
            <div class="summary-card skipped">
                <h3>{total_skipped}</h3>
                <p>跳过测试</p>
            </div>
        </div>
        
        <div class="success-rate">
            <h3>总体成功率: {success_rate:.1f}%</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate}%"></div>
            </div>
        </div>
        
        <div class="test-results">
            <h2>详细测试结果</h2>
    """
    
    for category, results in test_results.items():
        html += f"""
            <div class="test-category">
                <div class="test-category-header">
                    <h3>{category}</h3>
                    <div class="test-stats">
                        <span class="stat passed">✅ {results['passed']}</span>
                        <span class="stat failed">❌ {results['failed'] + results['errors']}</span>
                        <span class="stat skipped">⏭️ {results['skipped']}</span>
                        <span>成功率: {results['success_rate']:.1f}%</span>
                    </div>
                </div>
                <div class="test-output">{results['output']}</div>
            </div>
        """
    
    html += """
        </div>
        
        <div class="footer">
            <p>此报告由自动化测试系统生成</p>
        </div>
    </div>
</body>
</html>
    """
    
    return html


if __name__ == '__main__':
    try:
        generate_test_report()
    except KeyboardInterrupt:
        print("\n❌ 报告生成被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 生成报告时发生错误: {e}")
        sys.exit(1) 