# %%

from PIL import Image
from llmInterface import GlobalConfig, ParallelLLMCaller
from pathlib import Path
import re

root = Path("resources/files/managed/R7SO")

config = GlobalConfig("llm/model_configs.yaml", ".env")
caller = ParallelLLMCaller(config)



answerCSV = root / "answersTXT"
slides = root / "txts"
save = root / "flashcard"


paths = [answerCSV,slides,save]
for path in paths:
    if not path.is_dir():
        raise PermissionError("not dir")

answer_txts = ["csvは残念ながらない、ただし問題は11個あるので揃えるように"]
slide_txts = []

for file in answerCSV.iterdir():
    txt = file.read_text(encoding="utf-8")
    answer_txts.append(txt)


for file in slides.iterdir():
    txt = file.read_text(encoding="utf-8")
    slide_txts.append(txt)

print(len(answer_txts), len(slide_txts))


# %%
instraction = """
# csv-flashcard作成
2つのtxtを渡します。
csvの答えとスライド。
スライドの(① ~~ )が答えです。
これから質問,答え,memoのcsvを作成してもらいます。

# 注意事項
- スライド内の最大の丸数字の数以上の列を最終csvが持ってはならない、またscvと問題数を一致させなさい。
- csvの答えがないものもあります。その場合はスライドから作成してください。
- 簡潔に正しい漢字を使い行う。
- memo以外空白を許さない。

#手順
- scvの問題数と合わせてidを作成する。
- 以下ごとに繰り返す:
- 答えを書き写す、これは()で囲まれたかつ()の中に①のような丸数字が含まれるものを指す、例（⑪ フランス戦争）。また答えcsvのanswer列も対応している。それ以外は問題に含むな
- idに対応する"csvの答え"とスライドの丸数字周辺を参考にquestionを簡潔に作成する。
- memoを修正/新規作成。とても簡潔にanswer/questionに含まれる情報を含まないようにする。

# output
```csvと```で囲ったもののみ
列は(id,question,answer,memo)
id列は数字、残りは文字列""無しで書く

(
    id,  必須 1,2,3のように連番
    question,必須 スライドの文から簡潔に試験問題のように生成
    answer,必須
    memo,任意、question/answerに含まれない情報を簡潔につけたす。"csvの答え"のものが冗長で有れば編集などしてよい、任意の問題へつけたす。ように
)


# sumple
```
id,question,answer,memo
1,産業革命が最初に始まった国はどこか,イギリス,"18世紀後半～19世紀初頭"
2,産業革命期に発明された代表的な動力源は何か,蒸気機関,"ジェームズ・ワットが改良"
3,産業革命により増加した生産方式は何か,工場制機械工業,"手工業から大規模生産へ"
```
"""

prompts = [instraction + "\n\n# csvの答え\n" + answer + "\n\n# スライド\n" +
           slide for answer, slide in zip(answer_txts, slide_txts)]


# %%


savefile = save / "test.txt"


flashcard = caller.single_call_sync("gem2f-chat-ja",prompts[2])

print("call done-------------")

if not flashcard.result:
    print(f"error \n\n{flashcard.error}")
else:
    savefile.write_text(flashcard.result,encoding="utf-8")
    print(f"{flashcard.result} \nwrote to \n {savefile}")

print()
print(savefile)

# %%
results = caller.batch_call_sync(prompts, "gem2f-chat-ja")

for id,responce in enumerate(results):
    pattern = r'```csv(.*?)```'

    match = re.search(pattern, str(responce.result), re.DOTALL)
    csv_text = match.group(1).strip() if match else ""
    
    savefile = save / f"{id+1}.csv"
    savefile.write_text(csv_text,encoding="utf-8")
    print(f"savefile to {savefile}")
    
    
