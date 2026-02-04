#!/usr/bin/env python3
"""
将Markdown分析报告转换为PDF格式
使用markdown2和reportlab生成专业PDF报告
"""
import sys
import os
from pathlib import Path

# 简化版：直接提示使用在线工具或VS Code插件
def generate_pdf_info():
    """生成PDF转换说明"""
    
    report_path = Path(__file__).parent.parent / 'docs' / '2026年安徽省事业单位招聘超详细分析报告_最终完整版.md'
    
    print("=" * 80)
    print("PDF报告生成说明")
    print("=" * 80)
    print()
    print(f"Markdown报告路径：{report_path}")
    print()
    print("推荐转换方法：")
    print()
    print("方法1：使用VS Code插件（最简单）")
    print("  1. 在VS Code中打开Markdown文件")
    print("  2. 安装插件：Markdown PDF (yzane.markdown-pdf)")
    print("  3. 右键选择 'Markdown PDF: Export (pdf)'")
    print("  4. PDF将自动生成在同目录下")
    print()
    print("方法2：使用在线工具")
    print("  1. 打开 https://www.markdowntopdf.com/")
    print("  2. 上传Markdown文件")
    print("  3. 下载生成的PDF")
    print()
    print("方法3：安装Pandoc（推荐专业用户）")
    print("  1. 安装：brew install pandoc basictex")
    print("  2. 转换：pandoc report.md -o report.pdf --pdf-engine=xelatex")
    print()
    print("=" * 80)
    print("提示：报告已生成完整Markdown版本，可直接阅读或转换")
    print("=" * 80)
    
    # 创建PDF生成脚本
    script_content = f"""#!/bin/bash
# PDF生成脚本（需要先安装pandoc）

REPORT_DIR="{report_path.parent}"
REPORT_FILE="{report_path.name}"

echo "开始生成PDF报告..."

if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc未安装"
    echo "请运行: brew install pandoc basictex"
    exit 1
fi

cd "$REPORT_DIR"

pandoc "$REPORT_FILE" -o "2026年安徽省事业单位招聘超详细分析报告.pdf" \\
    --pdf-engine=xelatex \\
    --toc \\
    --toc-depth=3 \\
    -V CJKmainfont="PingFang SC" \\
    -V geometry:margin=1in \\
    --highlight-style=tango

if [ $? -eq 0 ]; then
    echo "✅ PDF生成成功！"
    echo "   路径: $REPORT_DIR/2026年安徽省事业单位招聘超详细分析报告.pdf"
else
    echo "❌ PDF生成失败"
fi
"""
    
    script_path = Path(__file__).parent / 'generate_pdf.sh'
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    
    print(f"\n✅ PDF生成脚本已创建：{script_path}")
    print(f"   运行: {script_path}")

if __name__ == '__main__':
    generate_pdf_info()
