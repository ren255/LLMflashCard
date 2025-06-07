#!/usr/bin/env python3
"""
PDF処理スクリプト
PDFファイルをページごとにPNG画像に分割する
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
from PIL import Image
import io


class FileSystem:
    """ファイルシステム操作を管理するクラス"""
    
    def __init__(self):
        self.base_path = Path(".")
        self.input_dir = self.base_path / "resources" / "FileSystem" / "in"
        self.output_base_dir = self.base_path / "resources" / "FileSystem" / "save" / "pdf_img"
        self.pdf_archive_dir = self.base_path / "resources" / "FileSystem" / "save" / "pdf"
    
    def ensure_directories(self):
        """必要なディレクトリを作成"""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_archive_dir.mkdir(parents=True, exist_ok=True)
    
    def get_pdf_files(self) -> List[Path]:
        """入力ディレクトリからPDFファイルを取得"""
        if not self.input_dir.exists():
            return []
        return list(self.input_dir.glob("*.pdf"))
    
    def create_output_dir(self, pdf_name: str) -> Path:
        """PDF名に基づいて出力ディレクトリを作成"""
        output_dir = self.output_base_dir / pdf_name
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def move_pdf_to_archive(self, pdf_path: Path) -> bool:
        """PDFファイルをアーカイブディレクトリに移動"""
        try:
            archive_path = self.pdf_archive_dir / pdf_path.name
            
            # 同名ファイルが存在する場合は連番を付ける
            counter = 1
            while archive_path.exists():
                name_part = pdf_path.stem
                extension = pdf_path.suffix
                archive_path = self.pdf_archive_dir / f"{name_part}_{counter:03d}{extension}"
                counter += 1
            
            # ファイルを移動
            pdf_path.rename(archive_path)
            print(f"移動完了: {pdf_path.name} -> {archive_path}")
            return True
            
        except Exception as e:
            print(f"エラー: PDFファイルの移動に失敗しました: {e}")
            return False


class PdfData:
    """PDFデータを管理するクラス"""
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.name = pdf_path.stem
        self.doc = None
        self.page_count = 0
    
    def load(self):
        """PDFファイルを読み込み"""
        try:
            self.doc = fitz.open(self.pdf_path)
            self.page_count = len(self.doc)
            return True
        except Exception as e:
            print(f"エラー: PDFファイル '{self.pdf_path}' の読み込みに失敗しました: {e}")
            return False
    
    def get_page(self, page_num: int):
        """指定されたページを取得"""
        if self.doc is None or page_num >= self.page_count:
            return None
        return self.doc[page_num]
    
    def close(self):
        """PDFファイルを閉じる"""
        if self.doc:
            self.doc.close()


class PdfProcess:
    """PDF処理のメインクラス"""
    
    def __init__(self, dpi: int = 150):
        self.filesystem = FileSystem()
        self.dpi = dpi
    
    def set_dpi(self, dpi: int):
        """DPI設定を変更"""
        self.dpi = max(72, min(600, dpi))  # 72-600の範囲で制限
    
    def get_pixmap(self, page, matrix=None, colorspace=None, alpha=True):
        """ページからPixmapを生成（最新PyMuPDF対応）"""
        try:
            # デフォルトの変換行列を設定
            if matrix is None:
                matrix = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            
            # デフォルトのカラースペースを設定
            if colorspace is None:
                colorspace = fitz.csRGB
            
            # Pixmapを生成（最新のAPI使用）
            pixmap = page.get_pixmap(
                matrix=matrix,
                colorspace=colorspace,
                alpha=alpha
            )
            
            return pixmap
            
        except Exception as e:
            print(f"エラー: Pixmap生成に失敗しました: {e}")
            return None
    
    def split_pdf_to_images(self, pdf_data: PdfData, output_dir: Path, 
                           format: str = "png") -> bool:
        """PDFを画像に分割"""
        try:
            for page_num in range(pdf_data.page_count):
                page = pdf_data.get_page(page_num)
                if page is None:
                    continue
                
                # 変換行列を設定
                matrix = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                
                # Pixmapを生成
                pixmap = self.get_pixmap(
                    page=page,
                    matrix=matrix,
                    colorspace=fitz.csRGB,
                    alpha=False  # PNGの場合はTrueでも可、JPEGの場合はFalse
                )
                
                if pixmap is None:
                    print(f"警告: ページ {page_num + 1} のPixmap生成に失敗しました")
                    continue
                
                # ファイル名を生成（ページ番号は1から開始）
                filename = f"page_{page_num + 1:03d}.{format.lower()}"
                output_path = output_dir / filename
                
                # 画像フォーマットに応じた保存処理
                if format.lower() == "png":
                    # PNGの場合：PIL経由で高品質保存
                    img_data = pixmap.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    img.save(output_path, "PNG", optimize=True)
                elif format.lower() in ["jpg", "jpeg"]:
                    # JPEGの場合：PIL経由で品質指定保存
                    img_data = pixmap.tobytes("png")  # 一旦PNGで取得
                    img = Image.open(io.BytesIO(img_data))
                    img = img.convert("RGB")  # JPEG用にRGBに変換
                    img.save(output_path, "JPEG", quality=95, optimize=True)
                else:
                    # その他のフォーマット（直接保存）
                    pixmap.save(str(output_path))
                
                # Pixmapのメモリを解放
                pixmap = None
                
                print(f"保存完了: {output_path}")
            
            return True
            
        except Exception as e:
            print(f"エラー: PDF分割処理中にエラーが発生しました: {e}")
            return False
    
    def process_all_pdfs(self, format: str = "png"):
        """入力ディレクトリの全PDFを処理"""
        # ディレクトリの確認・作成
        self.filesystem.ensure_directories()
        
        # PDFファイルを取得
        pdf_files = self.filesystem.get_pdf_files()
        
        if not pdf_files:
            print("処理対象のPDFファイルが見つかりません。")
            print(f"入力ディレクトリ: {self.filesystem.input_dir}")
            return
        
        print(f"{len(pdf_files)}個のPDFファイルを処理します...")
        
        for pdf_path in pdf_files:
            print(f"\n処理中: {pdf_path.name}")
            
            # PDFデータを作成・読み込み
            pdf_data = PdfData(pdf_path)
            if not pdf_data.load():
                continue
            
            print(f"ページ数: {pdf_data.page_count}")
            
            # 出力ディレクトリを作成
            output_dir = self.filesystem.create_output_dir(pdf_data.name)
            
            # PDF分割処理
            success = self.split_pdf_to_images(pdf_data, output_dir, format)
            
            # リソースをクリーンアップ
            pdf_data.close()
            
            if success:
                print(f"分割完了: {pdf_data.name} -> {output_dir}")
                
                # 処理成功時にPDFファイルをアーカイブに移動
                if self.filesystem.move_pdf_to_archive(pdf_path):
                    print(f"アーカイブ移動完了: {pdf_data.name}")
                else:
                    print(f"警告: アーカイブ移動に失敗しましたが、分割は完了しています")
            else:
                print(f"失敗: {pdf_data.name}")
        
        print("\n全ての処理が完了しました。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="PDFファイルを画像に分割")
    parser.add_argument(
        "--format", 
        default="png", 
        choices=["png", "jpg", "jpeg"],
        help="出力画像フォーマット (デフォルト: png)"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="出力解像度DPI (72-600, デフォルト: 150)"
    )
    
    args = parser.parse_args()
    
    # PDF処理を実行
    processor = PdfProcess(dpi=args.dpi)
    processor.process_all_pdfs(args.format)


if __name__ == "__main__":
    main()