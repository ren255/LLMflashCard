#!/usr/bin/env python3
"""
Sphinx Documentation Builder Script
====================================

Sphinxドキュメントの自動生成・ビルド・表示を行うスクリプトです。

使用方法:
    python build_docs.py [オプション]

例:
    python build_docs.py --clean --open
    python build_docs.py --full-rebuild --theme sphinx_rtd_theme
    python build_docs.py -c -o  # 短縮形
"""

import os
import sys
import subprocess
import webbrowser
import argparse
import shutil
from pathlib import Path
import time


class DocBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.docs_dir = self.project_root / "docs"
        self.source_dir = self.docs_dir / "source"
        self.build_dir = self.docs_dir / "_build"
        self.html_dir = self.build_dir / "html"
        self.text_dir = self.build_dir / "text"
        self.index_html = self.html_dir / "index.html"

    def print_info(self, message, level="INFO"):
        """情報を色付きで出力"""
        colors = {
            "INFO": "\033[94m",      # Blue
            "SUCCESS": "\033[92m",   # Green
            "WARNING": "\033[93m",   # Yellow
            "ERROR": "\033[91m",     # Red
            "RESET": "\033[0m"       # Reset
        }
        print(f"{colors.get(level, '')}{level}: {message}{colors['RESET']}")

    def check_requirements(self):
        """必要なファイル・ディレクトリの存在確認"""
        self.print_info("環境チェック中...")

        # 必要なディレクトリの作成
        self.docs_dir.mkdir(exist_ok=True)
        self.source_dir.mkdir(exist_ok=True)

        # conf.pyの存在確認
        conf_py = self.docs_dir / "conf.py"
        if not conf_py.exists():
            self.print_info("conf.pyが見つかりません。基本的なconf.pyを作成します。", "WARNING")
            self.create_basic_conf()

        # make.batの存在確認（Windows）
        make_bat = self.docs_dir / "make.bat"
        if not make_bat.exists() and sys.platform == "win32":
            self.print_info("make.batが見つかりません。基本的なmake.batを作成します。", "WARNING")
            self.create_make_bat()

        return True

    def create_basic_conf(self):
        """基本的なconf.pyを作成"""
        conf_content = '''# Configuration file for the Sphinx documentation builder.

import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------
project = 'LLM Flash Card'
copyright = '2025, Auto Generated'
author = 'Auto Generated'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = []
language = 'ja'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_permalinks_icon = '<span>#</span>'

# -- Extension configuration -------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True
jquery_use_sri = True
'''
        with open(self.docs_dir / "conf.py", "w", encoding="utf-8") as f:
            f.write(conf_content)

    def create_make_bat(self):
        """基本的なmake.batを作成"""
        make_content = '''@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=source
set BUILDDIR=_build

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://sphinx-doc.org/
	exit /b 1
)

if "%1" == "" goto help

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
'''
        with open(self.docs_dir / "make.bat", "w", encoding="utf-8") as f:
            f.write(make_content)

    def clean_build(self):
        """ビルドディレクトリをクリーンアップ"""
        self.print_info("ビルドディレクトリをクリーンアップ中...")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.print_info("クリーンアップ完了", "SUCCESS")

    def clean_source(self):
        """ソースディレクトリの自動生成ファイルをクリーンアップ"""
        self.print_info("ソースディレクトリをクリーンアップ中...")
        for rst_file in self.source_dir.glob("*.rst"):
            if rst_file.name != "index.rst":
                rst_file.unlink()
        self.print_info("ソースクリーンアップ完了", "SUCCESS")

    def run_sphinx_apidoc(self, args):
        """sphinx-apidocを実行"""
        self.print_info("API documentation生成中...")

        # 基本コマンドの構築
        cmd = [
            "sphinx-apidoc",
            "-f",  # force overwrite
            "-o", str(self.source_dir),  # output directory
            str(self.project_root),  # source directory
        ]

        # 除外パターンの追加
        excludes = [
            "setup.py",
            "test*",
            "tests*",
            ".venv*",
            ".git*",
            "_build*",
            "*.pyc",
            "__pycache__*"
        ]

        if args.exclude:
            excludes.extend(args.exclude)

        cmd.extend(excludes)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                self.print_info("API documentation生成完了", "SUCCESS")
                if args.verbose:
                    print(result.stdout)
            else:
                self.print_info(
                    f"sphinx-apidocでエラーが発生: {result.stderr}", "ERROR")
                return False
        except FileNotFoundError:
            self.print_info(
                "sphinx-apidocが見つかりません。Sphinxがインストールされているか確認してください。", "ERROR")
            return False

        return True

    def build_html(self, args):
        """HTMLドキュメントをビルド"""
        self.print_info("HTMLドキュメントをビルド中...")

        if sys.platform == "win32":
            make_cmd = [str(self.docs_dir / "make.bat"), "html"]
        else:
            make_cmd = ["make", "-C", str(self.docs_dir), "html"]

        try:
            result = subprocess.run(make_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.print_info("HTMLビルド完了", "SUCCESS")
                if args.verbose:
                    print(result.stdout)
            else:
                self.print_info(f"HTMLビルドでエラーが発生: {result.stderr}", "ERROR")
                if args.verbose:
                    print(result.stdout)
                return False
        except FileNotFoundError:
            self.print_info("makeコマンドが見つかりません。", "ERROR")
            return False

        return True

    def build_text(self, args):
        """テキストドキュメントをビルド"""
        self.print_info("テキストドキュメントをビルド中...")

        if sys.platform == "win32":
            make_cmd = [str(self.docs_dir / "make.bat"), "text"]
        else:
            make_cmd = ["make", "-C", str(self.docs_dir), "text"]

        try:
            result = subprocess.run(make_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.print_info("テキストビルド完了", "SUCCESS")
                if args.verbose:
                    print(result.stdout)
            else:
                self.print_info(f"テキストビルドでエラーが発生: {result.stderr}", "ERROR")
                if args.verbose:
                    print(result.stdout)
                return False
        except FileNotFoundError:
            self.print_info("makeコマンドが見つかりません。", "ERROR")
            return False

        return True

    def open_in_browser(self, browser_name=None):
        """ブラウザでindex.htmlを開く"""
        if not self.index_html.exists():
            self.print_info("index.htmlが見つかりません。ビルドが失敗している可能性があります。", "ERROR")
            return False

        self.print_info(f"ブラウザでドキュメントを開いています: {self.index_html}")

        try:
            if browser_name:
                browser = webbrowser.get(browser_name)
                browser.open(f"file://{self.index_html.absolute()}")
            else:
                webbrowser.open(f"file://{self.index_html.absolute()}")
            self.print_info("ブラウザで開きました", "SUCCESS")
            return True
        except Exception as e:
            self.print_info(f"ブラウザを開けませんでした: {e}", "ERROR")
            return False

    def show_info(self):
        """プロジェクト情報を表示"""
        self.print_info("=== プロジェクト情報 ===")
        print(f"プロジェクトルート: {self.project_root}")
        print(f"ドキュメントディレクトリ: {self.docs_dir}")
        print(f"ソースディレクトリ: {self.source_dir}")
        print(f"ビルドディレクトリ: {self.build_dir}")
        print(f"HTML出力: {self.html_dir}")
        print(f"テキスト出力: {self.text_dir}")
        print(f"インデックスファイル: {self.index_html}")

        # ファイル存在確認
        print("\n=== ファイル存在確認 ===")
        files_to_check = [
            ("conf.py", self.docs_dir / "conf.py"),
            ("make.bat", self.docs_dir / "make.bat"),
            ("index.html", self.index_html),
        ]

        for name, path in files_to_check:
            status = "✓" if path.exists() else "✗"
            print(f"{status} {name}: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Sphinx Documentation Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python build_docs.py                    # 基本的なビルド
  python build_docs.py --clean --open     # クリーンビルドしてブラウザで開く
  python build_docs.py -c -o              # 短縮形
  python build_docs.py --full-rebuild     # 完全な再ビルド
  python build_docs.py -f                 # 完全な再ビルド（短縮形）
  python build_docs.py --text             # テキスト形式も生成
  python build_docs.py -t                 # テキスト形式も生成（短縮形）
  python build_docs.py --info             # プロジェクト情報を表示
        """
    )

    # 基本オプション
    parser.add_argument("--clean", "-c", action="store_true",
                        help="ビルド前にビルドディレクトリをクリーンアップ")
    parser.add_argument("--clean-source", "-s", action="store_true",
                        help="ソースディレクトリの自動生成ファイルをクリーンアップ")
    parser.add_argument("--full-rebuild", "-f", action="store_true",
                        help="完全な再ビルド（--clean + --clean-source）")
    parser.add_argument("--open", "-o", action="store_true",
                        help="ビルド後にブラウザで開く")
    parser.add_argument("--browser", "-b", type=str,
                        help="使用するブラウザを指定 (chrome, firefox, edge, etc.)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="詳細な出力を表示")
    parser.add_argument("--info", "-i", action="store_true",
                        help="プロジェクト情報を表示して終了")

    # ビルド形式オプション
    parser.add_argument("--text", "-t", action="store_true",
                        help="テキスト形式のドキュメントも生成")
    parser.add_argument("--no-text", action="store_true",
                        help="テキスト形式のドキュメント生成を無効化")

    # 除外オプション
    parser.add_argument("--exclude", "-e", nargs="*", default=[],
                        help="除外するパターンを指定")

    # 実行制御オプション
    parser.add_argument("--no-apidoc", action="store_true",
                        help="sphinx-apidocをスキップ")
    parser.add_argument("--no-build", action="store_true",
                        help="HTMLビルドをスキップ")

    args = parser.parse_args()

    builder = DocBuilder()

    # 情報表示のみ
    if args.info:
        builder.show_info()
        return

    # 環境チェック
    if not builder.check_requirements():
        sys.exit(1)

    # 完全再ビルド
    if args.full_rebuild:
        args.clean = True
        args.clean_source = True

    # クリーンアップ
    if args.clean:
        builder.clean_build()

    if args.clean_source:
        builder.clean_source()

    # sphinx-apidoc実行
    if not args.no_apidoc:
        if not builder.run_sphinx_apidoc(args):
            sys.exit(1)

    # HTMLビルド
    if not args.no_build:
        if not builder.build_html(args):
            sys.exit(1)

    # テキストビルド
    if args.text and not args.no_text:
        if not builder.build_text(args):
            builder.print_info("テキストビルドでエラーが発生しましたが、処理を続行します。", "WARNING")

    # ブラウザで開く
    if args.open:
        time.sleep(1)  # ビルド完了を待つ
        builder.open_in_browser(args.browser)

    builder.print_info("すべての処理が完了しました！", "SUCCESS")


if __name__ == "__main__":
    main()