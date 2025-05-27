from pathlib import Path
import sys
import re
import argparse
import threading
import time
from typing import Dict, Tuple

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

class ProgressIndicator:
    def __init__(self, message: str = "計算中"):
        self.message = message
        self.running = False
        self.thread = None
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        # 進行状況表示をクリア
        print(f"\r{' ' * 50}\r", end='', flush=True)
        
    def _animate(self):
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        while self.running:
            print(f"\r{spinner[i % len(spinner)]} {self.message}...", end='', flush=True)
            i += 1
            time.sleep(0.1)

def get_directory_size_with_progress(path: Path) -> int:
    """ディレクトリ内のすべてのファイルサイズの合計を取得（プログレスバー付き）"""
    progress = ProgressIndicator(f"サイズ計算中: {path.name}")
    progress.start()
    
    try:
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
        return total_size
    finally:
        progress.stop()

def get_directory_size(path: Path) -> int:
    """ディレクトリ内のすべてのファイルサイズの合計を取得"""
    total_size = 0
    try:
        for item in path.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total_size

def get_file_size(path: Path) -> int:
    """ファイルサイズを取得"""
    try:
        return path.stat().st_size
    except (OSError, PermissionError):
        return 0

def collect_size_info(path: Path, max_files: int = 10, show_size: bool = False) -> Dict[Path, int]:
    """サイズ情報を事前に収集"""
    if not show_size:
        return {}
    
    size_info = {}
    
    def collect_recursive(current_path: Path, level: int = 0):
        try:
            entries = list(current_path.iterdir())
        except (OSError, PermissionError):
            return
        
        # 隠しファイル・ディレクトリと__で始まるものを除外
        filtered_entries = []
        for entry in entries:
            if re.match(r"^\.", entry.name) or re.match(r"^__", entry.name):
                continue
            filtered_entries.append(entry)
        
        # ファイル数制限適用
        if len(filtered_entries) > max_files:
            dirs = [e for e in filtered_entries if e.is_dir()]
            files = [e for e in filtered_entries if e.is_file()]
            
            if len(dirs) <= max_files:
                remaining_slots = max_files - len(dirs)
                selected_entries = dirs + files[:remaining_slots]
            else:
                selected_entries = dirs[:max_files]
            
            filtered_entries = selected_entries
        
        for entry in filtered_entries:
            if entry.is_dir():
                size_info[entry] = get_directory_size(entry)
                collect_recursive(entry, level + 1)
            else:
                size_info[entry] = get_file_size(entry)
    
    # ルートディレクトリのサイズ計算（プログレスバー付き）
    if path.is_dir():
        size_info[path] = get_directory_size_with_progress(path)
        collect_recursive(path)
    else:
        size_info[path] = get_file_size(path)
    
    return size_info

def calculate_max_width(lines: list[str]) -> int:
    """ツリー部分の最大幅を計算（サイズ表示のための位置決め用）"""
    max_width = 0
    for line in lines:
        # サイズ情報を除いた純粋なツリー部分の幅を計算
        tree_part = line.split(' [')[0] if ' [' in line else line
        max_width = max(max_width, len(tree_part))
    return max_width

def make_tree_lines(path: Path, prefix: str = "", max_files: int = 10, 
                   size_info: Dict[Path, int] | None = None, show_size: bool = False) -> list[str]:
    """ディレクトリツリーを1行ずつリストで返す"""
    lines = []
    
    try:
        entries = list(path.iterdir())
    except (OSError, PermissionError):
        return [prefix + "├── [Permission Denied]"]
    
    # 隠しファイル・ディレクトリと__で始まるものを除外
    filtered_entries = []
    for entry in entries:
        if re.match(r"^\.", entry.name) or re.match(r"^__", entry.name):
            continue
        filtered_entries.append(entry)
    
    # ファイル数が制限を超える場合は制限する
    if len(filtered_entries) > max_files:
        dirs = [e for e in filtered_entries if e.is_dir()]
        files = [e for e in filtered_entries if e.is_file()]
        
        if len(dirs) <= max_files:
            remaining_slots = max_files - len(dirs)
            selected_entries = dirs + files[:remaining_slots]
            omitted_count = len(filtered_entries) - len(selected_entries)
        else:
            selected_entries = dirs[:max_files]
            omitted_count = len(filtered_entries) - len(selected_entries)
        
        filtered_entries = selected_entries
    else:
        omitted_count = 0
    
    # ソート（ディレクトリ優先、その後名前順）
    sorted_entries = sorted(filtered_entries, key=lambda x: (not x.is_dir(), x.name.lower()))
    
    for idx, entry in enumerate(sorted_entries):
        is_last = (idx == len(sorted_entries) - 1) and (omitted_count == 0)
        connector = "└── " if is_last else "├── "
        
        line = prefix + connector + entry.name
        
        # サイズ情報を追加（後で位置調整）
        if show_size and size_info and entry in size_info:
            size_str = f" [{format_size(size_info[entry])}]"
            line += size_str
        
        lines.append(line)
        
        if entry.is_dir():
            extension = "    " if is_last and omitted_count == 0 else "│   "
            lines.extend(make_tree_lines(entry, prefix + extension, max_files, size_info, show_size))
    
    # 省略されたファイルがある場合の表示
    if omitted_count > 0:
        lines.append(prefix + f"└── ... and {omitted_count} more items")
    
    return lines

