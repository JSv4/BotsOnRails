from BotsOnRails import ExecutionTree, node_for_tree
import marvin
import os

# Configure Marvin AI
marvin.settings.openai.api_key = os.environ["OPENAI_API_KEY"]

tree = ExecutionTree()
node = node_for_tree(tree)


@node(start_node=True, next_nodes="analyze_content")
def receive_content(content: str, **kwargs) -> str:
    return content


@node(next_nodes={"flagged": "human_review", "clean": "publish_content"})
def analyze_content(content: str, **kwargs) -> str:
    # Use Marvin AI's classifier to analyze content
    result = marvin.classify(content, labels=["inappropriate", "clean"])
    return "flagged" if result == "inappropriate" else "clean"


@node(wait_for_approval=True, next_nodes="publish_content")
def human_review(content: str, **kwargs) -> bool:
    print(f"Content for review: {content}")
    decision = input("Approve the content? (yes/no): ")
    return decision.lower() == "yes"


@node()
def publish_content(content: str, approved: bool = True, **kwargs):
    if approved:
        print(f"Publishing content: {content}")
    else:
        print(f"Content rejected: {content}")


# Compile the execution tree
tree.compile()

# Example usage
while True:
    content = input("Enter some content to moderate (or 'quit' to exit): ")
    if content.lower() == "quit":
        break

    # Run the execution tree with the input content
    result = tree.run(content)

    # If the execution was halted (i.e., waiting for human approval), prompt for approval
    if result == "EXECUTION_HALTED":
        # Get the node where the execution stopped
        halted_node = tree.locked_at_node_name

        # Prompt for approval
        approve = input(f"Execution halted at node '{halted_node}'. Approve? (yes/no): ")

        # Resume execution based on approval
        if approve.lower() == "yes":
            tree.run_from_node(halted_node, prev_execution_state=tree.model_dump(), has_approval=True)
        else:
            print("Content rejected by human.")