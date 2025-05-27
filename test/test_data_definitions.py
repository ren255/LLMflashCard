"""
Test Data Definitions

テストデータのサンプル定義を管理するモジュール
"""

import random
import string


class SampleDataDefinitions:
    """テストデータのサンプル定義クラス"""

    @staticmethod
    def get_image_configs():
        """画像ファイルの設定を取得"""
        return [
            # 小さい画像
            {"name": "small_red.jpg", "size": (100, 100), "color": "red", "format": "JPEG"},
            {"name": "small_blue.png", "size": (150, 150), "color": "blue", "format": "PNG"},
            {"name": "small_green.webp", "size": (120, 120), "color": "green", "format": "WebP"},

            # 中サイズ画像
            {"name": "medium_landscape.jpg", "size": (800, 600), "color": "purple", "format": "JPEG"},
            {"name": "medium_portrait.png", "size": (600, 800), "color": "orange", "format": "PNG"},
            {"name": "medium_square.jpg", "size": (512, 512), "color": "yellow", "format": "JPEG"},

            # 大きい画像
            {"name": "large_photo.jpg", "size": (2000, 1500), "color": "lightblue", "format": "JPEG"},
            {"name": "large_banner.png", "size": (1920, 1080), "color": "lightgreen", "format": "PNG"},

            # 特殊サイズ
            {"name": "wide_banner.jpg", "size": (1600, 400), "color": "pink", "format": "JPEG"},
            {"name": "tall_poster.png", "size": (400, 1200), "color": "lightcoral", "format": "PNG"},
        ]

    @staticmethod
    def get_basic_flashcard_data():
        """基本的なフラッシュカードデータを取得"""
        return {
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

    @staticmethod
    def get_japanese_flashcard_data():
        """日本語フラッシュカードデータを取得"""
        return {
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

    @staticmethod
    def get_special_character_data():
        """特殊文字を含むデータを取得"""
        return {
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

    @staticmethod
    def get_quote_comma_data():
        """引用符とカンマを含むデータを取得"""
        return {
            'question': ['What is "Hello" in French?', 'Calculate: 1,000 + 2,000'],
            'answer': ['Bonjour', '3,000'],
            'notes': ['Contains quotes', 'Contains commas in numbers']
        }

    @staticmethod
    def get_minimal_columns_data():
        """最小構成（2列）のデータを取得"""
        return {
            'front': ['A', 'B', 'C'],
            'back': ['1', '2', '3']
        }

    @staticmethod
    def get_many_columns_data():
        """多列構成のデータを取得"""
        return {
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
        }

    @staticmethod
    def get_nulls_data():
        """空のセルを含むデータを取得"""
        return {
            'question': ['Q1', 'Q2', 'Q3', 'Q4'],
            'answer': ['A1', '', 'A3', 'A4'],
            'category': ['Cat1', 'Cat2', '', 'Cat4'],
            'notes': ['Note1', None, 'Note3', '']
        }

    @staticmethod
    def get_data_generation_config():
        """大容量データ生成用の設定を取得"""
        return {
            'categories': ['Math', 'Science', 'History', 'Geography', 'Literature', 'Art'],
            'difficulties': ['Easy', 'Medium', 'Hard'],
            'large_csv_rows': 10000
        }

    @staticmethod
    def generate_random_text(length: int = 16) -> str:
        """ランダムなテキストを生成"""
        return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length)).strip()

    @staticmethod
    def generate_random_question_answer():
        """ランダムな質問と回答のペアを生成"""
        return {
            'question': SampleDataDefinitions.generate_random_text(16),
            'answer': SampleDataDefinitions.generate_random_text(16)
        }