def align_size_display(lines: list[str], target_width: int = 80) -> list[str]:
    """サイズ表示を右揃えにして見やすく整列"""
    if not lines:
        return lines
    
    aligned_lines = []
    for line in lines:
        if ' [' in line and line.endswith(']'):
            # ツリー部分とサイズ部分を分離
            tree_part, size_part = line.rsplit(' [', 1)
            size_part = '[' + size_part
            
            # 適切な位置に配置
            tree_len = len(tree_part)
            if tree_len < target_width - len(size_part) - 1:
                spaces_needed = target_width - tree_len - len(size_part)
                aligned_line = tree_part + ' ' * spaces_needed + size_part
            else:
                aligned_line = tree_part + ' ' + size_part
            
            aligned_lines.append(aligned_line)
        else:
            aligned_lines.append(line)
    
    return aligned_lines

def print_tree(path: Path, max_files: int = 10, show_size: bool = False):
    """ディレクトリツリーをprintする"""
    # サイズ情報を事前収集
    size_info = collect_size_info(path, max_files, show_size) if show_size else {}
    
    # ルートの表示
    root_line = path.name
    if show_size and path in size_info:
        root_line += f" [{format_size(size_info[path])}]"
    print(root_line)
    
    # ツリーの生成
    tree_lines = make_tree_lines(path, max_files=max_files, size_info=size_info, show_size=show_size)
    
    # サイズ表示がある場合は位置を調整
    if show_size:
        tree_lines = align_size_display(tree_lines)
    
    for line in tree_lines:
        print(line)

def save_tree(path: Path, out_file: Path, max_files: int = 10, show_size: bool = False):
    """ディレクトリツリーをファイルに保存する"""
    # サイズ情報を事前収集
    size_info = collect_size_info(path, max_files, show_size) if show_size else {}
    
    # ルートの表示
    root_line = path.name
    if show_size and path in size_info:
        root_line += f" [{format_size(size_info[path])}]"
    
    # ツリーの生成
    tree_lines = make_tree_lines(path, max_files=max_files, size_info=size_info, show_size=show_size)
    
    # サイズ表示がある場合は位置を調整
    if show_size:
        tree_lines = align_size_display(tree_lines)
    
    lines = [root_line] + tree_lines
    tree_str = "\n".join(lines)
    
    out_file.parent.mkdir(exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(tree_str)
    print(f"[INFO] ツリーを {out_file} に保存しました")

def main():
    parser = argparse.ArgumentParser(
        description="ディレクトリツリーを表示・保存するツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python tree.py                          # カレントディレクトリを表示・保存
  python tree.py /path/to/dir             # 指定ディレクトリを表示・保存
  python tree.py -s                       # 保存のみ（表示しない）
  python tree.py -o                       # 表示のみ（保存しない）
  python tree.py --show-size              # ファイルサイズを表示
  python tree.py --max-files 20           # 最大表示ファイル数を20に設定
  python tree.py --show-size --max-files 15  # サイズ表示付きで最大15ファイル
        """
    )
    
    parser.add_argument(
        "path", 
        nargs="?", 
        default=".", 
        help="対象ディレクトリのパス（デフォルト: 現在のディレクトリ）"
    )
    
    parser.add_argument(
        "-s", "--save-only",
        action="store_true",
        help="ファイルに保存のみ行う（画面表示しない）"
    )
    
    parser.add_argument(
        "-o", "--output-only", 
        action="store_true",
        help="画面表示のみ行う（ファイル保存しない）"
    )
    
    parser.add_argument(
        "--show-size",
        action="store_true",
        help="ファイル・ディレクトリのサイズを表示（デフォルト: 無効）"
    )
    
    parser.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="各ディレクトリで表示する最大ファイル数（デフォルト: 10）"
    )
    
    args = parser.parse_args()
    
    # パスの検証
    dir_path = Path(args.path).resolve()
    if not dir_path.exists():
        print(f"エラー: {dir_path} は存在しません")
        sys.exit(1)
    
    # 動作の決定
    do_save = not args.output_only
    do_print = not args.save_only
    
    # 両方無効の場合は警告
    if not do_save and not do_print:
        print("警告: -s と -o の両方が指定されているため、何も実行されません")
        return
    
    # 実行
    if do_save:
        out_file = Path("tests") / f"{dir_path.name}_tree.txt"
        save_tree(dir_path, out_file, args.max_files, args.show_size)
    
    if do_print:
        print_tree(dir_path, args.max_files, args.show_size)

if __name__ == "__main__":
    main()