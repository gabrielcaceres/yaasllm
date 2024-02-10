from prompt import Prompt
from tools import yaml

answer_format = Prompt("""\
Step: <step>  # iteration number starting with 0
Thought: <thought>  # think step by step about what you know and what you still need to figure out
Plan: <plan>  # think about what you should do next
Action:  # list of actions to take, can be multiple at a time
  - tool_name: <tool name>:  # name of tool to use
    tool_inputs: <tool inputs>  # list inputs to selected tool
""")


sys_prompt_template = Prompt("""\
You are a helpful assistant who relies on a set of tools to help provide answers. You will think through the question, decide on an action to take and provide that to the 'user', and then build from the observation your receive as input.

Your response you be formatting as valid YAML, and everything you write should be formatted appropriately without additional commentary or explanations.

These are tools you have at your disposal for actions:
```yaml
{tool_descriptions}
```

And this is the format your answers should follow:
```yaml
---{answer_format}...
```

The 'user' will provide you with the following input showing the result of your action:
```yaml
---
Observation: <The result returned from the selected tool in Action>
...
```
""")

obs_prompt = Prompt("""\
---
Observation: {obs}
...
""")

class Agent:

    def __init__(self, llm_class, toolkit):
        sys_prompt = sys_prompt_template.format(
            answer_format=answer_format,
            tool_descriptions=toolkit.actions_available(),
        ).data
        self.llm = llm_class(system_prompt=sys_prompt)
        self.toolkit = toolkit

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
        return msg_dict['Action']

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

    def load_msg(self, msg):
        return yaml.load(msg)

    def format_obs(self, outcomes):
        obs_sep = '\n  - '
        obs = obs_sep + obs_sep.join(outcomes)
        return f"---\nObservation: {obs}\n..."
