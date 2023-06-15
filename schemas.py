from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, BaseSettings, validator, Field


class CoinCurrency(str, Enum):
    BITCOIN = "bitcoin"

class HodlHodlOfferBase(BaseModel):
    trading_type_name: str
    trading_type_slug: str
    # We will query our database depending on this key
    coin_currency: str
    fiat_currency: str
    payment_method_slug: str
    payment_method_name: str

    country_code: str
    min_trade_size: str
    max_trade_size: str

    margin_percentage: float

    offer_identifier: str
    site_name: str

    headline: str

    coin_currency: CoinCurrency = CoinCurrency.BITCOIN


class FeedbackType(str, Enum):
    SCORE = "SCORE"

class HodlHodlUserBase(BaseModel):
    username: str
    feedback_type: FeedbackType = FeedbackType.SCORE
    feedback_score: float
    trade_volume: Optional[str]
    completed_trades: int

    profile_image: Optional[str]
    # 'seller_name': offer.get("trader").get("login"),
    # 'seller_rating': offer.get("trader").get("rating"),
    # 'seller_trades_count': offer.get("trader").get("trades_count"),
    # 'seller_url': offer.get("trader").get("url")

    last_seen: str = None

    @validator("last_seen", pre=True)
    def last_seen_validate(cls, last_seen: float) -> str:
        return datetime.fromtimestamp(last_seen).strftime("%Y-%m-%d")


class Settings(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = "utf-8"


settings = Settings()