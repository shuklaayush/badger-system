from helpers.proxy_utils import deploy_proxy
from helpers.gnosis_safe import GnosisSafe, MultisigTxMetadata
import os
from scripts.systems.sushiswap_system import SushiswapSystem
from scripts.systems.badger_system import print_to_file
from scripts.systems.digg_system import connect_digg
from scripts.systems.uniswap_system import UniswapSystem
from scripts.systems.claw_minimal import deploy_claw_minimal
import time

from brownie import *
import decouple
from config.badger_config import (
    badger_config,
    sett_config,
    digg_config,
    claw_config
)
from helpers.constants import *
from helpers.time_utils import days
from helpers.token_utils import (
    distribute_from_whales,
    distribute_meme_nfts,
    distribute_test_ether,
)
from rich.console import Console
from scripts.deploy.deploy_digg import (
    deploy_digg_with_existing_badger,
    digg_deploy_flow,
)
from scripts.systems.badger_system import connect_badger
from helpers.registry import token_registry
from tests.sett.fixtures import SushiClawUSDCMiniDeploy
console = Console()


def main():
    """
    Connect to badger, distribute assets to specified test user, and keep ganache open.
    Ganache will run with your default brownie settings for mainnet-fork
    """

    # The address to test with
    user = accounts.at(decouple.config("TEST_ACCOUNT"), force=True)

    badger = connect_badger("deploy-final.json", load_deployer=False, load_keeper=False, load_guardian=False)

    # TODO: After prod deployment, just connect instead.
    claw = deploy_claw_minimal(badger.deployer, printToFile=True)
    # Deploy claw setts
    sushiswap = SushiswapSystem()
    for (settId, empName) in [("native.sushiBClawUSDC",  "bClaw"), ("native.sushiSClawUSDC", "sClaw")]:
        params = sett_config.sushi.sushiClawUSDC.params
        token = claw.emps[empName].tokenCurrency()
        if sushiswap.hasPair(token, token_registry.wbtc):
            params.want = sushiswap.getPair(token, token_registry.wbtc)
        else:
            params.want = sushiswap.createPair(
                token,
                token_registry.wbtc,
                badger.deployer,
            )
        want = params.want
        params.badgerTree = badger.badgerTree
        params.pid = sushiswap.add_chef_rewards(want)

        strategist = badger.daoProxyAdmin
        controller = badger.add_controller(settId)
        badger.deploy_sett(
            settId,
            want,
            controller,
            governance=badger.daoProxyAdmin,
            strategist=strategist,
            keeper=badger.keeper,
            guardian=badger.guardian,
        )
        badger.deploy_strategy(
            settId,
            "StrategySushiLpOptimizer",
            controller,
            params,
            governance=badger.daoProxyAdmin,
            strategist=strategist,
            keeper=badger.keeper,
            guardian=badger.guardian,
        )

    print_to_file(badger, "deploy-test.json")

    console.print("[blue]=== 🦡 Test ENV for account {} 🦡 ===[/blue]".format(user))

    # ===== Transfer test assets to User =====
    distribute_test_ether(user, Wei("20 ether"))
    distribute_test_ether(badger.deployer, Wei("20 ether"))
    distribute_from_whales(user)

    gitcoin_airdrop_root = "0xcd18c32591078dcb6686c5b4db427b7241f5f1209e79e2e2a31e17c1382dd3e2"
    bBadger = badger.getSett("native.badger")

    # ===== Local Setup =====
    airdropLogic = AirdropDistributor.deploy({"from": badger.deployer})
    airdropProxy = deploy_proxy(
        "AirdropDistributor",
        AirdropDistributor.abi,
        airdropLogic.address,
        badger.opsProxyAdmin.address,
        airdropLogic.initialize.encode_input(
            bBadger,
            gitcoin_airdrop_root,
            badger.rewardsEscrow,
            chain.time() + days(7),
            [user]
        ),
        badger.deployer
    )

    assert airdropProxy.isClaimTester(user) == True
    assert airdropProxy.isClaimTester(badger.deployer) == False

    bBadger.transfer(airdropProxy, Wei("10000 ether"), {"from": user})

    airdropProxy.unpause({"from": badger.deployer})
    airdropProxy.openAirdrop({"from": badger.deployer})

    console.print("[blue]Gitcoin Airdrop deployed at {}[/blue]".format(airdropProxy.address))

    console.print("[green]=== ✅ Test ENV Setup Complete ✅ ===[/green]")
    # Keep ganache open until closed
    time.sleep(days(365))
