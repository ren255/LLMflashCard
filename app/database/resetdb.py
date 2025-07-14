from pathlib import Path

root = Path('resources')


def reset_database():
    db_num = 0
    for db_file in root.rglob('*.db'):  # rglobで再帰的に検索[3][5]
        db_file.unlink()  # unlink()でファイル削除[3]
        db_file.touch()   # touch()で空ファイル作成
        print(db_file)
        db_num += 1
    print(f"reseted {db_num} dababases")

if __name__ == "__main__":
    print(f"resetting database in {root}")
    reset_database()
