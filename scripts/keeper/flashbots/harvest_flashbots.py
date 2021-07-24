import os

from brownie import *
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from web3.contract import estimate_gas_for_function
from web3.middleware import construct_sign_and_send_raw_middleware
from config.keeper import keeper_config
from flashbots import flashbot
from flashbots.types import SignTx
from helpers.gas_utils import gas_strategies
from helpers.registry import registry
from helpers.sett.SnapshotManager import SnapshotManager
from helpers.utils import tx_wait, val
from helpers.console_utils import console
from scripts.systems.badger_system import BadgerSystem, connect_badger
from tabulate import tabulate
from web3.types import TxParams, Wei

gas_strategies.set_default_for_active_chain()

ETH_ACCOUNT_SIGNATURE = Account.from_key(
    os.environ.get("ETH_SIGNATURE_KEY")
)
flashbot(web3, ETH_ACCOUNT_SIGNATURE)

def harvest_all(badger: BadgerSystem, skip, min_profit=0):
    """
    Runs harvest function for strategies if they are expected to be profitable.
    If a profit estimate fails for any reason the default behavior is to treat it as having a profit of zero.

    :param badger: badger system
    :param skip: strategies to skip checking
    :param min_profit: minimum estimated profit (in ETH or BNB) required for harvest to be executed on chain
    """
    for key, vault in badger.sett_system.vaults.items():
        if key in skip:
            continue

        console.print(
            "\n[bold yellow]===== Harvest: " + str(key) + " =====[/bold yellow]\n"
        )

        print("Harvest: " + key)

        snap = SnapshotManager(badger, key)
        strategy = badger.getStrategy(key)

        before = snap.snap()
        if strategy.keeper() == badger.badgerRewardsManager:
            keeper = accounts.at(strategy.keeper())
            estimated_profit = snap.estimateProfitHarvestViaManager(
                key,
                strategy,
                {"from": keeper, "gas_limit": 2000000, "allow_revert": True},
            )
            if estimated_profit >= min_profit:
                snap.settHarvestViaManager(
                    strategy,
                    {"from": keeper, "gas_limit": 2000000, "allow_revert": True},
                    confirm=False,
                )
        else:
            estimated_profit = snap.estimateProfitHarvest(
                key, {"from": keeper, "gas_limit": 2000000, "allow_revert": True}
            )
            if estimated_profit >= min_profit:
                snap.settHarvest(
                    {"from": keeper, "gas_limit": 2000000, "allow_revert": True},
                    confirm=False,
                )

        tx_wait()

        if rpc.is_active():
            chain.mine()
        after = snap.snap()

        snap.printCompare(before, after)


def main():
    badger = connect_badger(load_keeper=True, load_harvester=True)
    skip = keeper_config.get_active_chain_skipped_setts("harvest")

    if rpc.is_active():
        """
        Test: Load up testing accounts with ETH
        """
        accounts[0].transfer(badger.deployer, Wei("5 ether"))
        accounts[0].transfer(badger.keeper, Wei("5 ether"))
        accounts[0].transfer(badger.guardian, Wei("5 ether"))

        skip.append("native.test")
        skip.append("yearn.wbtc")
        skip.append("experimental.sushiIBbtcWbtc")
        skip.append("experimental.digg")

    harvest_all(badger, skip)