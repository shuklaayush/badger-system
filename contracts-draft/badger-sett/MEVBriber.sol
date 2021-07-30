// SPDX-License-Identifier: MIT

pragma solidity ^0.6.0;

import "deps/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "interfaces/badger/IBadgerRewardsManager.sol";

contract MEVBriber is AccessControlUpgradeable, ReentrancyGuardUpgradeable {
    IBadgerRewardsManager rewardsManager;

    function initialize(
        address admin,
        address initialKeeper,
        address _rewardsManager
    ) public initializer {
        __AccessControl_init();

        _setupRole(DEFAULT_ADMIN_ROLE, admin);
        _setupRole(KEEPER_ROLE, initialKeeper);
        rewardsManager = IBadgerRewardsManager(_rewardsManager);
    }

    /// ===== Modifiers =====

    function _onlyKeeper() internal view {
        require(hasRole(KEEPER_ROLE, msg.sender), "KEEPER_ROLE");
    }

    // * @param strategy Address of strategy to harvest
    // * @param minHarvest Min amount of want expected to be harvested
    function privateHarvest(address strategy, uint256 minHarvest) external payable nonReentrant {
        _onlyKeeper();

        // Redundant since it's checked in BadgerRewardsManager harvest(). Maybe remove?
        // require(rewardsManager.hasRole(rewardsManager.KEEPER_ROLE, msg.sender), "Must have keeper role");

        uint256 harvested = rewardsManager.harvest(strategy);
        require(harvested >= minHarvest, "Want harvested is too low");

        // Ref: https://docs.flashbots.net/flashbots-auction/searchers/advanced/coinbase-payment/#managing-payments-to-coinbaseaddress-when-it-is-a-contract
        block.coinbase.call{value: msg.value}();
        // block.coinbase.transfer(msg.value);
    }
}
