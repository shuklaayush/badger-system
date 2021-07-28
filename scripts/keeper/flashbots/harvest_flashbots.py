from brownie import *
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from config.keeper import keeper_config
from flashbots import flashbot
from helpers.flashbots_utils import estimate_briber_gas_cost
from helpers.gas_utils import gas_strategies
from helpers.sett.SnapshotManager import SnapshotManager
from helpers.utils import tx_wait
from helpers.console_utils import console
from scripts.systems.badger_system import BadgerSystem, connect_badger
from web3.types import Wei

gas_strategies.set_default_for_active_chain()

# Account which signifies your identify to flashbots network
FLASHBOTS_SIGNER: LocalAccount = accounts.load("flashbots-signer")
flashbot(web3, FLASHBOTS_SIGNER)

# Extra tip to pay Flashbots miner for tx
miner_tip = web3.toWei("0.01", "ether")


def has_briber_support(strategy_key):
    """
    Check if strategy supports harvesting through briber
    """
    return strategy_key in {"native.uniBadgerWbtc"}


def harvest_all(badger: BadgerSystem, skip, min_profit=0):
    """
    Runs harvest function for strategies if they are expected to be profitable.
    If a profit estimate fails for any reason the default behavior is to treat it as having a profit of zero.

    :param badger: badger system
    :param strategies: strategies to include in the harvest
    :param skip: strategies to skip checking
    :param min_profit: minimum estimated profit (in ETH or BNB) required for harvest to be executed on chain
    """
    for key, vault in badger.sett_system.vaults.items():
        if not has_briber_support(key) or key in skip:
            continue

        console.print(
            "\n[bold yellow]===== Harvest: " + str(key) + " =====[/bold yellow]\n"
        )

        print("Harvest: " + key)

        snap = SnapshotManager(badger, key)
        strategy = badger.getStrategy(key)

        before = snap.snap()
        if strategy.keeper() == badger.badgerRewardsManager:
            # TODO: This should be keeper of BadgerRewardsManager
            keeper = accounts.at(strategy.keeper())
            # TODO: Why pass key/strategy if SnapshotManager has self.strategy?
            estimated_profit = snap.estimateProfitHarvestViaManagerThroughFlashbots(
                key,
                strategy,
                {"from": keeper, "gas_limit": 2000000, "allow_revert": True},
                min_profit,
                web3.fromWei(miner_tip, "ether"),
            )
            if estimated_profit >= min_profit:
                gas_cost = estimate_briber_gas_cost(badger, strategy)
                bribe = miner_tip + gas_cost

                snap.settHarvestViaManagerThroughFlashbots(
                    strategy,
                    {
                        "from": keeper,
                        "value": bribe,
                        "gas_limit": 2000000,
                        "gas_price": 0,
                        "allow_revert": True,  # TODO: Not sure if this is needed
                    },
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

    harvest_all(badger, skip, miner_tip=miner_tip)
