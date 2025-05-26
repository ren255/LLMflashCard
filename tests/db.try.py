# %%
# from db.sqlite_utils import SQLiteManager
# import db
import random

import db

testDB = db.SQLiteManager("my_database.db")

table_schema = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT",
    "age": "INTEGER",
}

testDB.create_table("users", table_schema)


# データ挿入
testDB.insert("users", {"name": "Peter", "age": random.randint(10, 80)})

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
