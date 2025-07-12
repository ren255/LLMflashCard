from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import pytesseract
import os
import argparse
from pathlib import Path
from PIL import Image
from pdfminer.high_level import extract_text
import fitz  # PyMuPDF for PDF to image conversion

class SimpleOCR:
    """
    Enhanced OCR class with PDF and batch processing support
    """
    def __init__(self, lang='jpn'):
        self.lang = lang
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
        
    def imageOCR(self, pil_image):
        """PIL画像からOCRでテキストを抽出"""
        return pytesseract.image_to_string(pil_image, lang=self.lang)
    
    def fileOCR(self, image_path):
        """画像ファイルからOCRでテキストを抽出"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File '{image_path}' does not exist.")
        return pytesseract.image_to_string(image_path, lang=self.lang)
    
    def pdfOCR(self, pdf_path):
        """PDFファイルからOCRでテキストを抽出（画像化してOCR）"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File '{pdf_path}' does not exist.")
        
        # まず既存テキストの抽出を試行
        try:
            extracted_text = extract_text(pdf_path)
            if extracted_text and extracted_text.strip():
                return extracted_text
        except Exception:
            pass
        
        # テキストが抽出できない場合は画像に変換してOCR
        doc = fitz.open(pdf_path)
        all_text = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            mat = fitz.Matrix(2, 2)  # 2倍のズーム
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            # PIL Imageに変換
            from io import BytesIO
            pil_image = Image.open(BytesIO(img_data))
            
            # OCR実行
            text = self.imageOCR(pil_image)
            all_text.append(text)
        
        doc.close()
        return '\n'.join(all_text)
    
    def asyncOCR(self, pil_image_list):
        """PIL画像のリストを非同期でOCR処理"""
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.imageOCR, image) for image in pil_image_list]
            with tqdm(total=len(pil_image_list), desc="OCR処理中") as pbar:
                results = []
                for future in futures:
                    results.append(future.result())
                    pbar.update(1)
        return results
    
    def process_folder(self, folder_path, process_pdf=True, process_img=False):
        """フォルダ内のファイルを処理"""
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder '{folder_path}' does not exist.")
        
        files_to_process = []
        
        if process_pdf:
            pdf_files = list(folder_path.glob("*.pdf"))
            files_to_process.extend([(f, 'pdf') for f in pdf_files])
        
        if process_img:
            for ext in self.supported_image_formats:
                img_files = list(folder_path.glob(f"*{ext}"))
                files_to_process.extend([(f, 'img') for f in img_files])
        
        if not files_to_process:
            print("処理対象のファイルが見つかりません。")
            return
        
        # 出力フォルダの作成
        output_base = Path("resources/FileSystem/save/txt")
        output_folder = output_base / folder_path.name
        output_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"処理対象ファイル数: {len(files_to_process)}")
        
        with ThreadPoolExecutor() as executor:
            futures = []
            for file_path, file_type in files_to_process:
                if file_type == 'pdf':
                    future = executor.submit(self._process_pdf_file, file_path, output_folder)
                else:
                    future = executor.submit(self._process_image_file, file_path, output_folder)
                futures.append((future, file_path.name))
            
            with tqdm(total=len(futures), desc="ファイル処理中") as pbar:
                for future, filename in futures:
                    try:
                        future.result()
                        pbar.set_postfix(file=filename)
                    except Exception as e:
                        print(f"エラー: {filename} - {str(e)}")
                    pbar.update(1)
        
        print(f"処理完了。出力フォルダ: {output_folder}")
    
    def _process_pdf_file(self, pdf_path, output_folder):
        """PDFファイルを処理してテキストファイルに保存"""
        try:
            text = self.pdfOCR(pdf_path)
            output_file = output_folder / f"{pdf_path.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            raise Exception(f"PDF処理エラー: {str(e)}")
    
    def _process_image_file(self, image_path, output_folder):
        """画像ファイルを処理してテキストファイルに保存"""
        try:
            text = self.fileOCR(image_path)
            output_file = output_folder / f"{image_path.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            raise Exception(f"画像処理エラー: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description="フォルダ内のPDFや画像ファイルをOCR処理してテキストファイルに出力",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python ocr_tool.py /path/to/folder              # PDFファイルのみ処理（デフォルト）
  python ocr_tool.py /path/to/folder --pdf        # PDFファイルのみ処理
  python ocr_tool.py /path/to/folder --img        # 画像ファイルのみ処理
  python ocr_tool.py /path/to/folder --pdf --img  # PDFと画像の両方を処理
        """
    )
    
    parser.add_argument(
        'folder_path',
        help='処理対象のフォルダパス'
    )
    
    parser.add_argument(
        '--pdf',
        action='store_true',
        default=True,
        help='PDFファイルを処理する（デフォルト）'
    )
    
    parser.add_argument(
        '--img',
        action='store_true',
        default=False,
        help='画像ファイルを処理する'
    )
    
    parser.add_argument(
        '--lang',
        default='jpn',
        help='OCR言語設定（デフォルト: jpn）'
    )
    
    args = parser.parse_args()
    
    # --imgが指定された場合、--pdfは明示的に指定されない限りFalseにする
    if args.img and not any(arg in ['--pdf'] for arg in os.sys.argv):
        args.pdf = False
    
    try:
        ocr = SimpleOCR(lang=args.lang)
        ocr.process_folder(args.folder_path, process_pdf=args.pdf, process_img=args.img)
    except Exception as e:
        print(f"エラー: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())