import pytest

from brownie import *
from dotmap import DotMap
from helpers.sett.SnapshotManager import SnapshotManager
from tests.conftest import badger_single_sett, settTestConfig


# @pytest.mark.skip()
@pytest.mark.parametrize(
    "settConfig",
    settTestConfig,
)
def test_mev_briber(settConfig):
    print(settConfig)
    badger = badger_single_sett(settConfig)
    strategy = badger.getStrategy(settConfig["id"])

    # Deploy MEVBriber
    deployer = accounts[0]
    keeper = accounts[2]

    briber = MEVBriber.deploy({"from": deployer})
    briber.intialize(deployer, keeper, badger.badgerRewardsManager)
    mevBriber.privateHarvest(strategy, 0, {"value": web3.toWei("0.01", "ether")})
