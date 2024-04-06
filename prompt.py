from textwrap import dedent
from string import Formatter
from typing import Literal
from collections import UserString
from functools import cached_property
import logging


class PartialFillDict(dict):
    def __missing__(self, key):
        return f"{{{key}}}"

class Prompt(str):
    dedented: bool
    stripped: Literal["both", "left", "right", None]
    
    def __new__(cls, prompt: str, *, dedented: bool = True, stripped: Literal["both", "left", "right", None] = "both"):
        # If already of class `Prompt`, return unchanged
        if isinstance(prompt, Prompt):
            return prompt
        clean_prompt = prompt
        if dedented:
            clean_prompt = dedent(clean_prompt)
        if stripped == "both":
            clean_prompt = clean_prompt.strip()
        elif stripped == "left":
            clean_prompt = clean_prompt.lstrip()
        elif stripped == "right":
            clean_prompt = clean_prompt.rstrip()
        instance = super().__new__(cls, clean_prompt)
        instance.dedented = dedented
        instance.stripped= stripped
        return instance

    def dedent(self):
        return Prompt(str(self), dedented = True, stripped = self.stripped)

    def format_map(self, arg_dict: dict, *, partial: bool = False):
        if partial:
            arg_dict = PartialFillDict(**arg_dict)
        return Prompt(super().format_map(arg_dict), dedent_text=self.dedent_text)

    def format(self, *args, partial: bool = False, **kwargs):
        if partial:
            return self.format_map(kwargs, partial=partial)
        else:
            return Prompt(str(self).format(*args, **kwargs), dedented = self.dedented, stripped = self.stripped)
   
    @cached_property
    def arg_list(self):
        # Check if there are placeholders to fill
        return [arg for _, arg, _, _ in Formatter().parse(self) if arg is not None]

    @cached_property
    def is_template(self):
        # If there are variables that can be filled, then prompt is a template
        if self.arg_list:
            return True
        else:
            return False
    
    @cached_property
    def token_count(self):
        # Not implemented yet
        pass

    __call__ = format
