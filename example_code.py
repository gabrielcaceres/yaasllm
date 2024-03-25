from dotenv import load_dotenv
import os
import openai
from typing import Annotated

from llm import msg, OpenAIChatModel
from tools import Tool, Toolkit#, Action
from agent import Agent
from math import prod

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")

llm = OpenAIChatModel()

def final_answer(answer: Annotated[str, "test"]):
    return answer


def user_input(query):
    print("please answer the request")
    return input()

# Fake function to represent web search but actually uses user input
def search(query: Annotated[str, "test"]) -> str:
    return input()

def adder(a: Annotated[int | float, "first number"],
          b: Annotated[int | float, "second number"],
          *args: Annotated[int | float, "additional numbers"],
          ):
    return a+b+sum(args)

def multiplier(*args):
    return prod(args)

def power(x, exp=2):
    return x**exp

final_answer_tool = Tool(tool_name="final answer",
                   description="use this tool to provide the final answer once you have figured it out",
                   func=final_answer,
                   input_desc=dict(answer="the final answer to return"))

user_input_tool = Tool(tool_name="user input",
                   description="use this tool to request additional details or clarification from the user",
                   func=user_input,
                   input_desc=dict(query="query to ask the user"))

search_tool = Tool(tool_name="search",
                   description="use this tool to search the web for information",
                   func=search,
                   # input_desc=dict(query="question to search"))
                   input_desc={"query":"question to search"})

power_tool = Tool(tool_name="exponentiation",
                   description="use this tool to raise a number to the given power",
                   func=power,
                   input_desc=dict(x="the value to exponentiate", exp="the power of the exponent, defaults to 2"))

adder_tool = Tool(tool_name="addition",
                   description="use this tool to add numbers",
                   func=adder,
                   input_desc=dict(a="the first number to add", b="the second number to add", args="list any additional numbers to add"))

mult_tool = Tool(tool_name="multiplier",
                   description="use this tool to multiply numbers",
                   func=multiplier,
                   input_desc=dict(args="positional arguments with numbers to multiply"))

toolkit = Toolkit(final_answer_tool, user_input_tool, search_tool, power_tool, adder_tool, mult_tool)

agent = Agent(llm_class=OpenAIChatModel,
              toolkit=toolkit)

agent.run("what is 2+3")

agent.run("what is the previous value multiplied by 2.5?")

agent.print_logic()

agent.reset_history()
agent.run("Calculate the following 2+2, 1+2+3, 4^2, 2^3. Then multiply all those values together")

agent.print_logic()
