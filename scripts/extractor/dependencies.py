from __future__ import annotations

import importlib.util
import shutil
import sys
from extractor.config import PYTHON_DEPENDENCIES, HTML_EXTENSIONS


def macos_pdfkit_available() -> bool:
    """PDFKit is a no-install fallback for text-layer PDFs on macOS."""
    return sys.platform == "darwin" and bool(shutil.which("swift"))


DEPENDENCY_GROUPS = [
    {
        "label": "PPTX / PPTM",
        "modules": [],
        "system": [],
        "note": "使用标准库解析器，可保留幻灯片编号和演讲者备注",
    },
    {
        "label": "PDF（文字型）",
        "modules": ["PyPDF2", "pdfminer"],
        "system": ["pdftotext"],
        "any_tool_suffices": True,
        "note": "pdftotext、PyPDF2、pdfminer，或 macOS 上的系统 PDFKit 任一可用即可",
    },
    {
        "label": "PDF（表格/公式/代码密集）",
        "modules": ["docling"],
        "system": [],
        "note": "仅在 --mode technical 时增强；缺失时回退到文字提取链",
    },
    {
        "label": "扫描版 PDF OCR",
        "modules": [],
        "system": ["ocrmypdf", "pdftotext"],
        "note": "可选；低文字密度时才尝试 OCR",
    },
    {
        "label": "EPUB",
        "modules": ["ebooklib", "bs4"],
        "system": [],
        "note": "缺失时回退到标准库 ZIP/HTML 解析",
    },
    {
        "label": "DOCX",
        "modules": ["docx"],
        "system": [],
        "note": "标准库结构化解析器优先，可保留正文顺序、表格、脚注和图片占位；python-docx 仅作兼容回退",
    },
    {
        "label": "HTML",
        "modules": ["bs4"],
        "system": [],
        "note": "缺失时回退到标准库 html.parser",
    },
    {
        "label": "RTF",
        "modules": ["striprtf"],
        "system": [],
        "note": "缺失时回退到基础正则清理",
    },
    {
        "label": "MOBI / AZW / AZW3",
        "modules": [],
        "system": ["ebook-convert"],
        "required": True,
        "note": "仅这些格式需要 Calibre 的 ebook-convert，且无内置回退",
    },
]


def python_module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def missing_python_packages(module_names: list[str]) -> list[str]:
    return [PYTHON_DEPENDENCIES[name] for name in module_names if not python_module_available(name)]


def normalize_install_mode(argv: list[str]) -> str:
    """Retain CLI compatibility while making disabled installation requests explicit."""
    return "requested-but-disabled" if "--install-missing" in argv else "no"


def report_missing(feature: str, module_names: list[str], fallback: str | None) -> None:
    packages = missing_python_packages(module_names)
    if not packages:
        return
    message = f"{feature} 可使用可选包：{', '.join(packages)}。"
    if fallback:
        message += f"当前将使用回退方案：{fallback}。"
    else:
        message += "当前环境没有可用回退方案。"
    message += " 本 Skill 不会自动安装依赖；如需增强能力，请由用户确认后在隔离环境中安装固定版本。"
    print(message)


def prepare_dependencies(ext: str, extraction_mode: str, install_mode: str) -> None:
    """Report optional capabilities without installing packages or changing the system."""
    if ext == ".pdf" and extraction_mode == "technical":
        report_missing("技术型 PDF 提取", ["docling"], "PDF 文字提取链")
    if ext == ".pdf" and not shutil.which("pdftotext"):
        fallback = "macOS PDFKit（系统自带、仅限可读文字层）" if macos_pdfkit_available() else "任何已存在的 PDF 解析器"
        report_missing("PDF 文字提取", ["PyPDF2", "pdfminer"], fallback)
    if ext == ".epub":
        report_missing("EPUB 提取", ["ebooklib", "bs4"], "标准库 ZIP/HTML 解析器")
    if ext in HTML_EXTENSIONS:
        report_missing("HTML 提取", ["bs4"], "标准库 HTML 解析器")
    if ext == ".docx":
        report_missing("DOCX 提取", ["docx"], "标准库 ZIP/XML 解析器")
    if ext == ".rtf":
        report_missing("RTF 提取", ["striprtf"], "基础正则清理")


def run_dependency_check() -> int:
    """Report local capabilities only; never download, install, or modify the environment."""
    print("知识学习助手 — 依赖检查（只读）\n")
    native_pdfkit = macos_pdfkit_available()
    if native_pdfkit:
        print("  macOS PDFKit\n      ✓ system: Swift + PDFKit（可读PDF文字层，无需安装Python包）\n")
    missing_python: list[str] = []
    missing_system: list[str] = []
    for group in DEPENDENCY_GROUPS:
        print(f"  {group['label']}")
        modules = group["modules"]
        system = group["system"]
        available_modules = [name for name in modules if python_module_available(name)]
        available_system = [name for name in system if shutil.which(name)]
        for name in modules:
            package = PYTHON_DEPENDENCIES.get(name, name)
            print(f"      {'✓' if name in available_modules else '✗'} python: {package}")
            if name not in available_modules:
                missing_python.append(package)
        for name in system:
            print(f"      {'✓' if name in available_system else '✗'} system: {name}")
            if name not in available_system:
                missing_system.append(name)
        if group.get("label") == "PDF（文字型）" and native_pdfkit:
            ready = True
        elif group.get("any_tool_suffices"):
            ready = bool(available_modules or available_system)
        elif modules and system:
            ready = bool(available_modules) and bool(available_system)
        else:
            ready = bool(available_modules) if modules else bool(available_system) if system else True
        if ready:
            status = "可用"
        elif group.get("required"):
            status = "缺失且无内置回退"
        else:
            status = "可选增强缺失，存在回退或可跳过"
        print(f"      → {status}：{group['note']}\n")
    if missing_python or missing_system:
        if native_pdfkit:
            print("提示：部分可选组件缺失，但 macOS PDFKit 已可提取文字型 PDF；只有需要表格/公式增强、扫描件 OCR 或其他缺失格式时，才在用户明确同意后使用隔离环境和固定版本安装所需组件。")
        else:
            print("提示：本 Skill 不会安装任何依赖。仅在用户明确同意后，使用隔离环境和固定版本安装所需组件。")
    else:
        print("所有可选能力均已可用。")
    return 0
