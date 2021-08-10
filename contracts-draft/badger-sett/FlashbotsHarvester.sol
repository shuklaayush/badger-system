// SPDX-License-Identifier: MIT

pragma solidity ^0.6.0;

import "deps/@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "deps/@openzeppelin/contracts-upgradeable/utils/ReentrancyGuardUpgradeable.sol";
import "interfaces/badger/IKeeperAccessControl.sol";

contract FlashbotsHarvester is AccessControlUpgradeable, ReentrancyGuardUpgradeable {
    bytes32 public constant KEEPER_ROLE = keccak256("KEEPER_ROLE");

    IKeeperAccessControl keeperAcl;

    function initialize(
        address admin,
        address initialKeeper,
        address _keeperAcl
    ) public initializer {
        __AccessControl_init();

        _setupRole(DEFAULT_ADMIN_ROLE, admin);
        _setupRole(KEEPER_ROLE, initialKeeper);
        keeperAcl = IKeeperAccessControl(_keeperAcl);
    }

    /// ===== Modifiers =====

    function _onlyKeeper() internal view {
        require(hasRole(KEEPER_ROLE, msg.sender), "KEEPER_ROLE");
    }

    // * @param strategy Address of strategy to harvest
    // * @param minHarvestedExpected Min amount of want expected to be harvested
    function harvest(address strategy, uint256 minHarvestExpected) external payable nonReentrant {
        _onlyKeeper();

        uint256 harvested = keeperAcl.harvest(strategy);
        require(harvested >= minHarvestExpected, "Harvest is too low");

        block.coinbase.call{value: msg.value}(new bytes(0));
    }
}
