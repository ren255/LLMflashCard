#!/usr/bin/env python3
"""
AnkiConnect Deck Generator
CSVファイルからAnkiデッキを自動生成するスクリプト
"""

import sys
import json
import requests
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import pandas as pd
import yaml
import time
from datetime import datetime, timedelta


@dataclass
class ConfigData:
    """YAML設定データを保持するデータクラス"""
    csv_folder: Path
    note_type: str
    card_type: str
    field_mapping: Dict[str, str]  # anki_field: csv_column
    deck_location: str
    tag_list: List[str]


class YamlLoader:
    """YAML設定ファイルの読み込み・解析・チェック"""

    @staticmethod
    def load_config(config_path: Path) -> ConfigData:
        """YAML設定ファイルを読み込み、ConfigDataオブジェクトを返す"""
        if not config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

        # 必須フィールドの確認
        required_fields = ['csv_folder', 'note_type',
                           'card_type', 'field_mapping', 'deck_location']
        for field in required_fields:
            if field not in config_dict:
                raise ValueError(f"必須フィールドが不足しています: {field}")

        # パスの変換と検証
        csv_folder = Path(config_dict['csv_folder'])
        if not csv_folder.exists():
            raise FileNotFoundError(f"CSVフォルダが見つかりません: {csv_folder}")

        return ConfigData(
            csv_folder=csv_folder,
            note_type=config_dict['note_type'],
            card_type=config_dict['card_type'],
            field_mapping=config_dict['field_mapping'],
            deck_location=config_dict['deck_location'],
            tag_list=config_dict.get('tag_list', [])
        )


import json
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional


