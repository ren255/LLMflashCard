from __future__ import annotations
from typing import Optional, Dict, List, Any, Tuple
import os
import uuid
import hashlib
import shutil
from PIL import Image
from pathlib import Path

##
# @brief ファイル管理クラス
# @details path辞書を受け取ってファイルの保存、削除、サムネイル作成などを行う
class FileManager():
    def __init__(self, paths: Dict[str, str]):
        """
        path辞書からFileManagerを初期化
        
        Args:
            paths: パス情報の辞書
                - "storage_path": メインファイル保存ディレクトリ
                - "thumbnails_path": サムネイル保存ディレクトリ  
                - "temp_path": 一時ファイルディレクトリ
                - "base_path": ベースディレクトリ（相対パス計算用）
        """
        self.paths = paths
        self.storage_dir = Path(paths["storage_path"])
        self.thumbnails_dir = Path(paths["thumbnails_path"])
        self.temp_dir = Path(paths["temp_path"])
        self.base_path = Path(paths["base_path"])
        
        # ディレクトリが存在しない場合は作成
        self._ensure_directories()
    
    def _ensure_directories(self):
        """必要なディレクトリが存在することを確保"""
        for dir_path in [self.storage_dir, self.thumbnails_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def create_thumbnail(self, image_path: Path, filename: str) -> str:
        """サムネイル作成"""
        try:
            thumbnail_name = f"thumb_{filename}"
            thumbnail_path = self.thumbnails_dir / thumbnail_name
            
            with Image.open(image_path) as img:
                # RGB変換（RGBA対応）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", optimize=True, quality=85)
            
            return str(thumbnail_path)
        except Exception as e:
            print(f"サムネイル作成エラー: {e}")
            return ""

    def calculate_hash(self, file_path: str) -> str:
        """ファイルのSHA256ハッシュをバイナリから計算"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def generate_filename(self, file_extension: str) -> str:
        """新しいファイル名を生成（重複防止）"""
        return f"{uuid.uuid4().hex}{file_extension}"

    def get_file_path(self, filename: str) -> str:
        """ファイル名から完全パスを取得"""
        return str(self.storage_dir / filename)

    def get_relative_path(self, full_path: str) -> str:
        """完全パスから相対パスを生成"""
        return str(Path(full_path).relative_to(self.base_path))

    def delete_file(self, file_path: str, thumbnail_path: str = ""):
        """ファイルとサムネイルを削除"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except Exception as e:
            print(f"ファイル削除エラー: {e}")

    def save_file(self, source_path: str) -> str:
        """
        ファイルを保存し、pathを返す
        """
        try:
            file_extension = Path(source_path).suffix.lower()
            new_filename = self.generate_filename(file_extension)
            save_path = self.storage_dir / new_filename
            shutil.copy2(source_path, save_path)
            return str(save_path)
        
        except Exception as e:
            print(f"file保存エラー: {e}")
            return ""

    def move_from_temp(self, temp_filename: str) -> str:
        """
        一時ディレクトリからメインディレクトリにファイルを移動
        """
        try:
            temp_path = self.temp_dir / temp_filename
            if not temp_path.exists():
                raise FileNotFoundError(f"一時ファイルが見つかりません: {temp_path}")
            
            file_extension = temp_path.suffix.lower()
            new_filename = self.generate_filename(file_extension)
            final_path = self.storage_dir / new_filename
            
            shutil.move(str(temp_path), str(final_path))
            return str(final_path)
        
        except Exception as e:
            print(f"一時ファイル移動エラー: {e}")
            return ""

    def save_to_temp(self, source_path: str) -> str:
        """
        ファイルを一時ディレクトリに保存
        """
        try:
            source_file = Path(source_path)
            temp_filename = f"temp_{uuid.uuid4().hex}{source_file.suffix}"
            temp_path = self.temp_dir / temp_filename
            
            shutil.copy2(source_path, temp_path)
            return str(temp_path)
        
        except Exception as e:
            print(f"一時ファイル保存エラー: {e}")
            return ""

    def get_paths_info(self) -> Dict[str, str]:
        """パス情報を取得"""
        return {
            **self.paths,
            "storage_dir_resolved": str(self.storage_dir.resolve()),
            "thumbnails_dir_resolved": str(self.thumbnails_dir.resolve()),
            "temp_dir_resolved": str(self.temp_dir.resolve()),
        }