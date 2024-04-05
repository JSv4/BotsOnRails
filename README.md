# BotsOnRails

BotsOnRails was born out of a frustration with the challenges of building complex workflows involving large language 
models (LLMs), human interaction, and custom logic. As LLMs like GPT-3 and GPT-4 have become more powerful and 
accessible, there's been an explosion of interest in building applications that leverage their capabilities. However, 
building these applications often requires orchestrating a complex dance between AI-generated content, human review 
and approval, and custom processing logic.

Existing workflow orchestration tools, while powerful, often feel overly complex and rigid for these kinds of 
AI-driven workflows. They require a lot of upfront design and don't easily accommodate the kinds of dynamic, 
human-in-the-loop workflows that are common when working with LLMs.

At the same time, building these workflows from scratch using raw Python code quickly becomes unmanageable. The flow of 
data and control between different parts of the system becomes hard to follow, and it's easy for subtle bugs and 
inconsistencies to creep in.

BotsOnRails was created to provide a sweet spot between these two extremes. It offers a simple, flexible, and 
expressive way to define workflows as trees of nodes, where each node represents a single step or decision point. 
Crucially, it has first-class support for human interaction, allowing you to easily designate any node as a pause 
point for human review or approval.

# Key Features:

1. **Tree-based orchestration**: Define complex workflows as execution trees with nodes representing tasks or decisions.
2. **Human-in-the-loop**: Seamlessly integrate human input and approvals into automated workflows.
3. **Dynamic routing**: Route execution flow based on runtime data or conditions using functions or static mappings.
4. **Type checking**: Ensure type safety and compatibility between nodes for robust execution.
5. **Visualization**: Generate visual representations of your execution trees for analysis and debugging.
6. **Resumable execution**: Restart or continue execution from specific nodes for iterative review and modification.
7. **Lightweight and flexible**: Easy to integrate into existing projects and adapt to various use cases.

# Installation:

## Prerequisites 

You need to install graphviz, which has different installation methods depending on your system.

### Windows

We'd suggest using the .exe installer from the 
[official graphviz website](https://graphviz.org/doc/winbuild.html).

### Linux

If you're using Ubuntu or another Debian derivative, try using apt like so:

```requirements
sudo apt install graphviz 
```

### MacOS

There are a number of ways to install graphviz on Mac. For example, you can use homebrew:

```requirements
brew install graphviz
```

## Install BotsOnRails

You can install the package directly from PyPi using pip:

```commandline
pip install BotsOnRails
```

# Docs & Quickstart:

Check out our [extensive documentation](https://jsv4.github.io/BotsOnRails/) (still a work in progress).

# Examples

We have a number of examples that illustrate how to build some common LLM-powered applications using BotsOnRails:
1. [Document Processing Pipeline](docs/examples/llamaindex)
2. [Human-in-the-loop Content Moderation](docs/examples/content_moderation)
3. [LLM-Powered Interface](docs/examples/marvin)

# Contributing:

Contributions are welcome! Please see the contributing guidelines in the GitHub repository.

# License:

BotsOnRails is licensed under the MIT License.