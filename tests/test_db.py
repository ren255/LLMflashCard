import unittest
import os
import tempfile
import sys
from pathlib import Path

# Add the parent directory to sys.path to import from db module
# sys.path.append(str(Path(__file__).parent.parent))

from db import SQLiteManager


class TestSQLiteManager(unittest.TestCase):

    def setUp(self):
        """テスト前の準備 - 一時的なデータベースファイルを作成"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db_manager = SQLiteManager(self.db_path)

    def tearDown(self):
        """テスト後のクリーンアップ - データベースファイルを削除"""
        self.db_manager.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_create_table(self):
        """テーブル作成のテスト"""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "age": "INTEGER",
            "email": "TEXT UNIQUE",
        }

        # テーブル作成
        self.db_manager.create_table("users", columns)

        # テーブルが作成されたか確認
        cursor = self.db_manager.cursor
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "users")

    def test_insert_single_record(self):
        """単一レコード挿入のテスト"""
        # テーブル作成
        columns = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "age": "INTEGER"}
        self.db_manager.create_table("test_users", columns)

        # データ挿入
        data = {"name": "Alice", "age": 25}
        self.db_manager.insert("test_users", data)

        # データが挿入されたか確認
        all_data = self.db_manager.fetch_all("test_users")
        self.assertEqual(len(all_data), 1)
        self.assertEqual(all_data[0]["name"], "Alice")
        self.assertEqual(all_data[0]["age"], 25)

    def test_insert_multiple_records(self):
        """複数レコード挿入のテスト"""
        columns = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "score": "REAL"}
        self.db_manager.create_table("students", columns)

        # 複数データ挿入
        students = [
            {"name": "Bob", "score": 85.5},
            {"name": "Carol", "score": 92.0},
            {"name": "Dave", "score": 78.5},
        ]

        for student in students:
            self.db_manager.insert("students", student)

        # データ数確認
        all_students = self.db_manager.fetch_all("students")
        self.assertEqual(len(all_students), 3)

    def test_fetch_all(self):
        """全データ取得のテスト"""
        columns = {"id": "INTEGER PRIMARY KEY", "product": "TEXT", "price": "REAL"}
        self.db_manager.create_table("products", columns)

        # テストデータ挿入
        products = [
            {"product": "Laptop", "price": 999.99},
            {"product": "Mouse", "price": 25.50},
            {"product": "Keyboard", "price": 75.00},
        ]

        for product in products:
            self.db_manager.insert("products", product)

        # 全データ取得
        all_products = self.db_manager.fetch_all("products")
        self.assertEqual(len(all_products), 3)

        # データの内容確認
        product_names = [p["product"] for p in all_products]
        self.assertIn("Laptop", product_names)
        self.assertIn("Mouse", product_names)
        self.assertIn("Keyboard", product_names)

    def test_fetch_where(self):
        """条件付きデータ取得のテスト"""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "age": "INTEGER",
            "city": "TEXT",
        }
        self.db_manager.create_table("people", columns)

        # テストデータ挿入
        people = [
            {"name": "John", "age": 25, "city": "Tokyo"},
            {"name": "Jane", "age": 30, "city": "Osaka"},
            {"name": "Mike", "age": 25, "city": "Tokyo"},
            {"name": "Sara", "age": 35, "city": "Kyoto"},
        ]

        for person in people:
            self.db_manager.insert("people", person)

        # 年齢が25の人を取得
        young_people = self.db_manager.fetch_where("people", "age = ?", (25,))
        self.assertEqual(len(young_people), 2)

        # 東京住みの人を取得
        tokyo_people = self.db_manager.fetch_where("people", "city = ?", ("Tokyo",))
        self.assertEqual(len(tokyo_people), 2)

        # 年齢が30以上の人を取得
        older_people = self.db_manager.fetch_where("people", "age >= ?", (30,))
        self.assertEqual(len(older_people), 2)

        # 複数条件
        specific_people = self.db_manager.fetch_where(
            "people", "age = ? AND city = ?", (25, "Tokyo")
        )
        self.assertEqual(len(specific_people), 2)

    def test_update(self):
        """データ更新のテスト"""
        columns = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "status": "TEXT"}
        self.db_manager.create_table("tasks", columns)

        # 初期データ挿入
        tasks = [
            {"name": "Task 1", "status": "pending"},
            {"name": "Task 2", "status": "pending"},
            {"name": "Task 3", "status": "completed"},
        ]

        for task in tasks:
            self.db_manager.insert("tasks", task)

        # 特定のタスクを完了に更新
        self.db_manager.update(
            "tasks", {"status": "completed"}, "name = ?", ("Task 1",)
        )

        # 更新されたか確認
        completed_tasks = self.db_manager.fetch_where(
            "tasks", "status = ?", ("completed",)
        )
        self.assertEqual(len(completed_tasks), 2)

        # Task 1が更新されたか確認
        task1 = self.db_manager.fetch_where("tasks", "name = ?", ("Task 1",))
        self.assertEqual(task1[0]["status"], "completed")

        # 複数フィールド更新
        self.db_manager.update(
            "tasks", {"name": "Updated Task", "status": "in_progress"}, "id = ?", (2,)
        )
        updated_task = self.db_manager.fetch_where("tasks", "id = ?", (2,))
        self.assertEqual(updated_task[0]["name"], "Updated Task")
        self.assertEqual(updated_task[0]["status"], "in_progress")

    def test_delete(self):
        """データ削除のテスト"""
        columns = {"id": "INTEGER PRIMARY KEY", "item": "TEXT", "category": "TEXT"}
        self.db_manager.create_table("inventory", columns)

        # テストデータ挿入
        items = [
            {"item": "Apple", "category": "fruit"},
            {"item": "Banana", "category": "fruit"},
            {"item": "Carrot", "category": "vegetable"},
            {"item": "Broccoli", "category": "vegetable"},
        ]

        for item in items:
            self.db_manager.insert("inventory", item)

        # 特定のアイテムを削除
        self.db_manager.delete("inventory", "item = ?", ("Apple",))

        # 削除されたか確認
        remaining_items = self.db_manager.fetch_all("inventory")
        self.assertEqual(len(remaining_items), 3)

        apple_items = self.db_manager.fetch_where("inventory", "item = ?", ("Apple",))
        self.assertEqual(len(apple_items), 0)

        # カテゴリごと削除
        self.db_manager.delete("inventory", "category = ?", ("fruit",))
        remaining_after_category_delete = self.db_manager.fetch_all("inventory")
        self.assertEqual(len(remaining_after_category_delete), 2)

        # 残っているのは野菜のみか確認
        vegetables = self.db_manager.fetch_where(
            "inventory", "category = ?", ("vegetable",)
        )
        self.assertEqual(len(vegetables), 2)

    def test_empty_table_operations(self):
        """空のテーブルに対する操作のテスト"""
        columns = {"id": "INTEGER PRIMARY KEY", "data": "TEXT"}
        self.db_manager.create_table("empty_table", columns)

        # 空のテーブルから全データ取得
        empty_result = self.db_manager.fetch_all("empty_table")
        self.assertEqual(len(empty_result), 0)

        # 空のテーブルで条件検索
        empty_search = self.db_manager.fetch_where("empty_table", "id = ?", (1,))
        self.assertEqual(len(empty_search), 0)

    def test_data_types(self):
        """様々なデータ型のテスト"""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "text_field": "TEXT",
            "int_field": "INTEGER",
            "real_field": "REAL",
            "blob_field": "BLOB",
        }
        self.db_manager.create_table("data_types", columns)

        # 様々な型のデータを挿入
        test_data = {
            "text_field": "Hello, World!",
            "int_field": 42,
            "real_field": 3.14159,
            "blob_field": b"binary data",
        }

        self.db_manager.insert("data_types", test_data)

        # データ取得して型確認
        result = self.db_manager.fetch_all("data_types")
        self.assertEqual(len(result), 1)

        record = result[0]
        self.assertEqual(record["text_field"], "Hello, World!")
        self.assertEqual(record["int_field"], 42)
        self.assertAlmostEqual(record["real_field"], 3.14159)
        self.assertEqual(record["blob_field"], b"binary data")

    def test_duplicate_table_creation(self):
        """同じテーブルを複数回作成するテスト（IF NOT EXISTS動作確認）"""
        columns = {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}

        # 最初のテーブル作成
        self.db_manager.create_table("duplicate_test", columns)
        self.db_manager.insert("duplicate_test", {"name": "Test Record"})

        # 同じテーブルを再作成（エラーにならないはず）
        self.db_manager.create_table("duplicate_test", columns)

        # データが保持されているか確認
        data = self.db_manager.fetch_all("duplicate_test")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Test Record")


def run_all_tests():
    """全てのテストを実行する関数"""
    unittest.main()


if __name__ == "__main__":
    # テスト実行
    print("SQLiteManager のテストを開始します...")
    print("=" * 50)

    # テストスイート作成
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSQLiteManager)

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果表示
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ 全てのテストが成功しました！")
    else:
        print("❌ いくつかのテストが失敗しました。")
        print(f"失敗: {len(result.failures)}, エラー: {len(result.errors)}")

    print(f"実行したテスト数: {result.testsRun}")
