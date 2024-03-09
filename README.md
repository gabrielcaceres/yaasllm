# yaasllm

`yaasllm` is a personal project with yet another agent system for LLMs. It's primarily just a for myself to play around with, test things, think about system design, and generally just have things set up how _I_ like them or believe it's more convenient.

This first iteration uses YAML to format instructions and messages. Why YAML? In part because I think it's easier to read, and feel like some of the formatting aspects might be easier for an LLM to follow (less braces and quotes, although it also has it's own formatting quirks that can be more complex). It also has some greater flexibility for some things (anchors and aliases, custom types). Considering that many models have been fine-tuned to have better JSON performance (e.g. selecting JSON output for GPT), so this is likely to perform worse. But again, just a personal project to play around with.
