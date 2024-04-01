# BotsOnRails 

BotsOnRails is a flexible and lightweight Python library designed to make it easy to create complex workflows involving large language models (LLMs), human input, and arbitrary Python functions. It uses a tree-based orchestration model where each node in the tree represents a task or decision point. 

## Why use BotsOnRails?

- Easy Integration of LLMs: BotsOnRails makes it simple to integrate LLMs like OpenAI's GPT models into your workflows using libraries like Marvin.

- Human-in-the-Loop Support: BotsOnRails has first-class support for pausing execution to allow for human review and approval before proceeding. This allows you to build workflows that combine the power of LLMs with human oversight and decision making.

- Arbitrary Python Logic: In addition to LLMs, BotsOnRails allows you to incorporate arbitrary Python functions as nodes in your workflow. This gives you complete flexibility to build workflows that leverage any Python libraries or custom logic you need.

- Type-Safe: BotsOnRails uses Python type annotations to validate that data passing between nodes in your workflow matches the expected types. This catches errors before runtime.

- Dynamic Routing: Routing between nodes can be determined dynamically based on function outputs, allowing you to build workflows that adapt based on the results of each step.

- Visualization: BotsOnRails can generate visualizations of your workflow DAG to help you understand and debug your workflows.

## Examples

To see BotsOnRails in action, check out these example workflows:

- [Content Moderation](examples/content_moderation/main.py): This example shows how to build a content moderation workflow that uses an LLM to classify text content, pausing for human review if the content is flagged as inappropriate.

- [AI Stock Analysis](examples/llamaindex/main.py): This more complex example ingests a set of documents about a company's stock and uses an LLM along with the LlamaIndex library to extract key information about the stock, demonstrating more advanced workflow capabilities.

- [AI Agent Orchestration](examples/marvin/agent.py): This example demonstrates an AI agent that uses BotsOnRails to flexibly handle different user intents, leveraging tools like Marvin and custom Python functions.

## Getting Started

To use BotsOnRails in your own project, install it via:

```
pip install BotsOnRails
```

Then check out the [Quickstart Guide](quickstart.md) to learn the key concepts. The [Node Syntax Guide](node_syntax.md) dives deeper into how to define nodes and route between them.

One key concept to understand is how BotsOnRails handles looping using its [For Each Syntax](for_each_loops.md). This allows you to dynamically process each element of an iterable in a type-safe way.

BotsOnRails has some [Validation Rules](validation.md) to be aware of that enforce the integrity of your workflow definitions.

We hope you find BotsOnRails to be a powerful and flexible tool for building LLM workflows! If you have any feedback or questions, please open an issue on our GitHub repo.