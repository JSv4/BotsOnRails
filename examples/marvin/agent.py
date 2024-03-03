import json
import uuid
from pathlib import Path
from typing import NoReturn, Optional, Tuple, Literal

import jellyfish
import marvin
import requests
from pydantic import BaseModel, Field
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from nlx import ExecutionTree, node_for_tree
from nlx.types import SpecialTypes

tree = ExecutionTree()
node = node_for_tree(tree)

credential_file = Path(__file__).parent / "credentials.json.env"
credentials = json.loads(credential_file.read_text())

# Authorize Marvin
marvin.settings.openai.api_key = credentials["OPENAI_API_KEY"]


def show_document_report(name: str, date: str, parties: list[str]) -> NoReturn:
    """
    Create and display a sparkling card in the terminal with two string fields and a list of names.

    Args:
    name (str): The first string field to display on the card.
    date (str): The second string field to display on the card.
    parties (List[str]): A list of names to display on the card.
    """
    console = Console()

    # Create a table for the list of names
    name_table = Table(show_header=False, box=None)
    name_table.add_column("Name", style="cyan")
    for party in parties:
        name_table.add_row(party)

    # Create the main panel
    # Combine the name, date, and table into a single Group
    card_content = Group(Text(f"Name: {name}", style="bold"),
                         Text(f"Effective Date: {date}", style="bold"),
                         name_table)
    panel = Panel(card_content, style="bold magenta on black", title="[sparkle]Document Analysis[/sparkle]",
                  subtitle="Details")

    # Print the card
    console.print(panel)


class FileLocator(BaseModel):
    """
    Model to hold descriptors for where to find a file with at a local path (in which case path is populated) or a
    remote file (in which case the url is populated).
    """
    id: str = Field(default_factory=uuid.uuid4().__str__)
    name: str = Field(..., description='The name of the document')
    path: Optional[str] = Field(default=None, description="If a local file, the filepath of the document")
    url: Optional[str] = Field(default=None, description="If a remote file at https address, the url of the file")


class LoadedFile(FileLocator):
    """
    Model to hold descriptors for a file with at a local path (in which case path is populated) or a remote file (in
    which case the url is populated).
    """
    contents: Optional[bytes] = Field(default=None, description="Contents of the file as bytes")


documents: list[LoadedFile] = []


@node(
    start_node=True,
    wait_for_approval=True,
    next_nodes={
        "add document": "get_file_to_add_description",
        "analyze document": "get_file_to_analyze_description",
        "delete document": "get_file_to_delete_description",
        "exit": "exit"
    })
def classify_intent(message: str, **kwargs) -> str:
    val = marvin.classify(
        message,
        labels=['analyze document', 'delete document', 'add document', 'exit']
    )
    print(f"I think you wanted to {val}, correct?")
    return val


@node(
    wait_for_approval=True,
    next_nodes="load_file"
)
def get_file_to_add_description(*args, **kwargs) -> FileLocator:
    description = input("What file do you want to use?")
    match = marvin.cast(description, target=FileLocator)
    print(f"I think you want to add this:\n\n{match.model_dump_json(indent=2)}\n\nIs that right?")
    return match


@node(
    wait_for_approval=True,
    next_nodes="get_doc_to_analyze"
)
def get_file_to_analyze_description(*args, **kwargs) -> FileLocator:
    description = input("What file do you want to use?")
    match = marvin.cast(description, target=FileLocator)
    print(f"I think you want analyze this:\n\n{match.model_dump_json(indent=2)}\n\n. Is that right?")
    return match


@node(
    wait_for_approval=True,
    next_nodes="get_doc_to_delete"
)
def get_file_to_delete_description(*args, **kwargs) -> FileLocator:
    description = input("What file do you want to use?")
    match = marvin.cast(description, target=FileLocator)
    print(f"I think you want to delete this:\n\n{match.model_dump_json(indent=2)}\n\n. Is that right?")
    return match


def match_existing_doc(target_doc: FileLocator, **kwargs) -> Optional[LoadedFile]:
    target = list(filter(lambda d: d.id == target_doc.id, documents))
    if len(target) > 1:
        print("Too many documents matched!")
    elif len(target) == 1:
        print(f"Deleting this document: {target[0].name}. Please confirm?")
        return target[0]
    else:
        print("No matching docs!")
    return None


