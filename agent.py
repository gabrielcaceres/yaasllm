from typing import Optional
from prompt import Prompt
from tools import yaml
from llm import msg

# answer_format = Prompt("""\
# ```yaml
# ---
# Step: <step>  # iteration number starting with 0
# Thought: > <thought>  # think step by step about what you know and what you still need to figure out
# Plan: > <plan>  # think about what you should do next
# Actions:  # list of actions to take, can be multiple at a time
#   - tool_name: <tool name>  # name of tool to use
#     tool_inputs: <tool inputs>  # list inputs to selected tool
# ...
# ```
# """)
answer_format = Prompt("""\
```yaml
---
!!map
Step:  # iteration number for the current task, starting with 0. Increase as you perform more steps, reset to 0 after reaching the final answer and starting a new task
Knowledge: |  # review the facts you currently know and what you still need to figure out
Plan: |  # think step by step about what you should do next
Actions: !!seq  # list of actions to take, can be multiple at a time
  -
    tool_name: !!str  # name of tool to use
    tool_inputs: !!map  # inputs to selected tool
...
```
""")
# Temporarily removing Reference to anchor
# &{label}  # unique label to reference the output of this action

example_action = Prompt("""\
---
Stage: 0
Knowledge: |
  - I don't have any information yet.
  - I need to determine a task to perform.
Plan: |
  - Ask the user what to do next.
Actions: 
  - !Action
    tool_name: user input
    tool_inputs:
      query: What can I do for you?
...
"""
)


obs_prompt = Prompt("""\
---
Observations: {obs}
...
""")

obs_format = obs_prompt(obs="<observations> # the results returned from the selected Actions")

sys_prompt_template = Prompt("""\
You are a helpful assistant who relies on a set of tools to help provide answers. You will think through the question, decide on an action to take and provide that to the 'user', and then build from the observation your receive as input.

Your response you be formatting as valid YAML, and everything you write should be formatted appropriately without additional commentary or explanations.

These are tools you have at your disposal for actions:
```yaml
{tool_descriptions}
```

The following code block shows the format your answers should follow:
{answer_format}

The 'user' will provide you with the following input showing the result of your action:
```yaml
{obs_format}
```
""")

# Placeholder instructions about using anchors
# currently not set up to be able to evaluate
# You can use YAML anchors (`&`) to label values and aliases (`*`) to reference labels with any previous values you want to reuse. Follow the syntax from the standard YAML specification.


class Agent:

    def __init__(self, llm_class, toolkit):
        sys_prompt = sys_prompt_template.format(
            answer_format=answer_format,
            tool_descriptions=toolkit.actions_available(),
            obs_format=obs_format,
        ).data
        self.llm = llm_class(system_prompt=sys_prompt)
        self.toolkit = toolkit
        self.llm.chat_history = [msg(example_action.data, "assistant")]

    def run(self, query):
        msg = self.llm.chat(obs_prompt.format(obs=query).data)
        actions = self.get_actions(msg)
        while "final answer" not in self.get_tool_list(actions):
            outcomes = self.use_tools(actions)
            observations = self.format_obs(outcomes)
            msg = self.llm.chat(observations)
            actions = self.get_actions(msg)
        return self.use_tools(actions)

    def get_actions(self, msg):
        msg_dict = self.load_msg(msg)
        return msg_dict['Actions']

    def get_tool_list(self, actions):
        return [action.get("tool_name") for action in actions]
    
    def use_tools(self, actions):
        outcomes = list()
        for action in actions:
            tool_name = action.get("tool_name")
            tool_inputs = action.get("tool_inputs")
            tool = self.toolkit.tools[tool_name]
            tool_output = tool.use(**tool_inputs)
            outcomes.append(tool_output)
        return outcomes

    def load_msg(self, msg: str):
        clean_msg = msg.removeprefix("```")
        clean_msg = clean_msg.removeprefix("yaml")
        clean_msg = clean_msg.removeprefix("\n")
        clean_msg = clean_msg.removesuffix("\n")
        clean_msg = clean_msg.removesuffix("```")
        return yaml.load(clean_msg)

    def format_obs(self, outcomes):
        obs_sep = '\n  - '
        obs = obs_sep + obs_sep.join(outcomes)
        return f"---\nObservation: {obs}\n..."

    def print_logic(self):
        print(self.llm.chat_history)
