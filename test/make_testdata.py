"""
Storage Module Test Data Creator

このスクリプトは、storage モジュールのテスト用データファイルを作成します。
- 画像ファイル（JPEG, PNG, WebP）
- CSVファイル（UTF-8, Shift-JIS, 異なる区切り文字）
- 大容量ファイル（パフォーマンステスト用）
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import numpy as np
import random
import string
import json
from typing import List, Dict, Any


class TestDataCreator:
    """テストデータ作成クラス"""

    def __init__(self, base_dir: str = "test/fixtures"):
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / "test_images"
        self.csvs_dir = self.base_dir / "test_csvs"
        self.databases_dir = self.base_dir / "test_databases"

    def create_all(self):
        """全てのテストデータを作成"""
        print("テストデータ作成を開始します...")

        self._create_directories()
        self.create_test_images()
        self.create_test_csvs()

        print(f"\nテストデータの作成が完了しました。")
        print(f"場所: {self.base_dir.absolute()}")

    def _create_directories(self):
        """必要なディレクトリを作成"""
        for directory in [self.images_dir, self.csvs_dir, self.databases_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def create_test_images(self):
        """テスト用画像ファイルを作成"""
        print("\n画像ファイルを作成中...")

        # 基本的な画像パターン
        image_configs = [
            # 小さい画像
            {"name": "small_red.jpg", "size": (
                100, 100), "color": "red", "format": "JPEG"},
            {"name": "small_blue.png", "size": (
                150, 150), "color": "blue", "format": "PNG"},
            {"name": "small_green.webp", "size": (
                120, 120), "color": "green", "format": "WebP"},

            # 中サイズ画像
            {"name": "medium_landscape.jpg", "size": (
                800, 600), "color": "purple", "format": "JPEG"},
            {"name": "medium_portrait.png", "size": (
                600, 800), "color": "orange", "format": "PNG"},
            {"name": "medium_square.jpg", "size": (
                512, 512), "color": "yellow", "format": "JPEG"},

            # 大きい画像
            {"name": "large_photo.jpg", "size": (
                2000, 1500), "color": "lightblue", "format": "JPEG"},
            {"name": "large_banner.png", "size": (
                1920, 1080), "color": "lightgreen", "format": "PNG"},

            # 特殊サイズ
            {"name": "wide_banner.jpg", "size": (
                1600, 400), "color": "pink", "format": "JPEG"},
            {"name": "tall_poster.png", "size": (
                400, 1200), "color": "lightcoral", "format": "PNG"},
        ]

        for config in image_configs:
            self._create_single_image(**config)

        # パターン画像も作成
        self._create_pattern_images()

        # 破損した画像ファイル（テスト用）
        self._create_corrupted_files()

        print(f"  ✓ {len(image_configs) + 5} 個の画像ファイルを作成しました")

    def _create_single_image(self, name: str, size: tuple, color: str, format: str):
        """単一の画像ファイルを作成"""
        img = Image.new('RGB', size, color=color)
        draw = ImageDraw.Draw(img)

        # テキストを追加
        try:
            # デフォルトフォントを使用
            font_size = min(size) // 10
            draw.text((10, 10), f"{size[0]}x{size[1]}", fill="white")
            draw.text((10, 30), name, fill="white")
        except:
            # フォントが使用できない場合はテキストなしで続行
            pass

        # 簡単な図形を追加
        draw.rectangle([size[0]//4, size[1]//4, 3*size[0]//4, 3*size[1]//4],
                       outline="white", width=2)

        # 保存
        file_path = self.images_dir / name

        # JPEG品質設定
        if format == "JPEG":
            img.save(file_path, format=format, quality=85)
        else:
            img.save(file_path, format=format)

    def _create_pattern_images(self):
        """パターン画像を作成"""
        # チェッカーボードパターン
        size = (400, 400)
        img = Image.new('RGB', size, 'white')
        draw = ImageDraw.Draw(img)

        checker_size = 50
        for y in range(0, size[1], checker_size):
            for x in range(0, size[0], checker_size):
                if (x // checker_size + y // checker_size) % 2 == 0:
                    draw.rectangle(
                        [x, y, x + checker_size, y + checker_size], fill='black')

        img.save(self.images_dir / "pattern_checker.png", "PNG")

        # グラデーション画像
        img = Image.new('RGB', (600, 400), 'white')
        pixels = img.load()
        if pixels is None:
            raise ValueError("画像のピクセルデータを取得できません")

        for y in range(400):
            for x in range(600):
                r = int(255 * x / 600)
                g = int(255 * y / 400)
                b = 128
                pixels[x, y] = (r, g, b)

        img.save(self.images_dir / "pattern_gradient.jpg", "JPEG")

    def _create_corrupted_files(self):
        """破損したファイル（テスト用）を作成"""
        # 偽の画像ファイル（実際はテキスト）
        fake_jpg = self.images_dir / "corrupted.jpg"
        with open(fake_jpg, 'w') as f:
            f.write("This is not a real image file")

        # 空ファイル
        empty_png = self.images_dir / "empty.png"
        empty_png.touch()

        print("  ✓ 破損ファイル（テスト用）を作成しました")

    def create_test_csvs(self):
        """テスト用CSVファイルを作成"""
        print("\nCSVファイルを作成中...")

        # 基本的なフラッシュカードデータ
        self._create_basic_flashcards()

        # 日本語データ（異なるエンコーディング）
        self._create_japanese_flashcards()

        # 大容量CSVファイル
        self._create_large_csv()

        # 特殊文字・区切り文字のテスト
        self._create_special_character_csvs()

        # 異なる列構成のCSV
        self._create_various_column_csvs()

        print("  ✓ CSV ファイルを作成しました")

    def _create_basic_flashcards(self):
        """基本的なフラッシュカードCSVを作成"""
        data = {
            'question': [
                'What is the capital of France?',
                'What is 2 + 2?',
                'Who wrote "Romeo and Juliet"?',
                'What is the largest planet?',
                'What year did World War II end?'
            ],
            'answer': [
                'Paris',
                '4',
                'William Shakespeare',
                'Jupiter',
                '1945'
            ],
            'category': [
                'Geography',
                'Mathematics',
                'Literature',
                'Science',
                'History'
            ],
            'difficulty': [
                'Easy',
                'Easy',
                'Medium',
                'Easy',
                'Medium'
            ]
        }

        df = pd.DataFrame(data)
        df.to_csv(self.csvs_dir / "basic_flashcards_utf8.csv",
                  encoding='utf-8', index=False)

    def _create_japanese_flashcards(self):
        """日本語フラッシュカードを異なるエンコーディングで作成"""
        data_jp = {
            '質問': [
                '日本の首都は？',
                '富士山の高さは？',
                '日本で一番大きい島は？',
                '日本の国花は？',
                '平安時代の都は？'
            ],
            '回答': [
                '東京',
                '3776メートル',
                '本州',
                '桜',
                '平安京（京都）'
            ],
            'カテゴリ': [
                '地理',
                '地理',
                '地理',
                '文化',
                '歴史'
            ],
            '難易度': [
                '易しい',
                '普通',
                '易しい',
                '普通',
                '難しい'
            ]
        }

        df_jp = pd.DataFrame(data_jp)

        # UTF-8版
        df_jp.to_csv(self.csvs_dir / "japanese_flashcards_utf8.csv",
                     encoding='utf-8', index=False)

        # Shift-JIS版
        df_jp.to_csv(self.csvs_dir / "japanese_flashcards_sjis.csv",
                     encoding='shift-jis', index=False)

        # CP932版
        try:
            df_jp.to_csv(self.csvs_dir / "japanese_flashcards_cp932.csv",
                         encoding='cp932', index=False)
        except:
            print("    警告: CP932エンコーディングでの保存に失敗しました")

    def _create_large_csv(self):
        """大容量CSVファイルを作成（パフォーマンステスト用）"""
        print("  大容量CSVファイルを作成中...")

        # 1万行のデータを生成
        num_rows = 10000

        categories = ['Math', 'Science', 'History',
                      'Geography', 'Literature', 'Art']
        difficulties = ['Easy', 'Medium', 'Hard']

        data = {
            'id': range(1, num_rows + 1),
            'question': [f"Question {i}: " + ''.join(random.choices(string.ascii_letters + ' ', k=50))
                         for i in range(num_rows)],
            'answer': [f"Answer {i}: " + ''.join(random.choices(string.ascii_letters + ' ', k=30))
                       for i in range(num_rows)],
            'category': [random.choice(categories) for _ in range(num_rows)],
            'difficulty': [random.choice(difficulties) for _ in range(num_rows)],
            'score': [random.randint(0, 100) for _ in range(num_rows)],
            'created_date': [f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                             for _ in range(num_rows)]
        }

        df = pd.DataFrame(data)
        df.to_csv(self.csvs_dir / "large_flashcards.csv",
                  encoding='utf-8', index=False)

        print(f"    ✓ {num_rows:,} 行の大容量CSVを作成しました")

    def _create_special_character_csvs(self):
        """特殊文字・区切り文字のテストCSVを作成"""
        # カンマ区切り（標準）
        data = {
            'question': ['What is "Hello" in French?', 'Calculate: 1,000 + 2,000'],
            'answer': ['Bonjour', '3,000'],
            'notes': ['Contains quotes', 'Contains commas in numbers']
        }
        df = pd.DataFrame(data)
        df.to_csv(self.csvs_dir / "special_chars_comma.csv",
                  encoding='utf-8', index=False)

        # セミコロン区切り
        df.to_csv(self.csvs_dir / "special_chars_semicolon.csv",
                  encoding='utf-8', index=False, sep=';')

        # タブ区切り
        df.to_csv(self.csvs_dir / "special_chars_tab.tsv",
                  encoding='utf-8', index=False, sep='\t')

        # 特殊文字を含むデータ
        special_data = {
            'question': [
                'What is ∑(i=1 to n) i?',
                'Translate: café, naïve, résumé',
                'Symbol: α, β, γ, δ',
                'Emoji test: 📚✨🎯'
            ],
            'answer': [
                'n(n+1)/2',
                'Coffee, naive, resume',
                'Greek letters',
                'Books, sparkles, target'
            ]
        }

        df_special = pd.DataFrame(special_data)
        df_special.to_csv(self.csvs_dir / "unicode_special.csv",
                          encoding='utf-8', index=False)

    def _create_various_column_csvs(self):
        """異なる列構成のCSVを作成"""
        # 最小構成（2列）
        minimal = pd.DataFrame({
            'front': ['A', 'B', 'C'],
            'back': ['1', '2', '3']
        })
        minimal.to_csv(self.csvs_dir / "minimal_2columns.csv",
                       encoding='utf-8', index=False)

        # 多列構成
        many_columns = pd.DataFrame({
            'question': ['Q1', 'Q2'],
            'answer': ['A1', 'A2'],
            'category': ['Cat1', 'Cat2'],
            'subcategory': ['Sub1', 'Sub2'],
            'difficulty': ['Easy', 'Hard'],
            'tags': ['tag1,tag2', 'tag3,tag4'],
            'source': ['Book1', 'Book2'],
            'page': [10, 20],
            'created_by': ['User1', 'User2'],
            'last_review': ['2024-01-01', '2024-01-02'],
            'review_count': [5, 3],
            'success_rate': [0.8, 0.6]
        })
        many_columns.to_csv(self.csvs_dir / "many_columns.csv",
                            encoding='utf-8', index=False)

        # 空のセルを含むCSV
        with_nulls = pd.DataFrame({
            'question': ['Q1', 'Q2', 'Q3', 'Q4'],
            'answer': ['A1', '', 'A3', 'A4'],
            'category': ['Cat1', 'Cat2', '', 'Cat4'],
            'notes': ['Note1', None, 'Note3', '']
        })
        with_nulls.to_csv(self.csvs_dir / "with_nulls.csv",
                          encoding='utf-8', index=False)


if __name__ == "__main__":
    testgenerator = TestDataCreator()
    testgenerator.create_all()