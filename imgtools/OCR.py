from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import pytesseract
import os

class SimpleOCR:
    """
    pdfの場合は以下を使おう
    from pdfminer.high_level import extract_text
    """
    def __init__(self, lang='jpn'):
        self.lang = lang

    def imageOCR(self, pil_image):
        return pytesseract.image_to_string(pil_image, lang=self.lang)
    
    def fileOCR(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File '{image_path}' does not exist.")
        return pytesseract.image_to_string(image_path, lang=self.lang)
    
    def asyncOCR(self, pil_image_list):
        with ThreadPoolExecutor() as executor:
            # 各画像に対してOCRを非同期で実行
            futures = [executor.submit(self.imageOCR, image) for image in pil_image_list]
            # プログレスバーを初期化
            with tqdm(total=len(pil_image_list)) as pbar:
                results = []
                # futuresリストの順に結果を取得
                for future in futures:
                    results.append(future.result())
                    pbar.update(1)
        return results
