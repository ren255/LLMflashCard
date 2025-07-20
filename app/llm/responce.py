# 基本的なimport
import litellm
from litellm import completion

# ModelResponseの正しいimport
from litellm.utils import ModelResponse
# または
import litellm.utils

"""
LiteLLMのラッパークラスで基本設定（API設定、デフォルトパラメータ）関数を提供
既にJinja2処理済みのテキスト等を受けり
ExtendedModelResponseを返すシンプルなインターフェースを提供する。
"""
