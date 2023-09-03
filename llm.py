from typing import Any
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt


def msg(
        prompt: str,
        role: str = "user",
        **kwargs: Any
) -> dict[str, Any]:
    return dict(role=role, content=prompt, **kwargs)


class OpenAIChatModel:

    def __init__(
            self,
            model: str = "gpt-3.5-turbo",
            system_prompt: str = "",
            **kwargs: Any
    ) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self.openai_args = dict(model=model, **kwargs)
        self.last_run = None
        self.chat_history = [ ]

    @retry(wait=wait_random_exponential(min=1, max=60),
           stop=stop_after_attempt(6))
    def generate(
            self,
            messages: list[dict[str, str]],
            **kwargs: Any
    ) -> list[str]:
        openai_args = self.openai_args.copy()
        openai_args.update(kwargs)
        response_object = openai.ChatCompletion.create(messages=messages, **openai_args)
        responses = [i['message']['content'] for i in response_object['choices']]
        self.last_run = dict(
            messages=messages.copy(),
            responses=responses.copy(),
            openai_args=openai_args.copy(),
            response_object=response_object.copy(),
        )
        return responses

    def __call__(
            self,
            prompt: str | None,
            **kwargs: Any
    ) -> list[str]:
        self.clear_chat()
        messages = [msg(self.system_prompt, "system")]
        if prompt:
            messages.append(msg(prompt, "user"))
            self.chat_history.append(msg(prompt, "user"))           responses = self.generate(messages, **kwargs)
        self.chat_history.append(msg(responses[0], "assistant"))
        return responses

    def chat(
            self,
            prompt: str | None,
            **kwargs: Any
    ) -> str:
        if prompt:
            self.chat_history.append(msg(prompt, "user"))           system_msg = msg(self.system_prompt, "system")
        response = self.generate([system_msg] + self.chat_history, **kwargs)[0]
        self.chat_history.append(msg(response, "assistant"))
        return response

    def clear_chat(self) -> None:
        self.chat_history = [ ]

