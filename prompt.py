from textwrap import dedent
from string import Formatter
from collections import UserString
from functools import cached_property
import logging


class PartialFillDict(dict):
    def __missing__(self, key):
        return f"{{{key}}}"


class Prompt(UserString):
    def __init__(self, text: str, dedent_text: bool = True):
        self.dedent_text = dedent_text
        if isinstance(text, Prompt):
            text = text.data
        if dedent_text:
            text = dedent(text)
        super().__init__(text)    

    def dedent(self):
        return Prompt(dedent(self))

    def format_map(self, arg_dict: dict, partial: bool = False):
        if partial:
            arg_dict = PartialFillDict(**arg_dict)
        return Prompt(self.data.format_map(arg_dict), dedent_text=self.dedent_text)

    def format(self, *args, partial: bool = False, **kwargs):
        if partial:
            return self.format_map(kwargs, partial=partial)
        else:
            return Prompt(self.data.format(*args, **kwargs), dedent_text=self.dedent_text)
   
    @cached_property
    def arg_list(self):
        return [arg for _, arg, _, _ in Formatter().parse(self.data) if arg is not None]
    
    @cached_property
    def token_count(self):
        # Not implemented yet
        pass
    
    __call__ = format
