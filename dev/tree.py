from pathlib import Path
import sys
import re
import argparse
import time
from typing import List, Tuple, Optional


class FileUtils:
    """File and directory utility functions"""
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """バイト数を人間が読みやすい形式に変換"""
        if size_bytes == 0:
            return "0B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)}B"
        else:
            return f"{size:.1f}{units[unit_index]}"
    
    @staticmethod
    def get_file_size(path: Path) -> int:
        """ファイルサイズを取得"""
        try:
            return path.stat().st_size
        except (OSError, PermissionError):
            return 0
    
    @staticmethod
    def get_directory_size(path: Path, progress_bar: Optional['ProgressBar'] = None) -> int:
        """ディレクトリ内のすべてのファイルサイズの合計を取得"""
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        if progress_bar:
                            progress_bar.update(1)
                    except (OSError, PermissionError):
                        if progress_bar:
                            progress_bar.update(1)
        except (OSError, PermissionError):
            pass
        return total_size
    
    @staticmethod
    def count_files_in_directory(path: Path) -> int:
        """ディレクトリ内のファイル総数をカウント（プログレスバー用）"""
        count = 0
        print("file count: ", end="", flush=True)
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    count += 1
                    if count % 100 == 0:  # 100ファイルごとに更新
                        print(f"\rfile count: {count}", end="", flush=True)
        except (OSError, PermissionError):
            pass
        print(f"\rfile count: {count}")  # 最終結果を改行付きで表示
        return count


