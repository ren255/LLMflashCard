from pathlib import Path
import sys
import re


def print_tree(path: Path, prefix: str = ""):
    # ディレクトリとファイルを名前順で取得
    entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    for idx, entry in enumerate(entries):
        connector = "└── " if idx == len(entries) - 1 else "├── "
        print(prefix + connector + entry.name)
        if entry.is_dir():
            if re.match(r"^\.", entry.name):
                continue
            if re.match(r"^__", entry.name):
                continue
            # 最後の要素かどうかで接頭辞を変える
            extension = "    " if idx == len(entries) - 1 else "│   "
            print_tree(entry, prefix + extension)


if __name__ == "__main__":
    # コマンドライン引数から相対パスを取得
    if len(sys.argv) < 2:
        print("Usage: python tree.py <relative_folder_path>")
        sys.exit(1)
    folder = Path(sys.argv[1]).resolve()  # 相対パス→絶対パスに変換[10][9]
    if not folder.exists() or not folder.is_dir():
        print(f"{folder} は存在しないかディレクトリではありません")
        sys.exit(1)
    print(folder.name)
    print_tree(folder)
