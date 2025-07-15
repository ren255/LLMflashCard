#!/usr/bin/env python3
"""
PDF処理スクリプト（改良版）
PDFファイルをページごとにPNG画像に分割する
- 個別PDFファイル指定対応
- プログレスバー表示
- 予想時間表示
"""

import sys
import argparse
import time
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
from PIL import Image
import io
from tqdm import tqdm


class ProgressTracker:
    """進捗追跡とプログレスバー管理クラス"""

    def __init__(self):
        self.start_time = None
        self.total_pages = 0
        self.processed_pages = 0
        self.pdf_progress_bar = None
        self.page_progress_bar = None

    def start_tracking(self, total_pdfs: int, total_pages: int):
        """追跡開始"""
        self.start_time = time.time()
        self.total_pages = total_pages
        self.processed_pages = 0

        # 上段プログレスバー（PDF単位）
        self.pdf_progress_bar = tqdm(
            total=total_pdfs,
            desc="PDF処理",
            position=0,
            unit="file"
        )

    def start_pdf_processing(self, pdf_name: str, page_count: int):
        """PDF処理開始"""
        # 下段プログレスバー（ページ単位）
        self.page_progress_bar = tqdm(
            total=page_count,
            desc=f"ページ分割: {pdf_name}",
            position=1,
            leave=False,
            unit="page"
        )

    def update_page_progress(self):
        """ページ処理進捗更新"""
        if self.page_progress_bar:
            self.page_progress_bar.update(1)

        self.processed_pages += 1

        # 予想時間計算と表示
        if self.processed_pages > 0 and self.start_time:
            elapsed_time = time.time() - self.start_time
            avg_time_per_page = elapsed_time / self.processed_pages
            remaining_pages = self.total_pages - self.processed_pages
            estimated_remaining = avg_time_per_page * remaining_pages

            # プログレスバーの説明に予想時間を追加
            if self.page_progress_bar:
                self.page_progress_bar.set_postfix({
                    'ETA': f'{int(estimated_remaining)}s'
                })

    def finish_pdf_processing(self):
        """PDF処理完了"""
        if self.page_progress_bar:
            self.page_progress_bar.close()
            self.page_progress_bar = None

        if self.pdf_progress_bar:
            self.pdf_progress_bar.update(1)

    def finish_tracking(self):
        """追跡終了"""
        if self.pdf_progress_bar:
            self.pdf_progress_bar.close()

        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"\n総処理時間: {total_time:.2f}秒")
            if self.total_pages > 0:
                print(f"1ページあたりの平均時間: {total_time/self.total_pages:.2f}秒")


