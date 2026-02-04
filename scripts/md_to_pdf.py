#!/usr/bin/env python3
"""
使用WeasyPrint将Markdown转换为PDF
支持中文、图表、完整样式
"""
import markdown
from weasyprint import HTML, CSS
from pathlib import Path
import re

def convert_markdown_to_pdf(md_file, output_pdf):
    """
    将Markdown文件转换为PDF
    
    Args:
        md_file: Markdown文件路径
        output_pdf: 输出PDF路径
    """
    print(f"正在转换: {md_file}")
    
    # 读取Markdown内容
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 转换Markdown为HTML
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.toc',
            'markdown.extensions.nl2br'
        ]
    )
    
    # 添加CSS样式
    css_style = """
    @page {
        size: A4;
        margin: 2cm;
        @top-center {
            content: "2026年安徽省事业单位招聘超详细分析报告";
            font-size: 10px;
            color: #666;
        }
        @bottom-center {
            content: "第 " counter(page) " 页";
            font-size: 10px;
            color: #666;
        }
    }
    
    body {
        font-family: "PingFang SC", "Microsoft YaHei", "SimSun", sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    
    h1 {
        font-size: 24pt;
        color: #1a73e8;
        border-bottom: 3px solid #1a73e8;
        padding-bottom: 10px;
        margin-top: 30px;
        page-break-before: always;
    }
    
    h2 {
        font-size: 18pt;
        color: #1a73e8;
        border-bottom: 2px solid #dadce0;
        padding-bottom: 5px;
        margin-top: 20px;
    }
    
    h3 {
        font-size: 14pt;
        color: #202124;
        margin-top: 15px;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
        font-size: 9pt;
    }
    
    th {
        background-color: #1a73e8;
        color: white;
        padding: 8px;
        text-align: left;
        font-weight: bold;
    }
    
    td {
        border: 1px solid #dadce0;
        padding: 6px;
    }
    
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    code {
        background-color: #f1f3f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: "Monaco", "Courier New", monospace;
        font-size: 9pt;
    }
    
    pre {
        background-color: #f1f3f4;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
        font-size: 9pt;
    }
    
    blockquote {
        border-left: 4px solid #1a73e8;
        padding-left: 15px;
        color: #5f6368;
        font-style: italic;
        margin: 10px 0;
    }
    
    ul, ol {
        margin: 10px 0;
        padding-left: 25px;
    }
    
    li {
        margin: 5px 0;
    }
    
    .page-break {
        page-break-after: always;
    }
    """
    
    # 构建完整HTML
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>2026年安徽省事业单位招聘超详细分析报告</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    try:
        # 生成PDF
        HTML(string=full_html).write_pdf(
            output_pdf,
            stylesheets=[CSS(string=css_style)]
        )
        
        file_size = Path(output_pdf).stat().st_size / 1024 / 1024
        print(f"✅ PDF生成成功！")
        print(f"   输出路径: {output_pdf}")
        print(f"   文件大小: {file_size:.2f} MB")
        return True
        
    except Exception as e:
        print(f"❌ PDF生成失败: {str(e)}")
        return False

def main():
    """主函数"""
    project_dir = Path(__file__).parent.parent
    
    # 输入输出路径
    md_file = project_dir / 'docs' / '2026年安徽省事业单位招聘超详细分析报告_最终完整版.md'
    pdf_file = project_dir / 'docs' / '2026年安徽省事业单位招聘超详细分析报告_完整版.pdf'
    
    # 执行摘要也生成PDF
    summary_md = project_dir / 'docs' / '2026年安徽省事业单位招聘分析报告_执行摘要.md'
    summary_pdf = project_dir / 'docs' / '2026年安徽省事业单位招聘分析报告_执行摘要.pdf'
    
    print("=" * 80)
    print("安徽省事业单位招聘分析报告 - PDF生成工具")
    print("=" * 80)
    print()
    
    # 转换完整版
    if md_file.exists():
        print("[1/2] 转换完整版报告...")
        convert_markdown_to_pdf(str(md_file), str(pdf_file))
    else:
        print(f"❌ 找不到文件: {md_file}")
    
    # 转换执行摘要
    if summary_md.exists():
        print()
        print("[2/2] 转换执行摘要...")
        convert_markdown_to_pdf(str(summary_md), str(summary_pdf))
    else:
        print(f"⚠️  执行摘要文件不存在，跳过")
    
    print()
    print("=" * 80)
    print("✅ PDF报告生成完成！")
    print("=" * 80)

if __name__ == '__main__':
    main()
