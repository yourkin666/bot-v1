#!/bin/bash
# pytest 测试运行脚本

echo "🧪 多模态聊天机器人 pytest 测试套件"
echo "=" * 50

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ 未找到.env文件，请先配置API密钥"
    exit 1
fi

# 加载环境变量
export $(cat .env | xargs)

# 检查API密钥
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ 未找到GROQ_API_KEY，请检查.env文件配置"
    exit 1
fi

if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo "❌ 未找到SILICONFLOW_API_KEY，请检查.env文件配置"
    exit 1
fi

echo "✅ 环境配置检查通过"

# 创建报告目录
mkdir -p reports

# 运行pytest测试
echo "🚀 运行pytest测试..."

# 根据参数选择不同的测试运行方式
case "${1:-all}" in
    "fast")
        echo "⚡ 运行快速测试（跳过慢速测试）"
        python3 -m pytest tests/ -v -m "not slow" --tb=short
        ;;
    "integration")
        echo "🔗 运行集成测试"
        python3 -m pytest tests/ -v -m "integration" --tb=short
        ;;
    "api")
        echo "🌐 运行API测试"
        python3 -m pytest tests/ -v -m "api" --tb=short
        ;;
    "performance")
        echo "⚡ 运行性能测试"
        python3 -m pytest tests/test_performance.py -v --tb=short
        ;;
    "security")
        echo "🔒 运行安全测试"
        python3 -m pytest tests/test_security.py -v --tb=short
        ;;
    "edge")
        echo "🎯 运行边界情况测试"
        python3 -m pytest tests/test_edge_cases.py -v --tb=short
        ;;
    "unit")
        echo "🧪 运行单元测试"
        python3 -m pytest tests/test_unit.py -v --tb=short
        ;;
    "stress")
        echo "🔥 运行压力测试"
        python3 -m pytest tests/ -v -m "stress" --tb=short
        ;;
    "report")
        echo "📊 生成详细报告"
        python3 -m pytest tests/ -v --html=reports/pytest_report.html --self-contained-html --cov=. --cov-report=html:reports/coverage --cov-report=term-missing
        echo "📋 报告已生成："
        echo "   - HTML报告: reports/pytest_report.html"
        echo "   - 覆盖率报告: reports/coverage/index.html"
        ;;
    "summary")
        echo "📋 生成测试总结报告"
        python3 tests/generate_test_report.py
        ;;
    "all"|*)
        echo "🧪 运行所有测试"
        python3 -m pytest tests/ -v --tb=short
        ;;
esac

echo "✅ 测试完成"

# 显示使用说明
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "📖 测试脚本使用说明："
    echo "  ./run_tests.sh [选项]"
    echo ""
    echo "可用选项："
    echo "  fast        - 运行快速测试（跳过慢速测试）"
    echo "  integration - 运行集成测试"
    echo "  api         - 运行API测试"
    echo "  unit        - 运行单元测试"
    echo "  performance - 运行性能测试"
    echo "  security    - 运行安全测试"
    echo "  edge        - 运行边界情况测试"
    echo "  stress      - 运行压力测试"
    echo "  report      - 生成详细测试报告和覆盖率"
    echo "  summary     - 生成测试总结报告"
    echo "  all         - 运行所有测试（默认）"
    echo ""
    echo "示例："
    echo "  ./run_tests.sh fast      # 快速测试"
    echo "  ./run_tests.sh security  # 安全测试"
    echo "  ./run_tests.sh summary   # 生成报告"
    exit 0
fi 