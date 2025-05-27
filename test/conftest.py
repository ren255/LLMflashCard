"""
pytest設定とテスト用フィクスチャの定義
Storage モジュールのテストで共通的に使用するフィクスチャとユーティリティを提供
"""

import psutil
import pytest
import tempfile
import shutil
from pathlib import Path
import sqlite3
from PIL import Image
import pandas as pd
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils import LogLevel, set_global_log_level, log
from storage import FlashcardStorage, ImageStorage, FileManager, StorageController

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


set_global_log_level(LogLevel.DEBUG)
log.debug("Setting up test fixtures for Storage module")

# テスト用の定数
TEST_BASE_DIR = "test_resources"
FIXTURES_DIR = Path(__file__).parent / "_fixtures"


@pytest.fixture(scope="session")
def fixtures_path():
    """フィクスチャファイルのパスを返す"""
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def test_images_path(fixtures_path):
    """テスト画像ディレクトリのパスを返す"""
    return fixtures_path / "test_images"


@pytest.fixture(scope="session")
def test_csvs_path(fixtures_path):
    """テストCSVディレクトリのパスを返す"""
    return fixtures_path / "test_csvs"


@pytest.fixture(scope="session")
def bulk_files_path(fixtures_path):
    """バルクテストファイルディレクトリのパスを返す"""
    return fixtures_path / "bulk"


