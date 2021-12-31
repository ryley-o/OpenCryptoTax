import requests
import json
import os
from dotenv import load_dotenv
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# take environment variables from .env
load_dotenv()

# transports
transports = dict()
transports["ETH"] = AIOHTTPTransport(
    url=os.environ.get("UNISWAP_SUBGRAPH_HTTP_ENDPOINT"))
transports["BSC"] = AIOHTTPTransport(
    url=os.environ.get("PANCAKESWAP_V2_SUBGRAPH_HTTP_ENDPOINT"))
# prior to block 6810708 (04/23/2021), Pancakeswap V2 LP didn't exist
transports["BSC_V1"] = AIOHTTPTransport(
    url=os.environ.get("PANCAKESWAP_V1_SUBGRAPH_HTTP_ENDPOINT"))
# clients
clients = dict()
for chain in ["ETH", "BSC", "BSC_V1"]:
    clients[chain] = Client(transport=transports[chain], fetch_schema_from_transport=True)

eth_price_query = gql(
    '''
    query GetPair($block_number: Int!) {
        pair(
            id: "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"
            block: {
              number: $block_number
            }
        ) {
            token0Price
        }
    }
    '''
)

bnb_price_query = gql(
    '''
    query GetPair($id: ID!, $block_number: Int!) {
        pair(
            id: $id
            block: {
              number: $block_number
            }
        ) {
            token1Price
        }
    }
    '''
)


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
        params = {"block_number": block_number}
        response = clients["ETH"].execute(eth_price_query, variable_values=params)
        return response["pair"]["token0Price"]

    @staticmethod
    def get_bnb_price_at_bsc_block(block_number: int):
        """
        This returns the bnb price based on pancake swap subgraph
        at a given block number.
        Uses
        :param block_number: int BSC block number to get pancake swap BNB price
        :return: bnb_price_usd: double Price of bnb in USD (busd)
        """
        # pancakeswapv2 pair deployed block 6810708
        if block_number >= 6810708:
            _client = clients["BSC"]
            _pair_id = "0x58f876857a02d6762e0101bb5c46a8c1ed44dc16"
        else:
            _client = clients["BSC_V1"]
            _pair_id = "0x1b96b92314c44b159149f7e0303511fb2fc4774f"
        params = {"id": _pair_id, "block_number": block_number}
        print(params)
        response = _client.execute(bnb_price_query, variable_values=params)
        print(response)
        if response["pair"] is None:
            raise ValueError(f"Subgraph did not find an asset value at BSC block number {block_number}")
        return response["pair"]["token1Price"]
