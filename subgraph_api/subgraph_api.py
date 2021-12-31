import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env

UNISWAP_SUBGRAPH_HTTP_ENDPOINT: str = \
    os.environ.get("UNISWAP_SUBGRAPH_HTTP_ENDPOINT")
PANCAKESWAP_SUBGRAPH_HTTP_ENDPOINT: str = \
    os.environ.get("PANCAKESWAP_SUBGRAPH_HTTP_ENDPOINT")


class SubgraphQuery:

    def __init__(self):
        print('hi from subgraph_api')

    @staticmethod
    def get_eth_price_at_block(block_number: int):
        """
        This returns the eth price based on uniswap subgraph
        at a given block number
        :param block_number: int Block number to get uniswap eth price
        :return: eth_price_usd: double Price of eth in USD (usdt)
        """
        eth_price_query = f'''
            query {{
                pair(
                    id: "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"
                    block: {{
                      number: {block_number}
                    }}
                ) {{
                    token0Price
                }}
            }}'''
        result = json.loads(
            requests.post(
                UNISWAP_SUBGRAPH_HTTP_ENDPOINT,
                json={'query': eth_price_query}).text
        )
        return result["data"]["pair"]["token0Price"]

    @staticmethod
    def get_bnb_price_at_bsc_block(block_number: int):
        """
        This returns the bnb price based on pancake swap subgraph
        at a given block number.
        Uses
        :param block_number: int BSC block number to get pancake swap BNB price
        :return: bnb_price_usd: double Price of bnb in USD (busd)
        """
        eth_price_query = f'''
            query {{
                pair(
                    id: "0x58f876857a02d6762e0101bb5c46a8c1ed44dc16"
                    block: {{
                      number: {block_number}
                    }}
                ) {{
                    token1Price
                }}
            }}'''
        result = json.loads(
            requests.post(
                PANCAKESWAP_SUBGRAPH_HTTP_ENDPOINT,
                json={'query': eth_price_query}).text
        )
        return result["data"]["pair"]["token1Price"]
