// SPDX-License-Identifier: MIT

pragma solidity ^0.6.0;

import "deps/@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "interfaces/badger/IAccessControl.sol";

contract MEVBriber is AccessControlUpgradeable, ReentrancyGuardUpgradeable {
    IAccessControl rewardsManager;

    // TODO: Share definition by moving to library (or abstract contract)
    uint256 private constant MAX_SWAPS = 3; // Memory arrays are fixed size in solidity
    struct HarvestData {
        uint256 badgerHarvested;
        uint256 totalBadger;
        uint256 badgerConvertedToWbtc;
        uint256 wbtcFromConversion;
        uint256 lpGained;
        uint256 lpDeposited;
        // Swapped tokens
        address[MAX_SWAPS] swappedTokenAddressesIn;
        address[MAX_SWAPS] swappedTokenAddressesOut;
        uint256[MAX_SWAPS] swappedTokenAmountsIn;
        uint256[MAX_SWAPS] swappedTokenAmountsOut;
    }

    function initialize(address initialKeeper, address _rewardsManager) public initializer {
        __AccessControl_init();

        _setupRole(KEEPER_ROLE, initialKeeper);
        rewardsManager = IAccessControl(_rewardsManager);
    }

    /// ===== Modifiers =====

    function _onlyKeeper() internal view {
        require(hasRole(KEEPER_ROLE, msg.sender), "KEEPER_ROLE");
    }

    // * @param strategy Address of strategy to harvest
    // * @param swappedTokensIn Address of tokens which are swapped from during harvest
    // * @param swappedTokensOut Address of tokens which are swapped into during harvest
    // * @param minSwapPrices 10^18 * Minimum expected price from swap
    function privateHarvest(
        address strategy,
        address[] memory swappedTokensIn,
        address[] memory swappedTokensOut,
        uint256[] memory minSwapPrices
    ) external payable nonReentrant {
        _onlyKeeper();

        require(
            (swappedTokensIn.length == swappedTokensOut.length) && (swappedTokensIn.length == minAmountExpectedAfterSwap.length),
            "swappedTokensIn, swappedTokensOut and minAmountExpectedAfterSwap must have same length"
        );

        // Redundant since it's checked in BadgerRewardsManager harvest(). Maybe remove?
        // require(rewardsManager.hasRole(rewardsManager.KEEPER_ROLE, msg.sender), "Must have keeper role");

        // TODO: HarvestData struct is not standard across all strategies. Either standarize or return tuple
        HarvestData harvestData = rewardsManager.harvest(strategy);

        for (uint256 i = 0; i < swappedTokensIn.length; i++) {
            // Order of tokens is important
            require(harvestData.swappedTokenAddressesIn[i] == swappedTokensIn[i], "Swapped tokens inputs must match");
            require(harvestData.swappedTokenAddressesOut[i] == swappedTokensOut[i], "Swapped tokens outputs must match");

            // Check if slippage is within bounds
            uint256 minOutExpected = harvestData.swappedTokenAmountsIn[i].mul(minSwapPrices[i]).div(1e18);
            require(harvestData.swappedTokenAmountsOut[i] >= minOutExpected, "Token amount after swap is too low");
        }

        // Ref: https://docs.flashbots.net/flashbots-auction/searchers/advanced/coinbase-payment/#managing-payments-to-coinbaseaddress-when-it-is-a-contract
        block.coinbase.call{value: msg.value}();
        // block.coinbase.transfer(msg.value);
    }
}
