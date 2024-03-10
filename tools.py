from typing import Any, Callable
from collections.abc import Iterable
from ruamel.yaml import YAML, yaml_object
from ruamel.yaml.comments import CommentedMap, CommentedSeq
import sys
yaml = YAML(typ=['rt', 'string'])
yaml.indent(mapping=2, sequence=4, offset=2)

class Tool:

    def __init__(self,
                 tool_name: str,
                 description: str,
                 func: Callable,
                 input_desc: dict[str, str] | None = None,
                 ) -> None:
        self.tool_name = tool_name
        self.description = description
        self.func = func
        self.input_desc = input_desc

    def function_schema(self, as_string=True) -> str:
        function_map = CommentedMap(tool_name=self.tool_name,
                                    tool_inputs=CommentedMap())
        function_map.yaml_add_eol_comment(self.description, "tool_name", 0)
        for arg, desc in self.input_desc.items():
            function_map["tool_inputs"][arg] = None
            function_map["tool_inputs"].yaml_add_eol_comment(desc, arg, 0)
        if as_string:
            return yaml.dump_to_string(function_map)
            # return '!Action\n' + yaml.dump_to_string(function_map)
        else:
            return function_map

    def use(self, *args, **kwargs):
        args = list(args)
        self._prep_inputs(args, kwargs)
        return str(self.func(*args, **kwargs))

    # Modify inputs if there's a 'args' keyword in `kwargs`
    def _prep_inputs(self, args, kwargs):
        if "args" not in kwargs:
            return
        else:
            it = iter(kwargs.copy().items())
            par, val = next(it)
            while par != "args":
                args.append(kwargs.pop(par))
                par, val = next(it)
            args.extend(kwargs.pop("args"))
            return


class Toolkit:
    
    def __init__(self, *args: Tool):
        if args:
            self.tools = {tool.tool_name: tool for tool in args}
        else:
            self.tools = dict()

    def add_tools(self, *args: Tool):
        self.tools.update({tool.tool_name: tool for tool in args})

    def rm_tools(self, *args: Tool | str):
        for tool in args:
            if isinstance(tool, Tool):
                del self.tools[tool.tool_name]
            elif isinstance(tool, str):
                del self.tools[tool]
            else:
                raise TypeError("Can only remove type 'Tool' or a name of type 'str'")

    def actions_available(self) -> str:
        action_map = CommentedMap()
        action_map["Actions available"] = CommentedSeq()
        action_map.yaml_add_eol_comment("list of available tools and their inputs to perform actions", "Actions available", 0)
        for tool_name, tool in self.tools.items():
            action_map["Actions available"].append(tool.function_schema())
        return yaml.dump_to_string(action_map)

