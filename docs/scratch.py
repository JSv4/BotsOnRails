from BotsOnRails import ExecutionPath, step_decorator_for_path
from BotsOnRails.types import SpecialTypes

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

        print(path.model_dump())

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