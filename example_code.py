from dotenv import load_dotenv
import os
import openai
from typing import Annotated

from llm import msg, OpenAIChatModel
from tools import Tool, Toolkit, ToolParam
from agent import Agent
from math import prod

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")

llm = OpenAIChatModel()

def final_answer(answer: str):
    return answer


def user_input(query: str):
    print("please answer the request")
    return input()

# Fake function to represent web search but actually uses user input
def search(query: str) -> str:
    return input()

def adder(arg_list):
    return sum(arg_list)

def multiplier(arg_list):
    return prod(arg_list)

def power(x, exp=2):
    return x**exp

final_answer_tool = Tool(
    function=final_answer,
    name="final answer",
    description="use this tool to provide the final answer once you have figured it out",
    params=[ToolParam("answer", "the final answer to return")]
)
user_input_tool = Tool(
    function=user_input,
    name="user input",
    description="use this tool to request additional details or clarification from the user",
    params=[ToolParam("query", "query to ask the user")]
)
search_tool = Tool(
    function=search,
    name = "search",
    description = "use this tool to search the web for information",
    params=[ToolParam("query", "query to search")]
)
power_tool = Tool(
    function=power,
    name = "exponentiation",
    description = "use this tool to raise a number to the given power",
    params=[ToolParam("x", "value to exponentiate"),
            ToolParam("exp", "power of the exponent", default=2),]
)
adder_tool = Tool(
    function=adder,
    name="addition",
    description="use this tool to add numbers",
    params=[ToolParam("arg_list","list of numbers to add")]
)
mult_tool = Tool(
    function=multiplier,
    name="multiplier",
    description="use this tool to multiply numbers",
    params=[ToolParam("arg_list","list of arguments with numbers to multiply")]
)

tool_list = [final_answer_tool, user_input_tool, search_tool, power_tool, adder_tool, mult_tool]

agent = Agent(llm=OpenAIChatModel(), tools=tool_list)

agent.run("what is 2+3")

agent.run("what is the previous value multiplied by 2.5?")

agent.print_logic()

agent.reset_history()
agent.run("Calculate the following 2+2, 1+2+3, 4^2, 2^3. Then multiply all those values together")

agent.print_logic()
