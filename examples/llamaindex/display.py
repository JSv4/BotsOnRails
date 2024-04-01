from typing import List, Tuple, Optional
from rich import print
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from examples.llamaindex.models import StockSeriesInfo, ParticipationCap


def display_stock_series_cards(stock_series_list: List[Tuple[StockSeriesInfo, Optional[ParticipationCap]]]):
    cards = []
    for stock_series, participation_cap in stock_series_list:
        attributes = [
            f"[bold]Stock Series Name:[/bold] {stock_series.stock_series_name}",
            f"[bold]Stock Class Name:[/bold] {stock_series.stock_class_name}",
            f"[bold]Par Value:[/bold] {stock_series.par_value}",
            f"[bold]Currency Code:[/bold] {stock_series.currency_code}",
            f"[bold]Authorized Amount:[/bold] {stock_series.authorized_amount}",
            f"[bold]Original Issue Amount:[/bold] {stock_series.original_issue_amount}"
        ]

        if participation_cap:
            attributes.extend([
                f"[bold]Participation Cap:[/bold]",
                f"[bold]Preferred Series Name:[/bold] {participation_cap.preferred_series_name}",
                f"[bold]Amount:[/bold] {participation_cap.amount}",
                f"[bold]Amount Type:[/bold] {participation_cap.amount_type}",
                f"[bold]Multiple Amount Reference:[/bold] {participation_cap.multiple_amount_reference}"
            ])

        attribute_text = "\n".join(attributes)
        card = Panel(attribute_text, expand=False, title=stock_series.stock_series_name, border_style="bold")
        cards.append(card)

    print(Columns(cards))
