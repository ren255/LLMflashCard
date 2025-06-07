from PIL import Image
from llmInterface import GlobalConfig, ParallelLLMCaller
from pathlib import Path


managed = Path("resources/files/managed")
Dir = managed / "R7SO/imgs/1"

img1 = Image.open(Dir / "page_001.jpeg" )
img2 = Image.open(Dir / "page_002.jpeg")

# ========== 使用例 ==========
# 使用例：同期的な呼び出し

# 設定の初期化
config = GlobalConfig("./llm/model_configs.yaml", ".env")
caller = ParallelLLMCaller(config)

# 単一呼び出し
result = caller.single_call_sync("gem2f-ocr-ja", "Hello, how are you?")
print(result.result)

# バッチ呼び出し（プロンプトのリスト）
prompts = ["What is AI?", "Explain machine learning", "What is deep learning?"]
prompts = [pront + " answer in under 200 words" for pront in prompts]
results = caller.batch_call_sync(prompts, "gem2f-ocr-ja")
caller.print_results(results)

# バッチ呼び出し（辞書）
prompt_dict = {
    "What is Python?": None,
    "Describe this image": img2,
}
results = caller.batch_call_dict_sync(prompt_dict, "gem2f-ocr-ja")
caller.print_results(results)

# バッチ呼び出し（画像リスト）
images = [img1, img2]  # PIL.Imageのリスト
results = caller.batch_call_listIMG_sync(
    "この画像を説明してください", images, "gem2f-ocr-ja")
caller.print_results(results)
