# %%

from pathlib import Path
from PIL import Image
import re
import pandas as pd
from io import StringIO

# 必要なクラスや関数のインポート
from llmInterface import GlobalConfig, ParallelLLMCaller

config = GlobalConfig("./llm/model_configs.yaml", ".env")
caller = ParallelLLMCaller(config)

root = Path("resources/files/managed")

pront = """
# task 
日本語でOCRしてください。
答えとメモを書き起こしましょう。

# info
こちらは社会の授業プリントです。
丸1番から10番+ほどまでの質問の答えが()で囲まれてかかれています。番号の右側です必ず書きなさい。
またその右側にはメモがあります。
下の方には解説の一部がありますが無視してください。

# output
csvで書きましょう。```csv と``` で囲ったcsv以外を出さないでください。
列は(id,answer,memo)です 
idは英数字のみで連続する形に、(1,2,3)
答えは一つのこさず正確に書き写しなさい。なにも書かれていないのはだめです。
memoはほとんどについています。ついていなければ""を書きましょう
ついている場合は簡潔な文章になるように元のものを少し変えて書きます。平仮名でなく漢字で置き換えるなど

例:
```csv
id,answer,memo
1,鎌倉時代,武士の政権が始まった時代
2,徳川家康,江戸幕府を開いた人物
```
"""

images = []

imgs_path = root / "R7SO/歴史"
txt_savepath = root / "R7SO/answersTXT"

# %%

# targetIMGspath配下の画像ファイルをループ
for img_path in imgs_path.iterdir():
    if img_path.is_file():
        img = Image.open(img_path)
        images.append(img)


print(f"running... {len(images)}")
responces = caller.batch_call_listIMG_sync(pront, images, "gem2f-ocr-ja")
# %%

for id, responce in enumerate(responces):
    txtpath = txt_savepath / (str(id) + ".txt")
    if not responce.result:
        print(f"no result in {id}")
        continue
    txtpath.write_text(responce.result, encoding="utf-8")
    print(f"wriote to {txtpath}")

"""
# %%
datas = []

for responce in responces:
    # `````` に囲まれた部分を抽出
    pattern = r'```csv\\s*(.*?)\\s*```'
    match = re.search(pattern, str(responce.result), re.DOTALL)
    csv_text = match.group(1).strip() if match else ""

    # DataFrameへ変換
    df = pd.read_csv(StringIO(csv_text))

    datas.append(df)


dfs_with_index = []
for i, df in enumerate(datas):
    df_copy = df.copy()
    df_copy['list_index'] = i
    dfs_with_index.append(df_copy)

result_df = pd.concat(dfs_with_index, ignore_index=True)
result_df = result_df[['list_index', 'id', 'answer', 'memo']]

print("結合後のDataFrame:")
print(result_df.head())
print(f"\n形状: {result_df.shape}")
print(f"カラム: {list(result_df.columns)}")

# 各list_indexごとの件数確認
print("\n各リストインデックスごとの件数:")
print(result_df['list_index'].value_counts().sort_index())

"""
# %%
from pathlib import Path 
import re

dirTx = Path("../resources/files/managed/R7SO/answersTXT")


for file in reversed(list(dirTx.iterdir())):
    # ファイル名から数字を抽出
    matches = list(re.finditer(r"\d+", file.name))
    if matches:
        new_name = int(matches[-1].group()) + 2
        new_name = str(new_name)
        if file.suffix:
            new_name += file.suffix
        print(new_name)
        new_path = file.parent / new_name
        file.rename(new_path)
# %%