from PIL import Image
from llmInterface import GlobalConfig, ParallelLLMCaller
import asyncio
import nest_asyncio

# nest_asyncioを適用
nest_asyncio.apply()

config = GlobalConfig("llm\\model_configs.yaml", ".env")
llm = ParallelLLMCaller(config)


async def main():
    # プロンプト + 画像
    img1 = Image.open("resources/FileSystem/save/pdf_img/歴史/page_001.jpeg")
    img2 = Image.open("resources/FileSystem/save/pdf_img/歴史/page_002.jpeg")

    prompt_images = {
        "この画像を説明してください": img1,
        "何が写っていますか？": img2,
        "テキストのみの質問": None
    }

    # プロンプトのみ（既存機能）
    print("calling...")
    results1 = await llm.batch_call(["こんにちは偏差値なにでうｓか？", "質問2"], "gem2f-chat-ja")

    print("=== プロンプトのみの結果 ===")
    for i in results1:
        print(i)

    results2=await llm.batch_call_dict(prompt_images, "gem2f-ocr-ja")


    print("\n=== プロンプト + 画像の結果 ===")
    for i in results2:
        print(i)

# 方法1: asyncio.run()を使用
if __name__ == "__main__":
    asyncio.run(main())

# 方法2: nest_asyncioを活用してワンライナー実行
# asyncio.run(main())