class AnkiConnector:
    """AnkiConnect API通信・デッキ/ノート操作"""

    def __init__(self, test=False, url: str = "http://localhost:8765"):
        self.url = url
        actions_path = Path("anki/anki_connect_actions.json")
        self.actions_list = json.loads(actions_path.read_text(encoding="utf-8"))

        # 重複スコープ設定（デフォルト: deck）
        self.duplicateScope = "all" if test else "deck"

    def request_maker(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """リクエストデータの作成"""
        if action not in self.actions_list:
            raise ValueError(
                f"無効なaction: '{action}'. 有効なactionは: {', '.join(self.actions_list)}")

        # 重複スコープの適用
        if action in {"addNote", "addNotes"}:
            if params is None:
                params = {}
            params["options"] = {
                "duplicateScope": self.duplicateScope,
                "duplicateScopeOptions": {
                    "deckName": params.get("deckName") or "Default",
                    "checkChildren": False,
                    "checkAllModels": False
                }
            }

        return {
            "action": action,
            "version": 6,
            "params": params or {}
        }

    def _request(self, action: str, params: Optional[Dict] = None) -> Any:
        """AnkiConnect APIへリクエストを送信"""
        payload = self.request_maker(action, params)

        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("error"):
                raise Exception(
                    f"AnkiConnect API エラー actionは {action} : {result['error']}")

            return result.get("result")
        except requests.exceptions.ConnectionError:
            raise Exception("Ankiに接続できません。Ankiが起動していることを確認してください。")

    def test_connection(self) -> bool:
        """AnkiConnect接続テスト"""
        try:
            self._request("version")
            return True
        except:
            return False

    def get_note_type_fields(self, note_type: str) -> List[str]:
        """ノートタイプのフィールド名一覧を取得"""
        model_names = self._request("modelNames")
        if note_type not in model_names:
            raise ValueError(f"ノートタイプが見つかりません: {note_type}")
        return self._request("modelFieldNames", {"modelName": note_type})

    def create_deck(self, deck_name: str) -> None:
        """デッキを作成（既存の場合はスキップ）"""
        self._request("createDeck", {"deck": deck_name})

    def make_note(self, deck_name: str, note_type: str, fields: Dict[str, str], tags: List[str]) -> Dict[str, Any]:
        """ノート定義を作成"""
        return {
            "deckName": deck_name,
            "modelName": note_type,
            "fields": fields,
            "tags": tags
        }

    def add_note(self, note: Dict[str, Any]) -> None:
        """ノートをデッキに追加"""
        self._request("addNote", {"note": note})

    def add_notes(self, notes: List[Dict[str, Any]]) -> List[Optional[int]]:
        return self._request("addNotes", {"notes": notes})

class CSVProcessor:
    """CSV読み込み・フィールドマッピング・データ変換"""

    @staticmethod
    def get_csv_files(folder_path: Path) -> List[Path]:
        """フォルダ内のCSVファイル一覧を取得"""
        return list(folder_path.glob("*.csv"))

    @staticmethod
    def load_csv(csv_path: Path) -> pd.DataFrame:
        """CSVファイルを読み込み"""
        try:
            return pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(csv_path, encoding='shift_jis')

    @staticmethod
    def validate_mapping(df: pd.DataFrame, field_mapping: Dict[str, str]) -> Dict[str, List[str]]:
        """フィールドマッピングの検証を行い、使用/未使用フィールドを返す"""
        csv_columns = set(df.columns)
        mapped_csv_columns = set(field_mapping.values())

        # CSVにない列をマッピングしようとしているかチェック
        missing_columns = mapped_csv_columns - csv_columns
        if missing_columns:
            raise ValueError(
                f"CSVに存在しない列がマッピングされています: {list(missing_columns)}")

        # 使用されない列とフィールドの特定
        unused_csv_columns = list(csv_columns - mapped_csv_columns)

        return {
            "unused_csv_columns": unused_csv_columns,
            "mapped_csv_columns": list(mapped_csv_columns)
        }

    @staticmethod
    def convert_row_to_note_fields(row: pd.Series, field_mapping: Dict[str, str]) -> Dict[str, str]:
        """DataFrameの行をAnkiノートフィールドに変換"""
        fields = {}
        for anki_field, csv_column in field_mapping.items():
            value = row.get(csv_column, "")
            fields[anki_field] = str(value) if pd.notna(value) else ""
        return fields


class AnkiDeckGenerator:
    """全体制御・実行フロー管理・ユーザー確認"""

    def __init__(self, config_path: Path):
        self.config = YamlLoader.load_config(config_path)
        self.anki = AnkiConnector(True)
        self.csv_processor = CSVProcessor()
        self.total_cards = 0
        self.total_decks = 0
        self.all_csv_fields = set()
        self.anki_note_fields = []
        self.unused_anki_fields = []
        self.all_unused_csv_columns = set()

    def analyze_data(self) -> None:
        """データを分析して統計情報を収集"""
        print("データを分析中...")

        # AnkiConnect接続確認
        if not self.anki.test_connection():
            raise Exception("Ankiに接続できません。Ankiが起動していることを確認してください。")

        # Ankiノートタイプのフィールド取得
        self.anki_note_fields = self.anki.get_note_type_fields(
            self.config.note_type)

        # マッピングされていないAnkiフィールドを特定
        mapped_anki_fields = set(self.config.field_mapping.keys())
        self.unused_anki_fields = [field for field in self.anki_note_fields
                                   if field not in mapped_anki_fields]

        # CSVファイルを分析
        csv_files = self.csv_processor.get_csv_files(self.config.csv_folder)
        self.total_decks = len(csv_files)

        for csv_file in csv_files:
            df = self.csv_processor.load_csv(csv_file)
            self.total_cards += len(df)
            self.all_csv_fields.update(df.columns)

            # 各CSVファイルでマッピング検証
            validation_result = self.csv_processor.validate_mapping(
                df, self.config.field_mapping)
            self.all_unused_csv_columns.update(
                validation_result["unused_csv_columns"])

    def display_summary(self) -> None:
        """実行前の確認情報を表示"""
        print("\n" + "="*60)
        print("実行前確認")
        print("="*60)
        print(f"デッキ数合計/カード数合計: {self.total_decks} / {self.total_cards}")
        print()

        print("CSVフィールド名リスト:")
        print(f"  {",".join(self.all_csv_fields)}")
        print()

        print("Ankiノートフィールド名リスト:")
        print(f"  {",".join(self.anki_note_fields)}")
        print()

        print(
            f"ノートタイプ/カードタイプ: {self.config.note_type} / {self.config.card_type}")
        print(f"deck: {self.config.deck_location}")
        print()

        # フィールドマッピングを整列して表示
        print("フィールドマッピング:")
        if self.config.field_mapping:
            max_anki_len = max(len(k)
                               for k in self.config.field_mapping.keys())
            max_csv_len = max(len(v)
                              for v in self.config.field_mapping.values())

            print(f"  {'Ankiフィールド':<{max_anki_len}} -> {'CSVカラム':<{max_csv_len}}")
            print(f"  {'-'*max_anki_len} -> {'-'*max_csv_len}")

            for anki_field, csv_column in self.config.field_mapping.items():
                print(
                    f"  {anki_field:<{max_anki_len}} -> {csv_column:<{max_csv_len}}")
        print()

        # 使用されないフィールドの表示
        if self.all_unused_csv_columns:
            unused_csv_str = ", ".join(sorted(self.all_unused_csv_columns))
            print(f"使用されないCSVカラム: {unused_csv_str}")
        else:
            print("使用されないCSVカラム: なし")

        if self.unused_anki_fields:
            unused_anki_str = ", ".join(self.unused_anki_fields)
            print(f"使用されないAnkiフィールド: {unused_anki_str}")
        else:
            print("使用されないAnkiフィールド: なし")

        print("\n" + "="*60)

    def confirm_execution(self) -> bool:
        """実行確認"""
        while True:
            response = input("実行しますか？ (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("'y' または 'n' を入力してください。")

    def _calculate_eta(self, start_time: datetime, current_progress: int, total_progress: int) -> str:
        """ETA計算"""
        if current_progress == 0:
            return "計算中..."

        elapsed = datetime.now() - start_time
        avg_time_per_item = elapsed / current_progress
        remaining_items = total_progress - current_progress
        eta_seconds = (avg_time_per_item * remaining_items).total_seconds()

        if eta_seconds < 60:
            return f"{int(eta_seconds)}秒"
        elif eta_seconds < 3600:
            return f"{int(eta_seconds // 60)}分{int(eta_seconds % 60)}秒"
        else:
            hours = int(eta_seconds // 3600)
            minutes = int((eta_seconds % 3600) // 60)
            return f"{hours}時間{minutes}分"

    def _print_progress(self, current: int, total: int, prefix: str = "", start_time: datetime = None) -> None:
        """プログレスバー表示"""
        percent = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)

        eta_str = ""
        if start_time and current > 0:
            eta_str = f" | ETA: {self._calculate_eta(start_time, current, total)}"

        print(
            f'\r{prefix}[{bar}] {current}/{total} ({percent:.1f}%){eta_str}', end='', flush=True)

    def generate_decks(self) -> None:
        """デッキ生成実行"""
        print("\nデッキ生成を開始します...")
        start_time = datetime.now()

        csv_files = self.csv_processor.get_csv_files(self.config.csv_folder)
        total_files = len(csv_files)

        # 全体の進捗初期化
        self._print_progress(0, total_files, "全体進捗: ", start_time)

        for i, csv_file in enumerate(csv_files, 1):
            deck_name = csv_file.stem
            full_deck_name = f"{self.config.deck_location}::{deck_name}"

            print(f"\n[{i}/{total_files}] 処理中: {deck_name}")

            # デッキ作成
            self.anki.create_deck(full_deck_name)

            # CSV読み込み
            df = self.csv_processor.load_csv(csv_file)
            total_cards = len(df)

            # カード追加の進捗バー初期化
            card_start_time = datetime.now()

            # ノート作成・追加
            notes = []
            for card_idx, (_, row) in enumerate(df.iterrows(), 1):
                fields = self.csv_processor.convert_row_to_note_fields(
                    row, self.config.field_mapping)

                note_data = {
                    "deckName": full_deck_name,
                    "modelName": self.config.note_type,
                    "fields": fields,
                    "tags": self.config.tag_list
                }

                note = self.anki.make_note(note_data)
                notes.append(note)

            self.anki.add_notes(notes)

            print(f"\n  完了: {total_cards}枚のカードを追加")

            # 全体進捗更新
            self._print_progress(i, total_files, "全体進捗: ", start_time)

        print(
            f"\n\n全体完了: {self.total_decks}個のデッキに{self.total_cards}枚のカードを作成しました。")
        elapsed_total = datetime.now() - start_time
        print(f"総実行時間: {elapsed_total}")

    def run(self) -> None:
        """メイン実行フロー"""
        # データ分析
        self.analyze_data()

        # 確認情報表示
        self.display_summary()

        # 実行確認
        if self.confirm_execution():
            self.generate_decks()
        else:
            print("実行をキャンセルしました。")


def main():
    """メイン関数"""
    if len(sys.argv) != 2:
        print("使用方法: python script.py config.yaml")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    generator = AnkiDeckGenerator(config_path)
    generator.run()


if __name__ == "__main__":
    main()
