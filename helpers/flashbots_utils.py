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


def get_min_expected_harvest(strategy, key, overrides):
    """
    Return minimum expected harvest from strategy.
    """
    assert is_supported(key)

    # TODO: Get pending rewards and convert to want using price API
    pass


def estimate_briber_gas_cost(badger: BadgerSystem, strategy, overrides):
    """
    Estimate gas cost for calling harvest through briber.
    """
    gas_estimate = badger.mevBriber.privateHarvest.estimate_gas(strategy, 0, overrides)
    return gas_strategies.gas_cost(gas_estimate)