@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成し、テスト後にクリーンアップ"""
    temp_path = tempfile.mkdtemp(prefix="storage_test_")
    yield Path(temp_path)
    # クリーンアップ
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def storage_controller(temp_dir):
    """テスト用のStorageControllerインスタンス"""
    controller = StorageController(str(temp_dir))
    yield controller
    # クリーンアップ
    controller.cleanup()


@pytest.fixture
def image_storage(temp_dir):
    """テスト用のImageStorageインスタンス"""
    paths = {
        "base_path": str(temp_dir),
        "storage_path": str(temp_dir / "image"),
        "thumbnails_path": str(temp_dir / "thumbnails" / "image"),
        "temp_path": str(temp_dir / "temp" / "image"),
        "db_path": str(temp_dir / "db" / "images.db")
    }

    # ディレクトリを作成
    for path_key in ["storage_path", "thumbnails_path", "temp_path"]:
        Path(paths[path_key]).mkdir(parents=True, exist_ok=True)
    Path(paths["db_path"]).parent.mkdir(parents=True, exist_ok=True)

    storage = ImageStorage("image", paths)
    yield storage
    storage.cleanup() if hasattr(storage, 'cleanup') else None


@pytest.fixture
def flashcard_storage(temp_dir):
    """テスト用のFlashcardStorageインスタンス"""
    paths = {
        "base_path": str(temp_dir),
        "storage_path": str(temp_dir / "flashcard"),
        "thumbnails_path": str(temp_dir / "thumbnails" / "flashcard"),
        "temp_path": str(temp_dir / "temp" / "flashcard"),
        "db_path": str(temp_dir / "db" / "flashcards.db")
    }

    # ディレクトリを作成
    for path_key in ["storage_path", "thumbnails_path", "temp_path"]:
        Path(paths[path_key]).mkdir(parents=True, exist_ok=True)
    Path(paths["db_path"]).parent.mkdir(parents=True, exist_ok=True)

    storage = FlashcardStorage("flashcard", paths)
    yield storage
    storage.cleanup() if hasattr(storage, 'cleanup') else None


@pytest.fixture
def file_manager(temp_dir):
    """テスト用のFileManagerインスタンス"""
    paths = {
        "base_path": str(temp_dir),
        "storage_path": str(temp_dir / "files"),
        "thumbnails_path": str(temp_dir / "thumbnails"),
        "temp_path": str(temp_dir / "temp")
    }

    # ディレクトリを作成
    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)

    return FileManager(paths)


@pytest.fixture
def sample_image_file(temp_dir):
    """テスト用のサンプル画像ファイルを作成"""
    image_path = temp_dir / "sample_image.jpg"
    # 100x100の赤い画像を作成
    image = Image.new('RGB', (100, 100), color='red')
    image.save(image_path, 'JPEG')
    return image_path


@pytest.fixture
def sample_png_file(temp_dir):
    """テスト用のサンプルPNG画像ファイルを作成"""
    image_path = temp_dir / "sample_image.png"
    # 200x150の青い画像を作成
    image = Image.new('RGB', (200, 150), color='blue')
    image.save(image_path, 'PNG')
    return image_path


@pytest.fixture
def sample_csv_file(temp_dir):
    """テスト用のサンプルCSVファイルを作成"""
    csv_path = temp_dir / "sample_flashcards.csv"
    data = {
        'question': ['What is Python?', 'What is AI?', 'What is ML?'],
        'answer': ['Programming language', 'Artificial Intelligence', 'Machine Learning'],
        'category': ['Programming', 'Technology', 'Technology']
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    return csv_path


@pytest.fixture
def sample_csv_sjis_file(temp_dir):
    """テスト用のShift-JIS CSVファイルを作成"""
    csv_path = temp_dir / "sample_sjis.csv"
    data = {
        '質問': ['Pythonとは？', 'AIとは？'],
        '答え': ['プログラミング言語', '人工知能'],
        'カテゴリ': ['プログラミング', 'テクノロジー']
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding='shift-jis')
    return csv_path


@pytest.fixture
def multiple_test_images(temp_dir):
    """複数のテスト画像を作成"""
    images = {}

    # JPEG画像
    jpeg_path = temp_dir / "test.jpg"
    Image.new('RGB', (300, 200), color='green').save(jpeg_path, 'JPEG')
    images['jpeg'] = jpeg_path

    # PNG画像
    png_path = temp_dir / "test.png"
    Image.new('RGBA', (150, 150), color=(255, 0, 0, 128)).save(png_path, 'PNG')
    images['png'] = png_path

    # 大きな画像
    large_path = temp_dir / "large.jpg"
    Image.new('RGB', (1920, 1080), color='yellow').save(large_path, 'JPEG')
    images['large'] = large_path

    # 小さな画像
    small_path = temp_dir / "small.png"
    Image.new('RGB', (50, 50), color='purple').save(small_path, 'PNG')
    images['small'] = small_path

    return images


@pytest.fixture
def multiple_test_csvs(temp_dir):
    """複数のテストCSVを作成"""
    csvs = {}

    # 基本CSV
    basic_path = temp_dir / "basic.csv"
    pd.DataFrame({
        'front': ['Hello', 'Goodbye'],
        'back': ['こんにちは', 'さようなら']
    }).to_csv(basic_path, index=False)
    csvs['basic'] = basic_path

    # 多カラムCSV
    multi_path = temp_dir / "multi_column.csv"
    pd.DataFrame({
        'question': ['Q1', 'Q2', 'Q3'],
        'answer': ['A1', 'A2', 'A3'],
        'category': ['Cat1', 'Cat2', 'Cat1'],
        'difficulty': ['Easy', 'Hard', 'Medium'],
        'tags': ['tag1,tag2', 'tag3', 'tag1,tag3']
    }).to_csv(multi_path, index=False)
    csvs['multi'] = multi_path

    # 大きなCSV
    large_data = {
        'q': [f'Question {i}' for i in range(1000)],
        'a': [f'Answer {i}' for i in range(1000)]
    }
    large_path = temp_dir / "large.csv"
    pd.DataFrame(large_data).to_csv(large_path, index=False)
    csvs['large'] = large_path

    return csvs


@pytest.fixture
def corrupted_files(temp_dir):
    """破損したファイルを作成"""
    files = {}

    # 破損画像
    bad_image = temp_dir / "corrupted.jpg"
    with open(bad_image, 'wb') as f:
        f.write(b'This is not an image file')
    files['bad_image'] = bad_image

    # 破損CSV
    bad_csv = temp_dir / "corrupted.csv"
    with open(bad_csv, 'w') as f:
        f.write('This,is,not\nvalid,csv"data\nwith"broken,quotes')
    files['bad_csv'] = bad_csv

    return files


class TestDataHelper:
    """テストデータ作成のためのヘルパークラス"""

    @staticmethod
    def create_test_database(db_path: Path, table_name: str, schema: dict):
        """テスト用データベースを作成"""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)

        # テーブル作成
        columns = []
        for col_name, col_type in schema.items():
            columns.append(f"{col_name} {col_type}")

        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        conn.execute(create_sql)
        conn.commit()
        conn.close()

    @staticmethod
    def insert_test_data(db_path: Path, table_name: str, data: list):
        """テストデータをデータベースに挿入"""
        conn = sqlite3.connect(db_path)

        if data:
            columns = list(data[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            for record in data:
                values = [record.get(col) for col in columns]
                conn.execute(insert_sql, values)

        conn.commit()
        conn.close()


@pytest.fixture
def test_data_helper():
    """テストデータヘルパーのインスタンス"""
    return TestDataHelper()

# パフォーマンステスト用のマーカー


def pytest_configure(config):
    """pytestの設定"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )

# テスト実行時の共通設定


@pytest.fixture(autouse=True)
def setup_test_environment():
    """各テスト実行前の共通セットアップ"""
    # テスト開始前の処理
    yield
    # テスト終了後の処理（必要に応じて）


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    global process, peak_memory
    process = psutil.Process()
    peak_memory = process.memory_info().rss


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    global process, peak_memory
    mem = process.memory_info().rss
    if mem > peak_memory:
        peak_memory = mem
    print(
        f"\n[MEMORY] Max RSS during test run: {peak_memory / (1024 ** 2):.2f} MB")
