from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict
import asyncio

from .llm_types import LLMLiteConfig, build_Config


class RequestBuilder:
    def __init__(self, config) -> None:
        self.set_config(config)

    def set_config(self, config: LLMLiteConfig) -> None:
        self.config = config
        self.base_dict = asdict(config)

    def _build_request(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        req = self.base_dict.copy()
        req.update(kwargs)
        req["messages"] = messages
        return req

    def _build_messages(self, user_message: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})
        return messages

    # public bulders

    def build_single(self, message: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        msgs = self._build_messages(message, system_prompt)
        return self._build_request(msgs, **kwargs)

    def build_batch(self, messages: List[str], system_prompt: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        return [self.build_single(msg, system_prompt, **kwargs) for msg in messages]

    def build_with_image_single(self, message: str, image_path: str,
                                system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        msgs = self._build_messages(message, system_prompt)
        return self._build_request(msgs, image_paths=[image_path], **kwargs)

    def build_with_images_batch(self, messages: List[str], image_paths: List[str],
                                system_prompt: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        return [
            self.build_with_image_single(
                msg, img_path, system_prompt, **kwargs)
            for msg, img_path in zip(messages, image_paths)
        ]


if __name__ == "__main__":
    from .LiteLLMWrapper import LLMWrapper
    builder = RequestBuilder(build_Config("kimi2"))
    reqs = builder.build_batch(["testです名前何？", "22222222222番目のプロントですよ"])
    for req in reqs:
        print(req)

    print()
    tasks = LLMWrapper.allmcall_batch(reqs)
    results  = LLMWrapper.run_tasks(tasks)
    for res in results:
        print(res)