@node(next_nodes="remove_doc")
def get_doc_to_delete(target_doc: FileLocator, **kwargs) -> Optional[LoadedFile]:
    return match_existing_doc(target_doc, **kwargs)


@node(next_nodes="generate_report")
def get_doc_to_analyze(target_doc: FileLocator, **kwargs) -> Optional[LoadedFile]:
    return match_existing_doc(target_doc, **kwargs)


@node()
def remove_doc(target_doc: Optional[LoadedFile], **kwargs) -> NoReturn:
    if target_doc is None:
        print("No document to delete!")
    else:
        for index, document in enumerate(documents):
            if document.id == target_doc.id:
                documents.pop(index)
                break
        print("Deleted!")


@node(wait_for_approval=True)
def find_document(user_msg: str, **kwargs) -> Optional[LoadedFile]:
    filename = marvin.cast(user_msg, target=str, instructions="Valid unix or windows filename or empty string if no "
                                                              "obvious valid filename can be found.")

    best_result: Optional[Tuple[float, LoadedFile]] = None
    for doc in documents:
        sim_score = jellyfish.jaro_similarity(filename, doc.name)
        if best_result is None:
            best_result = (sim_score, doc)
        elif sim_score > best_result[0]:
            best_result = (sim_score, doc)

    if best_result is None:
        print("Sorry, I couldn't find anything that looked like that file")
        return None
    else:
        print(f"I think I found your document. Dod you want to use this:\n{best_result[1].model_dump_json(indent=2)}")
        return best_result[1]


@node()
def load_file(locator: FileLocator, **kwargs) -> Optional[LoadedFile]:
    """
    Add file to the document store.
    :param locator:
    :param kwargs:
    :return:
    """
    loaded = LoadedFile(
        name=locator.name,
        path=locator.path,
        url=locator.url
    )
    if locator.path is not None:
        contents = Path(locator.path).read_bytes()

    elif locator.url is not None:
        response = requests.get(locator.url)
        contents = response.content

    else:
        print("I need a path or url to load from!")
        return None

    loaded.contents = contents

    # Add document to our current document store
    documents.append(loaded)

    print(f"Documents added: {loaded.model_dump_json(indent=2)}")

    return loaded


@node()
def generate_report(doc: Optional[LoadedFile], **kwargs) -> NoReturn:
    """
    Generate basic information re: the document we're analyzing - doc name, effective date and signing parties.
    """

    if doc is None:
        print("No document to analyze")
    else:
        contents = doc.contents.decode("utf-8")
        document_name = marvin.cast(contents, target=str, instructions="The name of this document")
        effective_date = marvin.cast(contents, target=str, instructions="The effective date of this document")
        parties = marvin.extract(contents, instructions="The names of all the parties to this document")
        show_document_report(name=document_name, date=effective_date, parties=parties)


@node()
def exit(*args, **kwargs) -> Literal["EXIT"]:
    print("Thanks for chatting!")
    return "EXIT"


# tree.visualize_via_graphviz()
run_state = SpecialTypes.NEVER_RAN

# Execution loop for agent
while True:

    if run_state == SpecialTypes.NEVER_RAN:
        user_prompt = input("Welcome to the document agent. What do you want to do?:\n1. Add a document to the "
                            "store\n2. Remove a document from the store\n3. Analyze a Document in the store\n4. "
                            "Exit\n\nYour Choice? ")
        run_value = tree.run(user_prompt)
        run_state = tree.output
    elif run_state == SpecialTypes.EXECUTION_HALTED:
        user_choice = input("Please confirm you want to proceed? ")
        should_proceed = marvin.cast(user_choice, target=bool, instructions="Does the user appear to want to "
                                                                            "continue - True for yes or False for"
                                                                            " no")
        if should_proceed:
            tree.run_from_node(
                tree.locked_at_node_name,
                prev_execution_state=tree.model_dump(),
                has_approval=True
            )
        else:
            print("Ok, we'll stop")
            break
        run_state = tree.output
    else:
        # If output indicates user wants to exit... stop the loop
        if run_state == "EXIT":
            print("Exiting!")
            break
        # Otherwise, reset and start again
        else:
            run_state = SpecialTypes.NEVER_RAN

        # os.system('cls' if os.name == 'nt' else 'clear')
