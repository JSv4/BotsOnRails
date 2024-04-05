# About BotsOnRails

## Origins

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

## Why BotsOnRails?

So why should you care about BotsOnRails? Here are a few key benefits:

1. **Simplicity**: BotsOnRails offers a simple and intuitive way to define even complex workflows. The core concepts - nodes, routing, human approval - are easy to grasp, but combine to enable very sophisticated behavior.

2. **Flexibility**: BotsOnRails imposes very few constraints on what your nodes can do. A node can invoke an LLM, make a database query, call an API, prompt for human input, or run arbitrary Python code. This flexibility means you can use BotsOnRails for a wide variety of use cases.

3. **Visibility**: BotsOnRails can generate visualizations of your workflow tree, making it easy to see at a glance how data and control flow through your system. This can be invaluable for understanding, debugging, and communicating about your workflows.

4. **Resumability**: BotsOnRails makes it easy to create workflows that can be paused for human interaction and then seamlessly resumed. This is a game-changer when building human-in-the-loop AI systems, as it means the human can be brought into the loop at any point without disrupting the overall flow.

5. **Type Safety**: BotsOnRails uses Python's type annotation system to validate the consistency of inputs and outputs between nodes. This can help catch bugs and inconsistencies early, at definition time rather than runtime.

6. **Lightweight & Unopinionated**: BotsOnRails tries to stay out of your way as much as possible. It doesn't require you to fundamentally change how you write your Python code, and it doesn't impose any heavy runtime dependencies.

At its core, BotsOnRails is about empowering developers to build sophisticated AI-driven workflows without sacrificing simplicity, flexibility, or visibility. Whether you're building a content moderation system, a data processing pipeline, or a chatbot, BotsOnRails provides a powerful and expressive foundation.

We're excited to see what the community will build with BotsOnRails, and we're committed to evolving the library based on your feedback and needs. If you have ideas, questions, or suggestions, please don't hesitate to open an issue or pull request on our GitHub repo.

Happy bot building!
