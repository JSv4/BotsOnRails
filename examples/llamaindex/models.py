from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class CompanyInfo(BaseModel):
    """
    Object to hold basic information about issuer - the company issuing the stock being purchased.
    """
    company_name: str = Field(..., description="Name of the Company issuing stock")
    company_type: Optional[str] = Field(default=None, description="What kind of company is this - e.g. LLC, "
                                                                  "Corporation, etc.")
    company_organization_state: Optional[str] = Field(default=None, description="The abbreviation of the state or "
                                                                                "country where this company was "
                                                                                "organized.")
    date_of_organization: Optional[datetime] = Field(default=None, description="The date the company was organized to "
                                                                               "do business, if provided")

class StockSeriesInfo(BaseModel):
    """
    Information about a series of stock issued or authorized by an issuer.
    """
    stock_series_name: str = Field(..., description="Name of a stock series - e.g. Series A Preferred Stock, "
                                                    "Class A Common Stock, Common Stock, etc.")
    stock_class_name: str = Field(..., description="The class of stock - e.g. 'Preferred' or 'Common' Stock.")
    par_value: Optional[float] = Field(default=None, description="The par value of this stock series - e.g. $0.01 ("
                                                                 "Currency code capture separately).")
    currency_code: Optional[str] = Field(default=None, description="The currency type used in the document - e.g. USD "
                                                                   "or GBP")
    authorized_amount: Optional[int] = Field(default=None, description="The total number of authorized shares for "
                                                                       "this series")
    original_issue_amount: Optional[float] = Field(default=None, description="The original issue price of the stock, if provided. Should be currency amount")

class LiquidationPref(BaseModel):
    preferred_series_name: str = Field(description="Name of the preferred series")
    amount: float = Field(description="The amount the holder of given preferred stock receives before holder of common stock")
    amount_type: Literal['Multiple', 'Fixed'] = Field(description="Is the amount a multiple of another value or a fixed value")
    multiple_amount_reference: str = Field(description="If the amount_type is a multiple, of what is it a multiple?")

"""
Example of Relevant Language in NVCA:

provided, however, that if the aggregate amount which the holders of Series A Preferred Stock are entitled to receive
under Sections 2.1 and 2.2 shall exceed [$_______] per share (subject to appropriate adjustment in the event of a stock
split, stock dividend, combination, reclassification, or similar event affecting the Series A Preferred Stock)
(the “Maximum Participation Amount”), each holder of Series A Preferred Stock shall be entitled to receive upon
such liquidation, dissolution or winding up of the Corporation the greater of (i) the Maximum Participation Amount
and (ii) the amount such holder would have received if all shares of Series A Preferred Stock had been converted into
Common Stock immediately prior to such liquidation, dissolution or winding up of the Corporation.
"""

class ParticipationCap(BaseModel):
    preferred_series_name: str = Field(description="Name of the preferred series")
    amount: Optional[float] = Field(description="What is the maximum amount the preferred series is entitled to receive without forced conversion to Common - None for N/A?")
    amount_type: Literal['Multiple', 'Fixed'] = Field(description="Is the amount a multiple of another value or a fixed value")
    multiple_amount_reference: str = Field(description="If the amount_type is a multiple, of what is it a multiple?")