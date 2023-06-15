import logging
import random
import time
from enum import Enum
from logging import Logger

import requests
from prefect import Task
from prefect import flow
from prefect.server.schemas.states import StateType
from requests import RequestException

from schemas import (HodlHodlOfferBase, HodlHodlUserBase)


class ScraperName(str, Enum):
    HODLHODL = "hodlhodl"


class HodlhodlComScraper:
    def __init__(
        self,
        logger: Logger | None = None,
        prefect: bool = False,
        total_offer_percent_to_scrape: int = 100,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._prefect = prefect
        self._total_offer_percent_to_scrape = total_offer_percent_to_scrape

    def get_currency_list(self) -> list[str]:
        url = 'https://hodlhodl.com/api/frontend/currencies'
        try:
            currencies = requests.get(url).json()
            return [curr.get("code") for curr in currencies['currencies']]
        except RequestException as e:
            self._logger.error("Error fetching currency list: %s", e)

        return currency_list

    def get_and_post_offers(self, curr, trading_type):
        url = f"https://hodlhodl.com/api/frontend/offers?filters[currency_code]={curr}&pagination[offset]=0&filters[side]={trading_type}&facets[show_empty_rest]=true&facets[only]=false&pagination[limit]=100"
        try:
            resp = requests.get(url).json()
            for offer in resp.get("offers"):
                offer_info = self.create_offer_data(offer)
                seller_info = self.create_seller_data(offer)
                self.post_data_to_api(seller_info, offer_info)
        except RequestException as e:
            self._logger.error("Error fetching offers: %s", e)

    def create_offer_data(self, offer):
        return HodlHodlOfferBase(
            offer_identifier=offer.get("id"),
            fiat_currency=offer.get("asset_code"),
            country_code=offer.get("country_code"),
            trading_type_name=offer.get("side"),
            trading_type_slug=offer.get("side"),
            payment_method_name=offer.get("payment_methods")[0].get("type") if offer.get("payment_methods") else None,
            payment_method_slug=offer.get("payment_methods")[0].get("type") if offer.get("payment_methods") else None,
            description=offer.get("description"),
            currency_code=offer.get("currency_code"),
            coin_currency=offer.get("currency_code"),
            price=offer.get("price"),
            min_trade_size=offer.get("min_amount"),
            max_trade_size=offer.get("max_amount"),
            site_name='hodlhodl',
            margin_percentage=0,
            headline=''
        )

    def create_seller_data(self, offer):
        return HodlHodlUserBase(
            username=offer.get("trader").get("login"),
            feedback_score=offer.get("trader").get("rating") if offer.get("trader").get("rating") else 0,
            completed_trades=offer.get("trader").get("trades_count"),
            seller_url=offer.get("trader").get("url"),
            profile_image='',
            trade_volume=0
        )

    def post_data_to_api(self, seller_info, offer_info):
        data = {
            "user": seller_info.dict(),
            "offer": offer_info.dict(),
        }

        cc = offer_info.dict()["country_code"]
        if cc == "Global":
            cc = 'GL'

        params = {
            "country_code": cc,
            "payment_method": offer_info.dict()["payment_method_name"],
            "payment_method_slug": offer_info.dict()["payment_method_slug"],
        }

        try:
            return post_request_to_api(endpoint="local_traders/create_offer", data=data, params=params,
                                       logger=self._logger).json()
        except RequestException as e:
            self._logger.error("Error posting data to API: %s", e)

    def starter_cli(self):
        currencies_list = self.get_currency_list()
        curr = random.choice(currencies_list)
        self.get_and_post_offers(curr, 'sell')

    def starter(self):
        currencies_list = self.get_currency_list()
        for curr in currencies_list:
            for trading_type in ['buy', 'sell']:
                if self._prefect:
                    rate = Task(self.get_and_post_offers, name=f"get hodlhodl offers").submit(curr, trading_type,
                                                                                             return_state=True)
                    if rate.type != StateType.COMPLETED or not rate.result():
                        self._logger.error('Task failed')
                        continue
                    count_offers(rate.result(), ScraperName.HODLHODL)
                    self._logger.debug("Got %s rates", rate)

                    offer_counter = get_counter(ScraperName.HODLHODL)
                    return offer_counter

                else:
                    self.get_and_post_offers(curr, trading_type)
            time.sleep(1)  # rate limiting

@flow
def get_hodlhodl_offers():
    ag = HodlhodlComScraper()
    ag.starter()


if __name__ == "__main__":
    get_hodlhodl_offers()

