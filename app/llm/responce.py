# 基本的なimport
import litellm
from litellm import acompletion, completion

# ModelResponseの正しいimport
from litellm import ModelResponse ,  ,completion


"""
LiteLLMのラッパークラスで基本設定（API設定、デフォルトパラメータ）関数を提供
既にJinja2処理済みのテキスト等を受けり
from litellm.utils import ModelResponseを持つExtendedModelResponseを返すシンプルなインターフェースを提供する。
内部はLLM呼び出しobj(from litellm.utils import completion)の作成とそれの簡単な呼び出しとacync呼び出し
それぞれ1~Nこのcompletionの受け取りに対応しているまたacync関数をawait無しで使えるcompletionもある。
結果としてLLM呼び出し関数は2+1つのrapper
builderは大量にある。単一objを生成するものを集めたclassとバッチでobjを生成するclass
"""
