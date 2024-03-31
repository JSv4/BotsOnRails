import json
from typing import List, Optional

import marvin
from pathlib import Path

from llama_index.legacy.embeddings import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, ServiceContext, SimpleDirectoryReader
from BotsOnRails import ExecutionTree, node_for_tree
from examples.llamaindex.models import StockSeriesInfo, ParticipationCap

tree = ExecutionTree()
node = node_for_tree(tree)

my_dir = Path(__file__).parent
credential_file = my_dir / "credentials.json.env"
credentials = json.loads(credential_file.read_text())

# Authorize OpenAI
OPENAI_API_KEY = credentials["OPENAI_API_KEY"]
marvin.settings.openai.api_key = OPENAI_API_KEY

embed_model = HuggingFaceEmbedding(
    model_name='sentence-transformers/all-mpnet-base-v2',
    max_length=384
)
llm = OpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4-0125-preview",
    temperature=0.0
)
llamaindex_context = ServiceContext.from_defaults(
    embed_model=embed_model,
    llm=llm,
    chunk_size=4096
)


@node(start_node=True, next_nodes="check_doc_type")
def load_document(doc_dir: str, **kwargs) -> tuple[str, VectorStoreIndex]:
    documents = SimpleDirectoryReader("../paul_graham_essay/data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    return documents[0].txt, index


@node(next_nodes={"incorporation": "extract_stock_info", "other": "end_pipeline"})
def check_doc_type(doc_text: str, *args, **kwargs) -> str:
    doc_type = marvin.classify(doc_text, labels=["incorporation", "other"])
    return doc_type


@node(next_nodes=('FOR_EACH',"retrieve_passages"), unpack_output=False)
def extract_stock_info(doc_text: str, **kwargs) -> List[StockSeriesInfo]:
    print(f"extract_stock_info() - runtime kwargs: {kwargs}")
    index = kwargs['runtime_args']['load_document']['yo']
    # series_text =

    stock_series_list = marvin.extract(doc_text, target=StockSeriesInfo)
    return stock_series_list


@node(next_nodes="extract_participation_cap", unpack_output=False)
def retrieve_passages(stock_series: StockSeriesInfo, **kwargs) -> List[str]:
    query = f"{stock_series.stock_series_name} participation cap"
    # passages = index.as_retriever()

    # return [passage.text for passage in passages]
    return ["Bob", "is", "my", "uncle"]


@node(next_nodes="store_data", wait_for_approval=True)
def extract_participation_cap(passages: List[str], **kwargs) -> Optional[ParticipationCap]:
    participation_cap = None
    for passage in passages:
        participation_cap = marvin.cast(
            passage,
            target=ParticipationCap,
            instructions=f"Extract participation cap information from the given passage, if available. "
                         f"If not found, return null.",
            prefer_null=True,
        )
        if participation_cap is not None:
            break

    return participation_cap


@node(aggregator=True)
def store_data(participation_cap: Optional[ParticipationCap], **kwargs):
    print("Loading data into the system...")
    # for stock_series, participation_cap in zip(stock_series_list, participation_caps):
    #     print(f"Stock Series: {stock_series.stock_series_name}")
    #     if participation_cap:
    #         print(f"Participation Cap: {participation_cap.json(indent=2)}")
    #     else:
    #         print("No participation cap found for this series.")
    print("Data loading completed.")


@node()
def end_pipeline(*args, **kwargs):
    print("Document is not a Certificate of Incorporation. Pipeline ended.")

# Some docs to process
doc_dir_names = [
    "docs/palantir",
    "docs/airbnb",
    "docs/toast"
]

# Compile the execution tree
tree.compile(type_checking=True)

for doc_dir in doc_dir_names:
    doc_path = my_dir / doc_dir
    tree.run(doc_path.__str__())