class FileSystem:
    """ファイルシステム操作を管理するクラス"""

    def __init__(self):
        self.base_path = Path("resources")
        self.input_dir = self.base_path / "files" / "in"
        self.output_base_dir = self.base_path / \
            "files" / "managed" / "pdf_img"
        self.pdf_archive_dir = self.base_path / \
            "files" / "managed" / "pdf"

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

    def validate_pdf_file(self, pdf_path: str) -> Optional[Path]:
        """指定されたPDFファイルの存在確認"""
        path = Path(pdf_path)

        if not path.exists():
            print(f"エラー: ファイルが見つかりません: {pdf_path}")
            return None

        if path.suffix.lower() != '.pdf':
            print(f"エラー: PDFファイルではありません: {pdf_path}")
            return None

        return path

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
                archive_path = self.pdf_archive_dir / \
                    f"{name_part}_{counter:03d}{extension}"
                counter += 1

            # ファイルを移動
            pdf_path.rename(archive_path)
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
        self.progress_tracker = ProgressTracker()

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
                            format: str = "jpeg") -> bool:
        """PDFを画像に分割"""
        try:
            # PDF処理開始
            self.progress_tracker.start_pdf_processing(
                pdf_data.name, pdf_data.page_count)

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
                    tqdm.write(f"警告: ページ {page_num + 1} のPixmap生成に失敗しました")
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

                # 進捗更新
                self.progress_tracker.update_page_progress()

            # PDF処理完了
            self.progress_tracker.finish_pdf_processing()
            return True

        except Exception as e:
            print(f"エラー: PDF分割処理中にエラーが発生しました: {e}")
            return False

    def count_total_pages(self, pdf_files: List[Path]) -> int:
        """総ページ数をカウント"""
        total_pages = 0
        print("ページ数を計算中...")

        for pdf_path in pdf_files:
            try:
                with fitz.open(pdf_path) as doc:
                    total_pages += len(doc)
            except Exception as e:
                print(f"警告: {pdf_path.name} のページ数取得に失敗: {e}")

        return total_pages

    def process_single_pdf(self, pdf_path: str, format: str = "jpeg"):
        """単一PDFファイルを処理"""
        # ディレクトリの確認・作成
        self.filesystem.ensure_directories()

        # PDFファイルの検証
        validated_path = self.filesystem.validate_pdf_file(pdf_path)
        if not validated_path:
            return

        pdf_files = [validated_path]

        # 総ページ数計算
        total_pages = self.count_total_pages(pdf_files)
        if total_pages == 0:
            print("処理対象のページが見つかりません。")
            return

        # 進捗追跡開始
        self.progress_tracker.start_tracking(1, total_pages)

        print(f"処理開始: {validated_path.name} ({total_pages}ページ)")

        # PDFデータを作成・読み込み
        pdf_data = PdfData(validated_path)
        if not pdf_data.load():
            self.progress_tracker.finish_tracking()
            return

        # 出力ディレクトリを作成
        output_dir = self.filesystem.create_output_dir(pdf_data.name)

        # PDF分割処理
        success = self.split_pdf_to_images(pdf_data, output_dir, format)

        # リソースをクリーンアップ
        pdf_data.close()

        if success:
            tqdm.write(f"分割完了: {pdf_data.name} -> {output_dir}")

            # 処理成功時にPDFファイルをアーカイブに移動
            if self.filesystem.move_pdf_to_archive(validated_path):
                tqdm.write(f"アーカイブ移動完了: {pdf_data.name}")
            else:
                tqdm.write(f"警告: アーカイブ移動に失敗しましたが、分割は完了しています")
        else:
            tqdm.write(f"失敗: {pdf_data.name}")

        # 進捗追跡終了
        self.progress_tracker.finish_tracking()
        print("処理が完了しました。")

    def process_all_pdfs(self, format: str = "jpeg"):
        """入力ディレクトリの全PDFを処理"""
        # ディレクトリの確認・作成
        self.filesystem.ensure_directories()

        # PDFファイルを取得
        pdf_files = self.filesystem.get_pdf_files()

        if not pdf_files:
            print("処理対象のPDFファイルが見つかりません。")
            print(f"入力ディレクトリ: {self.filesystem.input_dir}")
            return

        # 総ページ数計算
        total_pages = self.count_total_pages(pdf_files)
        if total_pages == 0:
            print("処理対象のページが見つかりません。")
            return

        # 進捗追跡開始
        self.progress_tracker.start_tracking(len(pdf_files), total_pages)

        print(f"{len(pdf_files)}個のPDFファイル ({total_pages}ページ) を処理します...")

        for pdf_path in pdf_files:
            # PDFデータを作成・読み込み
            pdf_data = PdfData(pdf_path)
            if not pdf_data.load():
                self.progress_tracker.finish_pdf_processing()
                continue

            # 出力ディレクトリを作成
            output_dir = self.filesystem.create_output_dir(pdf_data.name)

            # PDF分割処理
            success = self.split_pdf_to_images(pdf_data, output_dir, format)

            # リソースをクリーンアップ
            pdf_data.close()

            if success:
                tqdm.write(f"分割完了: {pdf_data.name} -> {output_dir}")

                # 処理成功時にPDFファイルをアーカイブに移動
                if self.filesystem.move_pdf_to_archive(pdf_path):
                    tqdm.write(f"アーカイブ移動完了: {pdf_data.name}")
                else:
                    tqdm.write(f"警告: アーカイブ移動に失敗しましたが、分割は完了しています")
            else:
                tqdm.write(f"失敗: {pdf_data.name}")

        # 進捗追跡終了
        self.progress_tracker.finish_tracking()
        print("全ての処理が完了しました。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="PDFファイルを画像に分割")
    parser.add_argument(
        "pdf_file",
        nargs="?",
        help="処理するPDFファイルのパス（省略時は入力ディレクトリの全PDFを処理）"
    )
    parser.add_argument(
        "-f", "--format",
        default="jpeg",
        choices=["png", "jpg", "jpeg"],
        help="出力画像フォーマット (デフォルト: jpeg)"
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

    if args.pdf_file:
        # 単一PDFファイル処理
        processor.process_single_pdf(args.pdf_file, args.format)
    else:
        # 全PDFファイル処理
        processor.process_all_pdfs(args.format)


if __name__ == "__main__":
    main()
