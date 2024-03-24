from typing import Any, Callable
from collections.abc import Iterable
from ruamel.yaml import YAML, yaml_object
from ruamel.yaml.comments import CommentedMap, CommentedSeq
import sys
from dataclasses import dataclass


@dataclass
class ToolParam:
    name: str
    description: str
    default: Any | None = None
    enum: list[Any] | None = None

    def __post_init__(self):
        self.schema = {self.name: {"description": self.description}}
        if self.default:
            self.schema[self.name]["default"] = self.default
        if self.enum:
            self.schema[self.name]["enum"] = self.enum


@dataclass
class Tool:
    function: Callable
    name: str
    description: str
    params: list[ToolParam]

    def __post_init__(self):
        self.schema = {
            self.name: {"type": "Tool",
                        "description": self.description,
                        "parameters": {}
                        }
        }
        for par in self.params:
            self.schema[self.name]["parameters"].update(par.schema)

    def use(self, **kwargs):
        return self.function(**kwargs)

class Toolkit:

    def __init__(self, *args: Tool):
        if args:
            self.tools = {tool.name: tool for tool in args}
        else:
            self.tools = dict()
        self.yaml = YAML(typ=['rt', 'string'])
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.yaml.width = 4096
        self.final_action = False

    @property
    def actions_schema(self):
        schema = {}
        for tool in self.tools.values():
            schema.update(tool.schema)
        return schema

    @property
    def tool_names(self):
        return self.tools.keys()
    
    @property
    def actions_schema_formatted(self) -> str:
        return self.yaml.dump_to_string(self.actions_schema)

    def perform_actions(self, action_plan: str):
        actions = self.load_actions(action_plan)
        outcomes = list()
        self.final_action = False
        for action in actions:
            tool_name = action.get("tool_name")
            tool_inputs = action.get("tool_inputs")
            tool = self.tools[tool_name]
            tool_output = tool.use(**tool_inputs)
            outcomes.append(str(tool_output))
            if tool_name == "final answer":
                self.final_action = True
        return self.format_obs(outcomes)

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

    def load_actions(self, input: str):
        clean_input = self.clean_input_str(input)
        return self.yaml.load(clean_input)["Actions"]

    def clean_input_str(self, input: str) -> str:
        clean_input = input.strip()
        clean_input = clean_input.removeprefix("```")
        clean_input = clean_input.removeprefix("yaml")
        clean_input = clean_input.removeprefix("\n")
        clean_input = clean_input.removesuffix("\n")
        clean_input = clean_input.removesuffix("```")
        return clean_input
  
    def format_obs(self, outcomes):
        obs_sep = '\n  - '
        obs = obs_sep + obs_sep.join(outcomes)
        return f"---\nObservation: {obs}\n..."
    
    

class Tool_old:

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


class Toolkit_old:
    
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

