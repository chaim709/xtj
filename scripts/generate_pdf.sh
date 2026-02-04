#!/bin/bash
# PDF生成脚本（需要先安装pandoc）

REPORT_DIR="/Users/chaim/CodeBuddy/公考项目/docs"
REPORT_FILE="2026年安徽省事业单位招聘超详细分析报告_最终完整版.md"

echo "开始生成PDF报告..."

if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc未安装"
    echo "请运行: brew install pandoc basictex"
    exit 1
fi

cd "$REPORT_DIR"

pandoc "$REPORT_FILE" -o "2026年安徽省事业单位招聘超详细分析报告.pdf" \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=3 \
    -V CJKmainfont="PingFang SC" \
    -V geometry:margin=1in \
    --highlight-style=tango

if [ $? -eq 0 ]; then
    echo "✅ PDF生成成功！"
    echo "   路径: $REPORT_DIR/2026年安徽省事业单位招聘超详细分析报告.pdf"
else
    echo "❌ PDF生成失败"
fi