class ProgressBar:
    """シンプルなプログレスバー"""
    
    def __init__(self, total: int, prefix: str = "Processing", width: int = 40):
        self.total = total
        self.current = 0
        self.prefix = prefix
        self.width = width
        self.start_time = time.time()
        self.finished = False

    def update(self, increment: int = 1):
        """プログレスを更新"""
        if self.finished:
            return  # すでに終了していれば何もしない
        self.current += increment
        if self.current >= self.total:
            self.current = self.total
            self._print_progress()
            self.finished = True
        else:
            self._print_progress()

    def _print_progress(self):
        """プログレスバーを表示"""
        if self.total == 0 or self.finished:
            return

        percent = min(100, (self.current / self.total) * 100)
        filled = int(self.width * self.current // self.total)
        bar = '█' * filled + '-' * (self.width - filled)

        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: --s"

        print(f'\r{self.prefix}: |{bar}| {percent:.1f}% ({self.current}/{self.total}) {eta_str}', end='', flush=True)

        if self.current >= self.total:
            print()  # 改行


class TreeOptions:
    """Tree generation options"""
    
    def __init__(self, path: Path, max_files: int = 10, show_size: bool = True, 
                 align_size: bool = False, include_hidden: bool = False,
                 output_file: Optional[str] = None, do_save: bool = True, 
                 do_print: bool = True, exclude_patterns: Optional[List[str]] = None):
        self.path = path
        self.max_files = max_files
        self.show_size = show_size
        self.align_size = align_size
        self.include_hidden = include_hidden
        self.output_file = output_file
        self.do_save = do_save
        self.do_print = do_print
        self.exclude_patterns = exclude_patterns or []
    
    def validate(self) -> bool:
        """オプションの妥当性をチェック"""
        if not self.path.exists():
            print(f"エラー: {self.path} は存在しません")
            return False
        
        if self.max_files < 1:
            print("エラー: --max-files は1以上である必要があります")
            return False
        
        if not self.do_save and not self.do_print:
            print("警告: 保存も表示も無効のため、何も実行されません")
            return False
        
        return True


class DirectoryTreeGenerator:
    """Directory tree generation logic"""
    
    def __init__(self, options: TreeOptions):
        self.options = options
        self.file_utils = FileUtils()
    
    def should_include_entry(self, entry: Path) -> bool:
        """エントリを含めるべきかチェック"""
        return self.should_include_directory(entry) if entry.is_dir() else True
    
    def should_include_directory(self, dir_path: Path) -> bool:
        """ディレクトリが対象であるかを確認する"""
        # --hiddenオプションが有効な場合は常にTrue
        if self.options.include_hidden:
            return True
        
        # 隠しディレクトリ・特殊ディレクトリをチェック
        name = dir_path.name
        
        # . で始まる隠しディレクトリ
        if name.startswith('.'):
            return False
        
        # __ で始まる特殊ディレクトリ（__pycache__等）
        if name.startswith('__'):
            return False
        
        # _ で始まるディレクトリ
        if name.startswith('_'):
            return False
        
        return True
    
    def calculate_max_name_length(self, path: Path, prefix: str = "", 
                                 depth: int = 0, max_depth: int = 3) -> int:
        """ツリー表示で必要な最大の名前長を計算（深い階層は制限）"""
        max_length = len(prefix) + len(path.name)
        
        if depth >= max_depth:
            return max_length
        
        try:
            entries = list(path.iterdir())
        except (OSError, PermissionError):
            return max_length
        
        # フィルタリング
        filtered_entries = [e for e in entries if self.should_include_entry(e)]
        
        # ファイル数制限の適用
        if len(filtered_entries) > self.options.max_files:
            dirs = [e for e in filtered_entries if e.is_dir()]
            files = [e for e in filtered_entries if e.is_file()]
            
            if len(dirs) <= self.options.max_files:
                remaining_slots = self.options.max_files - len(dirs)
                selected_entries = dirs + files[:remaining_slots]
            else:
                selected_entries = dirs[:self.options.max_files]
            
            filtered_entries = selected_entries
        
        sorted_entries = sorted(filtered_entries, key=lambda x: (not x.is_dir(), x.name.lower()))
        
        for idx, entry in enumerate(sorted_entries):
            is_last = (idx == len(sorted_entries) - 1)
            connector = "└── " if is_last else "├── "
            current_prefix = prefix + connector
            current_length = len(current_prefix) + len(entry.name)
            max_length = max(max_length, current_length)
            
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                child_length = self.calculate_max_name_length(
                    entry, prefix + extension, depth + 1, max_depth
                )
                max_length = max(max_length, child_length)
        
        return max_length
    
    def make_tree_lines(self, path: Path, prefix: str = "", 
                       align_width: Optional[int] = None, 
                       progress_bar: Optional[ProgressBar] = None, 
                       is_root: bool = False) -> List[str]:
        """ディレクトリツリーを1行ずつリストで返す"""
        lines = []
        
        try:
            entries = list(path.iterdir())
        except (OSError, PermissionError):
            line = prefix + "├── [Permission Denied]"
            if self.options.show_size and align_width:
                line = line.ljust(align_width) + " [N/A]"
            return [line]
        
        # 全てのエントリを取得（ファイルは従来通り、ディレクトリは表示するが中身を制御）
        all_entries = []
        for entry in entries:
            if entry.is_file():
                # ファイルは従来の判定
                if self.should_include_entry(entry):
                    all_entries.append(entry)
            else:
                # ディレクトリは常に表示対象に含める
                all_entries.append(entry)
        
        # ファイル数が制限を超える場合は制限する（ただし、ルートディレクトリは制限しない）
        if not is_root and len(all_entries) > self.options.max_files:
            dirs = [e for e in all_entries if e.is_dir()]
            files = [e for e in all_entries if e.is_file()]
            
            if len(dirs) <= self.options.max_files:
                remaining_slots = self.options.max_files - len(dirs)
                selected_entries = dirs + files[:remaining_slots]
                omitted_count = len(all_entries) - len(selected_entries)
            else:
                selected_entries = dirs[:self.options.max_files]
                omitted_count = len(all_entries) - len(selected_entries)
            
            filtered_entries = selected_entries
        else:
            filtered_entries = all_entries
            omitted_count = 0
        
        # ソート（ディレクトリ優先、その後名前順）
        sorted_entries = sorted(filtered_entries, key=lambda x: (not x.is_dir(), x.name.lower()))
        
        for idx, entry in enumerate(sorted_entries):
            is_last = (idx == len(sorted_entries) - 1) and (omitted_count == 0)
            connector = "└── " if is_last else "├── "
            
            line = prefix + connector + entry.name
            
            # サイズ情報を追加
            if self.options.show_size:
                if entry.is_dir():
                    # 全ディレクトリのサイズを計算
                    size = self.file_utils.get_directory_size(entry, progress_bar)
                else:
                    size = self.file_utils.get_file_size(entry)
                    if progress_bar:
                        progress_bar.update(1)
                
                size_str = f" [{self.file_utils.format_size(size)}]"
                
                if align_width:
                    line = line.ljust(align_width) + size_str
                else:
                    line += size_str
            
            lines.append(line)
            
            # ディレクトリの場合、対象ディレクトリのみ中身を展開
            if entry.is_dir() and self.should_include_directory(entry):
                extension = "    " if is_last and omitted_count == 0 else "│   "
                lines.extend(self.make_tree_lines(
                    entry, prefix + extension, align_width, progress_bar, False
                ))
        
        # 省略されたファイルがある場合の表示
        if omitted_count > 0:
            line = prefix + f"└── ... and {omitted_count} more items"
            if self.options.show_size and align_width:
                line = line.ljust(align_width) + " [N/A]"
            lines.append(line)
        
        return lines
    
    def generate_tree_lines(self) -> Tuple[str, List[str]]:
        """ツリーを生成して（ルート行, 子行のリスト）を返す"""
        path = self.options.path
        
        # プログレスバーの初期化（サイズ計算時のみ）
        progress_bar = None
        if self.options.show_size:
            total_files = self.file_utils.count_files_in_directory(path)
            if total_files > 0:
                progress_bar = ProgressBar(total_files, "サイズ計算中")
        
        # ルートの処理
        root_line = path.name
        if self.options.show_size:
            if path.is_dir():
                total_size = self.file_utils.get_directory_size(path, progress_bar)
            else:
                total_size = self.file_utils.get_file_size(path)
                if progress_bar:
                    progress_bar.update(1)
            size_str = f" [{self.file_utils.format_size(total_size)}]"
            
            if self.options.align_size:
                max_width = self.calculate_max_name_length(path)
                root_line = root_line.ljust(max_width) + size_str
            else:
                root_line += size_str
        
        # プログレスバー完了
        if progress_bar:
            progress_bar.current = progress_bar.total
            progress_bar._print_progress()
            print()  # 改行
        
        # ツリーの生成
        align_width = self.calculate_max_name_length(path) if self.options.align_size else None
        child_lines = self.make_tree_lines(
            path, align_width=align_width, progress_bar=progress_bar, is_root=True
        )
        
        return root_line, child_lines


class TreePrinter:
    """Tree output handling"""
    
    def __init__(self, generator: DirectoryTreeGenerator):
        self.generator = generator
    
    def print_tree(self):
        """ディレクトリツリーをprintする"""
        root_line, child_lines = self.generator.generate_tree_lines()
        print(root_line)
        for line in child_lines:
            print(line)
    
    def save_tree(self, out_file: Path):
        """ディレクトリツリーをファイルに保存する"""
        root_line, child_lines = self.generator.generate_tree_lines()
        lines = [root_line] + child_lines
        tree_str = "\n".join(lines)
        
        out_file.parent.mkdir(exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(tree_str)
        print(f"[INFO] ツリーを {out_file} に保存しました")


class ArgumentParser:
    """Command line argument parsing"""
    
    @staticmethod
    def setup_parser() -> argparse.ArgumentParser:
        """引数パーサーをセットアップする"""
        parser = argparse.ArgumentParser(
            description="ディレクトリツリーを表示・保存するツール",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  python tree.py                        # カレントディレクトリを表示・保存
  python tree.py /path/to/dir           # 指定ディレクトリを表示・保存
  python tree.py --save-only            # ファイル保存のみ
  python tree.py --print-only           # 画面表示のみ
  python tree.py --align                # サイズを縦に揃えて表示
  python tree.py --no-size              # サイズ表示なし
  python tree.py --max-files 20         # 最大表示ファイル数を20に設定
  python tree.py --output custom.txt    # 出力ファイル名を指定
  python tree.py --hidden               # 隠しファイルも表示
  python tree.py --exclude "*.pyc" "*.log"  # 特定パターンを除外
            """
        )

        # 基本引数
        parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="対象ディレクトリのパス（デフォルト: 現在のディレクトリ）"
        )

        # 動作モード
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            "--save-only", "-s",
            action="store_true",
            help="ファイルに保存のみ実行"
        )
        mode_group.add_argument(
            "--print-only", "-p",
            action="store_true",
            help="画面表示のみ実行"
        )

        # 表示・動作オプション
        parser.add_argument(
            "-b", "--basic",
            action="store_true",
            help="サイズ計算を行わない（高速表示）"
        )
        
        parser.add_argument(
            "--align", "-a",
            action="store_true",
            help="ファイルサイズを縦に揃えて表示"
        )
        
        parser.add_argument(
            "--no-size",
            action="store_true",
            help="ファイルサイズを表示しない"
        )
        
        parser.add_argument(
            "--hidden",
            action="store_true",
            help="隠しファイル・ディレクトリも表示"
        )

        # 制限・フィルタリング
        parser.add_argument(
            "--max-files", "-m",
            type=int,
            default=10,
            help="各ディレクトリで表示する最大ファイル数（デフォルト: 10）"
        )
        
        parser.add_argument(
            "--exclude", "-e",
            action="append",
            help="除外するファイルパターン（複数指定可能）"
        )

        # 出力設定
        parser.add_argument(
            "--output", "-o",
            help="出力ファイル名（デフォルト: {dirname}_tree.txt）"
        )

        return parser
    
    @staticmethod
    def process_args(args) -> TreeOptions:
        """コマンドライン引数を処理してTreeOptionsを返す"""
        path = Path(args.path).resolve()
        
        # 動作モードの決定
        if args.save_only:
            do_save, do_print = True, False
        elif args.print_only:
            do_save, do_print = False, True
        else:
            do_save, do_print = True, True
        
        return TreeOptions(
            path=path,
            max_files=args.max_files,
            show_size=not args.basic,  # -b オプションでサイズ計算無効
            align_size=args.align,
            include_hidden=args.hidden,
            output_file=args.output,
            do_save=do_save,
            do_print=do_print,
            exclude_patterns=args.exclude or []
        )


class TreeApplication:
    """Main application class"""
    
    def __init__(self):
        self.parser = ArgumentParser.setup_parser()
    
    def run(self):
        """アプリケーションを実行"""
        args = self.parser.parse_args()
        options = ArgumentParser.process_args(args)
        
        # オプション検証
        if not options.validate():
            sys.exit(1)
        
        # ツリー生成器とプリンターを作成
        generator = DirectoryTreeGenerator(options)
        printer = TreePrinter(generator)
        
        # 実行
        if options.do_save:
            if options.output_file:
                out_file = Path(options.output_file)
            else:
                out_file = Path("dev/tree") / f"{options.path.name}_tree.txt"
            printer.save_tree(out_file)
        
        if options.do_print:
            printer.print_tree()


def main():
    app = TreeApplication()
    app.run()


if __name__ == "__main__":
    main()