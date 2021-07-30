// SPDX-License-Identifier: MIT
pragma solidity >=0.5.0 <0.8.0;

interface IBadgerRewardsManager {
    function deposit(address strategy) external;

    // TODO: Maybe return uint256 here as well if we want to check later
    function tend(address strategy) external;

    function harvest(address strategy) external returns (uint256);
}
