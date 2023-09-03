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
    ) -> Any:
        self.model = model
        self.system_prompt = system_prompt
        self.openai_args = dict(model=model, **kwargs)
        self.last_run = None

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
            prompt: str,
            **kwargs: Any
    ) -> list[str]:
        messages = [msg(self.system_prompt, "system"),
                    msg(prompt, "user")]
        responses = self.generate(messages, **kwargs)
        return responses
