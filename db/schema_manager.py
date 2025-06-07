import argparse
import sqlite3
from pathlib import Path
from typing import List


class SchemaManager:
    """
    schema.sqlファイルを読み込み、CREATE TABLEステートメントを順次実行するクラス

    責務:
    - schema.sqlの読み込み・解析（セミコロン分割）
    - CREATE TABLEの順次実行
    - 各テーブル作成結果の出力
    - DBファイル作成（存在しない場合）
    """

    def __init__(self, db_path: Path, schema_path:  Path):
        """
        Args:
            db_path: データベースファイルのパス（相対パス）
            schema_path: スキーマファイルのパス（相対パス）
        """
        self.db_path = db_path
        self.schema_path = schema_path

    def load_schema(self) -> List[str]:
        """
        schema.sqlファイルを読み込み、CREATE TABLEステートメントを抽出

        Returns:
            CREATE TABLEステートメントのリスト
        """
        if not self.schema_path.exists():
            print(f"Schema file not found: {self.schema_path}")
            return []

        try:
            content = self.schema_path.read_text(encoding='utf-8')
            # セミコロンで分割してCREATE TABLEステートメントを抽出
            statements = []
            for statement in content.split(';'):
                statement = statement.strip()
                if statement and 'CREATE TABLE' in statement.upper():
                    statements.append(statement)
            return statements
        except Exception as e:
            print(f"Failed to read schema file: {e}")
            return []

    def extract_table_name(self, sql: str) -> str:
        """
        CREATE TABLEステートメントからテーブル名を抽出

        Args:
            sql: CREATE TABLEステートメント

        Returns:
            テーブル名（抽出できない場合は"unknown"）
        """
        try:
            # CREATE TABLE table_name の部分を抽出
            upper_sql = sql.upper()
            start = upper_sql.find('CREATE TABLE') + len('CREATE TABLE')
            remaining = sql[start:].strip()

            # IF NOT EXISTS がある場合は除去
            if remaining.upper().startswith('IF NOT EXISTS'):
                remaining = remaining[len('IF NOT EXISTS'):].strip()

            # テーブル名を抽出（スペースまたは括弧まで）
            table_name = remaining.split()[0].split('(')[0].strip('`"[]')
            return table_name
        except:
            return "unknown"

    def create_tables(self, mode: str = "default") -> None:
        """
        スキーマファイルからテーブルを作成

        Args:
            mode: 作成モード
                - "default": 新規テーブルのみ作成（既存はスキップ）
                - "overwrite": 既存テーブルを削除してから作成
        """
        statements = self.load_schema()
        if not statements:
            print("No CREATE TABLE statements found")
            return

        # 有効なモードかチェック
        valid_modes = ["default", "overwrite"]
        if mode not in valid_modes:
            print(f"Invalid mode '{mode}'. Valid modes: {valid_modes}")
            return

        # DBファイルの親ディレクトリを作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with sqlite3.connect(self.db_path) as conn:
                for statement in statements:
                    table_name = self.extract_table_name(statement)

                    try:
                        if mode == "overwrite":
                            # 上書きモード: 既存テーブルを削除してから作成
                            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                            conn.execute(statement)
                            print(
                                f"Table '{table_name}': Overwritten successfully")

                        else:  # default mode
                            # デフォルトモード: 新規作成のみ
                            conn.execute(statement)
                            print(
                                f"Table '{table_name}': Created successfully")

                    except sqlite3.OperationalError as e:
                        if "already exists" in str(e).lower():
                            print(
                                f"Table '{table_name}': Already exists (skipped)")
                        else:
                            print(f"Table '{table_name}': Failed - {e}")
                    except Exception as e:
                        print(f"Table '{table_name}': Failed - {e}")

                conn.commit()

        except Exception as e:
            print(f"Database connection failed: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="schemaマネージャー")
    parser.add_argument(
        "db_path",
        nargs="?",
        default="resources/db.db",
        help="対象のdbへのpath、省略でresources/db.db"
    )
    parser.add_argument(
        "-y",
        action="store_true",
        help="上書きモードで実行"
    )

    args = parser.parse_args()

    db = Path(args.db_path)
    schema = Path("db/schema.sql")
    manager = SchemaManager(db, schema)

    if args.y:
        # 上書きモード
        print("\n=== Overwrite mode ===")
        manager.create_tables("overwrite")
    else:
        # デフォルトモード（新規作成のみ）
        print("=== Default mode ===")
        manager.create_tables("default")


if __name__ == "__main__":
    main()
