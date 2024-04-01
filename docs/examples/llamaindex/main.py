import json
from typing import List, Optional

import marvin
from pathlib import Path

from llama_index.legacy.embeddings import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.retrievers import BaseRetriever
from BotsOnRails import ExecutionPath, step_decorator_for_path
from display import display_stock_series_cards
from models import StockSeriesInfo, ParticipationCap

tree = ExecutionPath()
node = step_decorator_for_path(tree)

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

# Configure Llama Index
Settings.chunk_size = 4096
Settings.llm = llm
Settings.embed_model = embed_model


@node(path_start=True, next_step="check_doc_type")
def load_document(doc_dir: str, **kwargs) -> BaseRetriever:
    print(f"Loading dovs from {doc_dir}...")
    documents = SimpleDirectoryReader(doc_dir).load_data()
    print(f"Vectorizing...")
    index = VectorStoreIndex.from_documents(documents)
    print(f"Building retriever...")
    retriever = index.as_retriever(similarity_top_k=3)
    print("Passing the baton... It's been a pleasure.")
    ## TODO - check that return signatures match function return signatures...
    return retriever


@node(next_step={"incorporation": "extract_stock_info", "other": "end_pipeline"})
def check_doc_type(retriever: BaseRetriever, *args, **kwargs) -> str:
    retrieved_context = retriever.retrieve("This document, made between this parties as of this date.")
    context = "------\n".join([rc.text for rc in retrieved_context])
    print(f"Doc context: {context}")
    doc_type = marvin.classify(context, labels=["incorporation", "other"])
    print(f"Inferred doc type: {doc_type}")
    return doc_type


@node(next_step='filter_common', unpack_output=False)
def extract_stock_info(*args, **kwargs) -> List[StockSeriesInfo]:
    print(f"extract_stock_info() - runtime kwargs: {kwargs}")

    retriever = kwargs['runtime_args']['input_chain']['check_doc_type'][0]
    retrieved_stock_text = retriever.retrieve('Stock or series of stock authorized and/or issued by this company')
    stock_text = "-----\n".join([rc.text for rc in retrieved_stock_text])
    stock_series_list = marvin.extract(stock_text, target=StockSeriesInfo)
    print(f"Found {len(stock_series_list)}")
    return stock_series_list


@node(next_step=('FOR_EACH', "retrieve_passages"), unpack_output=False)
def filter_common(stock_series: List[StockSeriesInfo], **kwargs) -> List[StockSeriesInfo]:
    return [
        ss for ss in stock_series if ss.stock_class_name.lower() != 'common'
    ]


@node(next_step="extract_participation_cap", unpack_output=False)
def retrieve_passages(stock_series: StockSeriesInfo, **kwargs) -> List[str]:
    print(f"retrieve_passages - kwargs: {kwargs}")
    loop_data = kwargs['runtime_args']['for_each_loop']
    max_iterations = loop_data['expected']
    current_index = loop_data['actual']
    iterating_over = loop_data['source_iterable']

    print(f"Retrieving passes #{current_index} for max iterations {max_iterations}: {iterating_over}")

    retriever = kwargs['runtime_args']['input_chain']['check_doc_type'][0]
    participation_cap_passages = retriever.retrieve(f"maximum amount the preferred series "
                                                    f"{stock_series.stock_series_name} is entitled to receive without"
                                                    f" forced conversion to Common")

    return [pc.text for pc in participation_cap_passages]


@node(next_step="aggregate_data", unpack_output=False)
def extract_participation_cap(passages: List[str], **kwargs) -> tuple[StockSeriesInfo, Optional[ParticipationCap]]:
    print(f"Extract_participation_cap got iterable data: {kwargs['runtime_args']['for_each_loop']}")

    series_info = kwargs['runtime_args']['input_chain']['retrieve_passages'][0]
    search_area = "-----\n".join(passages)

    participation_cap = marvin.cast(
        search_area,
        target=Optional[ParticipationCap],
        instructions=f"Extract participation cap information for maximum amount given series of preferred can "
                     f"receive before converting to common based on provided excerpts from a certificate of "
                     f"incorporation, if available. If not found, return null."
    )
    return series_info, participation_cap


@node(aggregator=True)
def aggregate_data(series_data: tuple[StockSeriesInfo, Optional[ParticipationCap]], **kwargs) -> tuple[StockSeriesInfo, Optional[ParticipationCap]]:
    return series_data


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
tree.visualize_via_graphviz()

for doc_dir in doc_dir_names:
    doc_path = my_dir / doc_dir
    series_data = tree.run(doc_path.__str__())
    print(f"\n----------\nSeries data for {doc_dir}:")
    display_stock_series_cards(series_data)
