from pathlib import Path
from rich import print
import json
from BotsOnRails import ExecutionTree, node_for_tree
import marvin

from BotsOnRails.types import SpecialTypes

credential_file = Path(__file__).parent / "credentials.json.env"
credentials = json.loads(credential_file.read_text())

# Authorize Marvin
marvin.settings.openai.api_key = credentials["OPENAI_API_KEY"]

tree = ExecutionTree()
node = node_for_tree(tree)


@node(start_node=True, next_nodes={"flagged": "human_review", "clean": "publish_content"})
def analyze_content(content: str, **kwargs) -> str:
    # Use Marvin AI's classifier to analyze content
    result = marvin.classify(content, labels=["inappropriate", "clean"])
    return "flagged" if result == "inappropriate" else "clean"


@node(wait_for_approval=True, next_nodes="publish_content")
def human_review(*args, **kwargs) -> str:
    result = marvin.cast(kwargs['runtime_args']['input'][0], target=str, instructions="Why is this content inappropriate?")
    return result
    # print(f"⚠⚠⚠ FLAGGED ⚠⚠⚠ - Please review: {kwargs['runtime_args']['input'][0]}")
    # decision = input("Approve the contnt? (yes/no): ")
    # return decision.lower() == "yes"


@node()
def publish_content(status: str, **kwargs):
    original_message = kwargs['runtime_args']['input'][0]
    if status == 'clean':
        print(f"Publishing content: {original_message}")
    else:
        print(f"Content rejected: {original_message}")


# Compile the execution tree
tree.compile()

# Example usage
while True:
    content = input("Enter some content to moderate (or 'quit' to exit): ")
    if content.lower() == "quit":
        break

    # Run the execution tree with the input content
    result = tree.run(content)
    print(f"Tree result: {result}")

    # If the execution was halted (i.e., waiting for human approval), prompt for approval
    if result == SpecialTypes.EXECUTION_HALTED:
        # Get the node where the execution stopped
        halted_node = tree.locked_at_node_name
        assert halted_node == 'human_review'
        node_result = tree.nodes[halted_node].output_data

        print(f"⚠⚠⚠ MESSAGE FLAGGED ⚠⚠⚠\n\tMessage: {tree.input}\n\tReason: {node_result}")

        print(tree.model_dump())

        # Prompt for approval
        approve = input(f"Approve? (yes/no): ")

        # Resume execution based on approval
        if approve.lower() == "yes":
            tree.run_from_node(
                halted_node,
                prev_execution_state=tree.model_dump(),
                has_approval=True,
                override_output="clean"
            )
        else:
            print("Content rejected by human.")