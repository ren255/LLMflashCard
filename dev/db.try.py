# %%
# from db.sqlite_utils import SQLiteManager
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import random

import db

from path import projectPath, storagePath


testDB = db.SQLiteManager(storagePath + "db\\test.sqlite")

table_schema = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT",
    "age": "INTEGER",
}

testDB.create_table("users", table_schema)


# データ挿入
testDB.insert("users", {"name": "girl", "age": random.randint(10, 80)})

# データ取得
all_users = testDB.fetch_all("users")
print(all_users)

# 条件取得
adults = testDB.fetch_where("users", "age >= ?", (18,))
print(adults)

# 更新
testDB.update("users", {"age": 16}, "name = ?", ("Peter",))

# 削除
# testDB.delete("users", "name = ?", ("Peter",))

testDB.close()


# %%
