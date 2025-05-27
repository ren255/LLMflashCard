from pathlib import Path
import sys
import re

def make_tree_lines(path: Path, prefix: str = "") -> list[str]:
    """ディレクトリツリーを1行ずつリストで返す"""
    lines = []
    entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    for idx, entry in enumerate(entries):
        connector = "└── " if idx == len(entries) - 1 else "├── "
        lines.append(prefix + connector + entry.name)
        if entry.is_dir():
            if re.match(r"^\.", entry.name):
                continue
            if re.match(r"^__", entry.name):
                continue
            extension = "    " if idx == len(entries) - 1 else "│   "
            lines.extend(make_tree_lines(entry, prefix + extension))
    return lines

def print_tree(path: Path):
    """ディレクトリツリーをprintする"""
    print(path.name)
    for line in make_tree_lines(path):
        print(line)

def save_tree(path: Path, out_file: Path):
    """ディレクトリツリーをファイルに保存する"""
    lines = [path.name] + make_tree_lines(path)
    tree_str = "\n".join(lines)
    out_file.parent.mkdir(exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(tree_str)
    print(f"[INFO] ツリーを {out_file} に保存しました")

if __name__ == "__main__":
    # デフォルト値
    dir_path = Path(".")
    save_file = True
    do_print = True

    args = sys.argv[1:]
    if len(args) > 0:
        dir_path = Path(args[0])
    if len(args) > 1:
        save_file = args[1] == "1"
    if len(args) > 2:
        do_print = args[2] == "1"

    dir_path = dir_path.resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"{dir_path} は存在しないかディレクトリではありません")
        sys.exit(1)

    if save_file:
        out_file = Path("tests") / f"{dir_path.name}_tree.txt"
        save_tree(dir_path, out_file)
    if do_print:
        print_tree(dir_path)
