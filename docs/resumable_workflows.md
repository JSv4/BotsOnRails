# Resumable and Human-Approvable Workflows in BotsOnRails

One of the key features of BotsOnRails is the ability to create workflows that can be paused, reviewed by a human, and 
then resumed. This is particularly useful when you need human judgment or approval at certain points in your workflow.

## Marking a Node for Human Approval

To mark a node as requiring human approval before the workflow can proceed, use the `wait_for_approval=True` 
argument to the `@step` decorator:

```python
from BotsOnRails import ExecutionPath, step_decorator_for_path

path = ExecutionPath()
step = step_decorator_for_path(path)

@step(wait_for_approval=True)
def human_review(text: str) -> bool:
    print(f"Please review the following text: {text}")
    return input("Approve? (y/n): ").lower() == "y"
```

When the workflow reaches this node, it will pause execution and wait for human interaction. The node function should 
prompt the user for input and return a value indicating whether to proceed or not.

## Resuming a Workflow

When a workflow is paused at a human approval node, you can resume it by calling the `run_from_step` method on the 
`ExecutionPath`:

```python
result = path.run(initial_data)

if result == SpecialTypes.EXECUTION_HALTED:
    print("Workflow paused for human approval")
    approve = input("Proceed? (y/n): ").lower() == "y"
    
    if approve:
        path.run_from_step(
            halted_node_name,
            prev_execution_state=tree.model_dump(),
            has_approval=True
        )
    else:
        print("Workflow cancelled by user")
```

The `run` method will return a special value `SpecialTypes.EXECUTION_HALTED` if the workflow is paused at a human approval node. 

To resume, you first need to get the name of the node where execution is halted. You can find this in the `locked_at_step_name` attribute of the `ExecutionPath`.

Then, call `run_from_step`, passing:
- The name of the node to resume from
- The previous execution state, obtained by calling `model_dump()` on the `ExecutionPath` 
- `has_approval=True` to indicate that the human has approved proceeding

The workflow will then resume from the approval node.

## Detailed Example

Here's a more detailed example of a content moderation workflow that uses human approval:

```python
from BotsOnRails import ExecutionPath, step_decorator_for_path, SpecialTypes

path = ExecutionPath()
step = step_decorator_for_path(path)


@step(path_start=True, next_step={"flagged": "human_review", "clean": "publish"})
def analyze_content(text: str,  **kwargs) -> str:
    if "spam" in text:
        return "flagged"
    else:
        return "clean"


@step(wait_for_approval=True, next_step={"approve": "publish", "reject": "end"})
def human_review(text: str, **kwargs) -> str:
    # You can access data from other nodes using the runtime_args property in the kwargs
    orig_input = kwargs['runtime_args']['input'][0]
    print(f"Please review the following content: {orig_input}")
    # We set this is a default return type, but we can override this when we resume the workflow
    return "reject"


@step()
def publish(text: str, **kwargs):
    print(f"Publishing: {text}")


@step()
def end(**kwargs):
    print("Content rejected")


path.compile()

while True:
    text = input("Enter some text to moderate (or 'quit'): ")
    if text == "quit":
        break

    result = path.run(text)

    if result == SpecialTypes.EXECUTION_HALTED:
        halted_node = path.locked_at_step_name
        print(f"Workflow paused at {halted_node}")

        approve = input("Proceed? (y/n): ").lower() == "y"

        if approve:
            path.run_from_step(
                halted_node,
                prev_execution_state=path.model_dump(),
                has_approval=True,
                override_output="approve"
            )
        else:
            path.run_from_step(
                halted_node,
                prev_execution_state=path.model_dump(),
                has_approval=True,
                override_output="reject"
            )
```

This workflow first analyzes the input text. If it's flagged as potentially inappropriate, it routes to a 
`human_review` node for approval. This node is marked with `wait_for_approval=True`, so execution will pause here.

The main loop checks the result of `tree.run()`. If it's `EXECUTION_HALTED`, it prompts the user to approve or 
reject the content. 

If approved, it resumes the workflow from the `human_review` node with `override_output="approve"`, which will cause
the workflow to proceed to the `publish` node.

If rejected, it resumes with `override_output="reject"`, which will route to the `end` node instead.

This demonstrates how you can build workflows that flexibly incorporate human judgment and easily resume after human 
interaction. The `wait_for_approval` mechanism allows you to designate any node as a pause point, and 
`run_from_step` allows you to resume from that point once human input is provided.

You can also see how the execution state could be easily persisted to disk and then resumed later... the `ExecutionPath`
obj instance is a Pydantic model, so we can dump the model out to disk, serialize it, store it, and **return to 
execution at any arbitrary point in time.**