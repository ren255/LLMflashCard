from pathlib import Path
from database_manager import DatabaseManager, TableManager


def setup_database():
    """データベースとテーブルを初期化"""
    db_path = Path("resources/db.db")
    
    # resourcesディレクトリが存在しない場合は作成
    db_path.parent.mkdir(exist_ok=True)
    
    with DatabaseManager(db_path) as db_manager:
        table_manager = TableManager(db_manager)
        
        # usersテーブル作成
        create_users_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # postsテーブル作成（JOINのサンプル用）
        create_posts_table_sql = """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        
        # テーブル作成実行
        table_manager.execute_raw(create_users_table_sql)
        table_manager.execute_raw(create_posts_table_sql)
        
        print("✅ データベースとテーブルが作成されました")


def sample_operations():
    """サンプル操作の実行"""
    db_path = Path("resources/db.db")
    
    with DatabaseManager(db_path) as db_manager:
        table_manager = TableManager(db_manager)
        
        print("\n=== データベース情報 ===")
        # 全テーブル名取得
        tables = db_manager.get_all_table_names()
        print(f"テーブル一覧: {tables}")
        
        # usersテーブルのスキーマ取得
        schema = table_manager.get_table_schema("users")
        print(f"usersテーブルスキーマ: {schema}")
        
        # カラム名取得
        columns = table_manager.get_column_names("users")
        print(f"usersテーブルカラム: {columns}")
        
        print("\n=== データ挿入 ===")
        # ユーザー挿入
        user1_id = table_manager.insert("users", {
            "name": "Alice",
            "email": "alice@example.com",
            "age": 30
        })
        print(f"Alice挿入完了 ID: {user1_id}")
        
        user2_id = table_manager.insert("users", {
            "name": "Bob",
            "email": "bob@example.com", 
            "age": 25
        })
        print(f"Bob挿入完了 ID: {user2_id}")
        
        # 一括挿入
        users_data = [
            {"name": "Charlie", "email": "charlie@example.com", "age": 35},
            {"name": "Diana", "email": "diana@example.com", "age": 28}
        ]
        table_manager.bulk_insert("users", users_data)
        print("一括挿入完了")
        
        # 投稿データ挿入
        table_manager.insert("posts", {
            "user_id": user1_id,
            "title": "Hello World",
            "content": "This is my first post!"
        })
        
        table_manager.insert("posts", {
            "user_id": user2_id,
            "title": "Python Tips",
            "content": "Here are some useful Python tips..."
        })
        
        print("\n=== データ検索 ===")
        # 全ユーザー取得
        all_users = table_manager.select("users")
        print(f"全ユーザー数: {len(all_users)}")
        for user in all_users:
            print(f"  - {user['name']} ({user['email']}) - {user['age']}歳")
        
        # 条件検索
        young_users = table_manager.select("users", {"age": 25})
        print(f"\n25歳のユーザー: {len(young_users)}人")
        for user in young_users:
            print(f"  - {user['name']}")
        
        # レコード数取得
        total_users = table_manager.count("users")
        users_over_30 = table_manager.count("users", {"age": 35})
        print(f"\n総ユーザー数: {total_users}")
        print(f"35歳のユーザー数: {users_over_30}")
        
        # 存在確認
        alice_exists = table_manager.exists("users", {"name": "Alice"})
        print(f"Aliceが存在するか: {alice_exists}")
        
        print("\n=== データ更新 ===")
        # Aliceの年齢を更新
        updated_count = table_manager.update(
            "users", 
            {"age": 31}, 
            {"name": "Alice"}
        )
        print(f"更新されたレコード数: {updated_count}")
        
        # 更新後の確認
        alice = table_manager.select("users", {"name": "Alice"})[0]
        print(f"更新後のAlice: {alice['name']} - {alice['age']}歳")
        
        print("\n=== 複数テーブル操作（JOIN） ===")
        # ユーザーと投稿をJOIN
        join_result = table_manager.execute_raw("""
            SELECT u.name, u.email, p.title, p.content, p.created_at
            FROM users u
            JOIN posts p ON u.id = p.user_id
            ORDER BY p.created_at DESC
        """)
        
        print("ユーザーと投稿の一覧:")
        for row in join_result:
            print(f"  - {row['name']}: '{row['title']}'")
        
        print("\n=== データ削除 ===")
        # 特定ユーザーの投稿を削除
        deleted_posts = table_manager.delete("posts", {"user_id": user2_id})
        print(f"削除された投稿数: {deleted_posts}")
        
        # ユーザー削除
        deleted_users = table_manager.delete("users", {"name": "Bob"})
        print(f"削除されたユーザー数: {deleted_users}")
        
        # 最終的なユーザー数
        final_count = table_manager.count("users")
        print(f"最終ユーザー数: {final_count}")


def main():
    """メイン実行関数"""
    print("🚀 データベースサンプル実行開始")
    
    try:
        # データベース初期化
        setup_database()
        
        # サンプル操作実行
        sample_operations()
        
        print("\n✅ すべての操作が正常に完了しました")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()