import json
import os
import uuid
from datetime import datetime
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
import tika
from tika import parser

from BotsOnRails import ExecutionTree, node_for_tree
from BotsOnRails.types import SpecialTypes

tree = ExecutionTree()
node = node_for_tree(tree)

my_dir = Path(__file__).parent
credential_file = my_dir / "credentials.json.env"
credentials = json.loads(credential_file.read_text())

# Authorize Marvin
marvin.settings.openai.api_key = credentials["OPENAI_API_KEY"]

palantir_coi = my_dir / "Palantir-COI.pdf"
plaantir_coi_txt = parser.from_file(palantir_coi.__str__())


class CompanyInfo(BaseModel):
    name: str = Field(description="The legal name of the Company")
    incorporation_date: datetime = Field(description="The original date the company was incorporated")
    incorporation_place: str = Field(description="The abbreviation of the state (if in the US) or country (otherwise) "
                                                 "where the Company was formed")
    company_type: str = Field(description="The type of the Company - e.g. Corporation, LLP, LLC, etc.")


class CurrencyType(BaseModel):
    currency_code: str = Field("Currency code, like USD of GBP")
    amount: float = Field("The total amount of currency")


class StockSeries(BaseModel):
    series_name: str = Field(description="The name of the stock series - e.g. 'Series A' in Series A Preferred")
    stock_type: str = Field(description="The type of stock - e.g. common or preferred")
    par_value: CurrencyType = Field(description="The par value of the stock")
    authorized: int = Field(description="How many shares are authorized")


class NamedDirectors(BaseModel):
    """Describes a director or directors assigned to be elected by a class or classes voting together as a
    separate class"""
    director_name: str = Field(description="The defined name of the director being elected by a class or classes "
                                           "voting together as a separate series")
    voting_classes: list[str] = Field(description="The list of the classes, voting together as a separate series, "
                                                  "who get to elect this director")


class CompanyInfo(BaseModel):
    company_info: CompanyInfo = Field(description="Information about the issuing company")
    stock_series: list[StockSeries] = Field(description="Series of stock issued by the company")
    directors: list[NamedDirectors] = Field(description="List of directors entitled to be elected by a series or "
                                                        "series of stock, voting together")


data = marvin.cast(
    plaantir_coi_txt,
    target=CompanyInfo,
    instructions="Here is the certificate of incorporation of a company issuing stock. Based on the text, "
                 "please extract the company information specified in the target data structure."
)

print(data.model_dump_json(indent=2))


@node(start_node=True)
def count_named_directors(*args, **kwargs) -> int:
    doc_text = kwargs['runtime_args']['input'][0]['content']
    print(f"Working with doc_text: {doc_text}")

    count = marvin.extract(
        doc_text,
        target=NamedDirectors,
        instructions="For each director which is elected by a single series or group of series, voting together, "
                     "please fill out the specified information."
    )

    print(f"Count: {count}")
    return len(count)

tree.compile()
tree.run(plaantir_coi_txt)
