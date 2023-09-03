import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt


def msg(prompt: str, role: str = "user", **kwargs) -> dict:
    return dict(role=role, content=prompt, **kwargs)


class OpenAIChatModel:

    def __init__(self, model="gpt-3.5-turbo", system_prompt="", **kwargs):
        self.model = model
        self.system_prompt = system_prompt
        self.openai_args = dict(model=model, **kwargs)
        self.last_run = None

    def generate(self, messages, **kwargs):
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
        
