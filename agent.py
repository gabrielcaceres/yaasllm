from typing import Optional
from prompt import Prompt
from tools import Toolkit
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
  - &{label}  # unique label to reference the output of this action
    tool_name: !!str  # name of tool to use
    tool_inputs: !!map  # inputs to selected tool
...
```
""")

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

sys_prompt_template = Prompt("""\
You are a helpful assistant who relies on a set of tools to help provide answers. You will think through the question, decide on an action to take and provide that to the 'user', and then build from the observation your receive as input.

Your response you be formatting as valid YAML, and everything you write should be formatted appropriately without additional commentary or explanations.

These are tools you have at your disposal for actions:
```yaml
{tool_descriptions}
```

The following code block shows the format your answers should follow:
{answer_format}

You can use YAML anchors (`&`) to label values and aliases (`*`) to reference labels with any previous values you want to reuse. Follow the syntax from the standard YAML specification.

The 'user' will provide you with the following input showing the result of your action:
```yaml
---
Observations: <observations> # the results returned from the selected Actions
...
```
""")

obs_prompt = Prompt("""\
---
Observations: {obs}
...
""")

class Agent:

    def __init__(self,
                 llm,
                 tools: list[Tool],
                 system_prompt: Prompt | str | None = None,
                 init_history = None,
                 ):
        self.llm = llm
        self.toolkit = Toolkit(*tools)
        self.system_prompt = system_prompt or llm.system_prompt
        self.init_history = init_history or []
        self.history = init_history or []

    # @property
    # def tool_list(self):
    #     return self.toolkit.tool_list

    @property
    def system_prompt(self):
        return self.llm.system_prompt

    @system_prompt.setter
    def system_prompt(self, new_system_prompt):
        self.llm.system_prompt = new_system_prompt

    @property
    def history(self):
        return self.llm.chat_history

    @history.setter
    def history(self, new_history):
        self.llm.chat_history = new_history

    def add_to_history(self, msg):
        self.llm.chat_history.append(msg)

    def reset_history(self):
        self.history = self.init_history

    def clear_history(self):
        self.history = []

    def run(self, task: Prompt | str, reset_history = True):
        if reset_history:
            self.reset_history()
        action_plan = self.determine_actions(task)
        outcome = self.execute(action_plan)
        while not self.is_final_action():
            action_plan = self.determine_actions(outcome)
            outcome = self.execute(action_plan)
        return outcome

    def determine_actions(self, context):
        response = self.llm.chat(obs_prompt.format(obs=context).data)
        return response

    def execute(self, action_plan):
        outcome = self.toolkit.perform_actions(action_plan)
        return

    def is_final_action(self):
        return self.toolkit.final_action


class Agent_old:

    def __init__(self, llm, toolkit):
        sys_prompt = sys_prompt_template.format(
            answer_format=answer_format,
            tool_descriptions=toolkit.actions_available(),
        ).data
        self.llm = llm_class(system_prompt=sys_prompt)
        self.toolkit = toolkit
        self.llm.chat_history = [msg(example_action.data, "assistant")]

    def run(self, query):
        msg = self.llm.chat(obs_prompt.format(obs=query).data)
        print(msg)
        actions = self.get_actions(msg)
        while "final answer" not in self.get_tool_list(actions):
            outcomes = self.use_tools(actions)
            observations = self.format_obs(outcomes)
            print(observations)
            msg = self.llm.chat(observations)
            print(msg)
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

    # def load_msg(self, msg: str):
    #     clean_msg = msg.removeprefix("```")
    #     clean_msg = clean_msg.removeprefix("yaml")
    #     clean_msg = clean_msg.removeprefix("\n")
    #     clean_msg = clean_msg.removesuffix("\n")
    #     clean_msg = clean_msg.removesuffix("```")
    #     print("cleaned message")
    #     print(clean_msg)
    #     print("end cleaned message")
    #     print("Commented map")
    #     print(yaml.load(clean_msg))
    #     print("end Commented map")
    #     return yaml.load(clean_msg)

    def format_obs(self, outcomes):
        obs_sep = '\n  - '
        obs = obs_sep + obs_sep.join(outcomes)
        return f"---\nObservation: {obs}\n..."
