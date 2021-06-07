from rich.console import Console

from config.badger_config import badger_config
from scripts.systems.badger_system import BadgerSystem, connect_badger

console = Console()

CRV_SETTS_TO_UPGRADE = [
    "native.renCrv",
    # "native.sbtcCrv",
    # "native.tbtcCrv",
]

CRV_NAME_TO_LOGIC = {
    "native.renCrv": "upgrade_strategy_native_rencrv",
    "native.sbtcCrv": "upgrade_strategy_native_sbtccrv",
    "native.tbtcCrv": "upgrade_strategy_native_tbtccrv",
}

def queue_upgrade_crv_strat(badger: BadgerSystem, stratID: str) -> str:
    upgradeFn = getattr(badger, CRV_NAME_TO_LOGIC[stratID])
    return upgradeFn()


def main():
    """
        Queues crv sett upgrades
    """
    badger = connect_badger(badger_config.prod_json)

    for stratID in CRV_SETTS_TO_UPGRADE:
        txFilename = queue_upgrade_crv_strat(badger, stratID)
        console.print("[orange] queued up timelock tx {} [/orange]".format(txFilename))
