// SPDX-License-Identifier: MIT

pragma solidity ^0.6.0;

import "deps/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "interfaces/badger/IAccessControl.sol";

contract MEVBriber is OwnableUpgradeable {
    IAccessControl rewardsManager;

    function initialize(address _rewardsManager) public initializer {
        __Ownable_init();
        rewardsManager = IAccessControl(_rewardsManager);
    }

    function briber(address[] memory targets, bytes[] memory data) external payable {
        require(targets.length == data.length, "targets and data must have same length");
        require(rewardsManager.hasRole(rewardsManager.KEEPER_ROLE, msg.sender), "Must have keeper role");

        for (uint256 i = 0; i < targets.length; i++) {
            (bool _success, ) = _targets[i].call(_data[i]);
            require(_success);
        }

        block.coinbase.call{value: msg.value}();
    }
}
