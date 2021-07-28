from brownie import *
from helpers.gas_utils import gas_strategies
from helpers.sett.strategy_earnings import (
    get_price,
)
from rich.console import Console
from scripts.systems.badger_system import BadgerSystem
import requests

console = Console()


def is_supported(key):
    # TODO: Currently only supports native.uniBadgerWbtc
    return key in {"native.uniBadgerWbtc"}


def get_min_price_for_swap(sellToken, buyToken, sellAmount, slippage=None):
    """
    Get minimum swap price based on slippage tolerance.
    """
    # TODO: This doesn't work either. Find an API for off-chain price for BADGER-WBTC
    try:
        get_price(sellToken, buyToken, sellAmount)
    except ValueError:
        endpoint = "https://api.1inch.exchange/v3.0/"

        params = (
            str(web3.chain_id)  # TODO: Maybe move to network_manager
            + "/quote?fromTokenAddress="
            + sellToken
            + "&toTokenAddress="
            + buyToken
            + "&amount="
            + str(sellAmount)
        )
        r = requests.get(endpoint + params)
        data = r.json()

        if not data.get("toTokenAmount"):
            console.log(data)
            raise ValueError("Price could not be fetched")

        return data["toTokenAmount"] / data["fromTokenAmount"]


def get_harvest_swap_expected(strategy, key, overrides):
    """
    Return swaps expected in strategy harvest() call and corresponding guaranteed swap prices.
    """
    assert is_supported(key)

    harvest_data = strategy.harvest.call(overrides)
    num_swaps = len(harvest_data.swappedTokenAddressesIn)
    return {
        "tokensIn": harvest_data.swappedTokenAddressesIn,
        "tokensOut": harvest_data.swappedTokenAddressesOut,
        "minPrices": [
            get_min_price_for_swap(
                harvest_data.swappedTokenAddressesIn[i],
                harvest_data.swappedTokenAddressesOut[i],
                harvest_data.swappedTokenAmountsIn[i],
            )
            for i in range(num_swaps)
        ],
    }


def get_harvest_swap_expected_array(strategy, key, overrides):
    assert is_supported(key)

    harvest_data = strategy.harvest.call(overrides)
    num_swaps = len(harvest_data.swappedTokenAddressesIn)
    return [
        {
            "tokenIn": harvest_data.swappedTokenAddressesIn[i],
            "tokenOut": harvest_data.swappedTokenAddressesOut[i],
            "minPrice": get_min_price_for_swap(
                harvest_data.swappedTokenAddressesIn[i],
                harvest_data.swappedTokenAddressesOut[i],
                harvest_data.swappedTokenAmountsIn[i],
            ),
        }
        for i in range(num_swaps)
    ]


def estimate_briber_gas_cost(badger: BadgerSystem, strategy, overrides):
    """
    Estimate gas cost for calling harvest through briber.
    """
    harvest_data = strategy.harvest.call(overrides)

    tokens_in = harvest_data.swappedTokenAddressesIn
    tokens_out = harvest_data.swappedTokenAddressesOut
    min_prices = [0] * len(tokens_in)

    gas_estimate = badger.mevBriber.privateHarvest.estimate_gas(
        strategy, tokens_in, tokens_out, min_prices, overrides
    )
    return gas_strategies.gas_cost(gas_estimate)
