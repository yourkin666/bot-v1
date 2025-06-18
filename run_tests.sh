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
    "report")
        echo "📊 生成详细报告"
        python3 -m pytest tests/ -v --html=reports/pytest_report.html --self-contained-html --cov=. --cov-report=html:reports/coverage --cov-report=term-missing
        echo "📋 报告已生成："
        echo "   - HTML报告: reports/pytest_report.html"
        echo "   - 覆盖率报告: reports/coverage/index.html"
        ;;
    "all"|*)
        echo "🧪 运行所有测试"
        python3 -m pytest tests/ -v --tb=short
        ;;
esac

echo "✅ 测试完成" 