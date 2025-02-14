// SPDX-License-Identifier: MIT

pragma solidity ^0.6.11;

import "deps/@openzeppelin/contracts-upgradeable/token/ERC20/IERC20Upgradeable.sol";
import "deps/@openzeppelin/contracts-upgradeable/math/SafeMathUpgradeable.sol";
import "deps/@openzeppelin/contracts-upgradeable/utils/AddressUpgradeable.sol";
import "deps/@openzeppelin/contracts-upgradeable/utils/PausableUpgradeable.sol";
import "deps/@openzeppelin/contracts-upgradeable/token/ERC20/SafeERC20Upgradeable.sol";
import "deps/@openzeppelin/contracts-upgradeable/proxy/Initializable.sol";
import "deps/@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";

import "interfaces/uniswap/IUniswapRouterV2.sol";
import "interfaces/uniswap/IUniswapV2Factory.sol";

/*
    Expands swapping functionality over base strategy
    - ETH in and ETH out Variants
    - Sushiswap support in addition to Uniswap
*/
contract UniswapLibraryExternal {
    using SafeERC20Upgradeable for IERC20Upgradeable;
    using AddressUpgradeable for address;
    using SafeMathUpgradeable for uint256;

    bytes32 public constant UNI_V2_LIKE_ROUTER_ROLE = keccak256("UNI_LIKE_ROUTER_ROLE");
    uint256 public constant MAX_FEE = 10000;

    IBadgerAccessControl public constant badgerAccessControl = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address public constant uniswap = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D; // Uniswap router
    address public constant sushiswap = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F; // Sushiswap router

    function swapExactTokensForTokens(
        address router,
        address startToken,
        uint256 balance,
        address[] memory path
    ) public {
        require(badgerAccessControl.hasRole(UNI_V2_LIKE_ROUTER_ROLE, router), "Specified router not approved as UniV2 like router");
        _safeApproveHelper(startToken, router, balance);
        IUniswapRouterV2(router).swapExactTokensForTokens(balance, 0, path, address(this), now);
    }

    function swapExactETHForTokens(
        address router,
        uint256 balance,
        address[] memory path
    ) public {
        require(badgerAccessControl.hasRole(UNI_V2_LIKE_ROUTER_ROLE, router), "Specified router not approved as UniV2 like router");
        IUniswapRouterV2(uniswap).swapExactETHForTokens{value: balance}(0, path, address(this), now);
    }

    function swapExactTokensForETH(
        address router,
        address startToken,
        uint256 balance,
        address[] memory path
    ) public {
        require(badgerAccessControl.hasRole(UNI_V2_LIKE_ROUTER_ROLE, router), "Specified router not approved as UniV2 like router");
        _safeApproveHelper(startToken, router, balance);
        IUniswapRouterV2(router).swapExactTokensForETH(balance, 0, path, address(this), now);
    }

    function getPair(
        address router,
        address token0,
        address token1
    ) public view returns (address) {
        require(badgerAccessControl.hasRole(UNI_V2_LIKE_ROUTER_ROLE, router), "Specified router not approved as UniV2 like router");
        address factory = IUniswapRouterV2(router).factory();
        return IUniswapV2Factory(factory).getPair(token0, token1);
    }

    /// @notice Add liquidity to uniswap for specified token pair, utilizing the maximum balance possible
    function addMaxLiquidity(
        address router,
        address token0,
        address token1
    ) public {
        require(badgerAccessControl.hasRole(UNI_V2_LIKE_ROUTER_ROLE, router), "Specified router not approved as UniV2 like router");
        uint256 _token0Balance = IERC20Upgradeable(token0).balanceOf(address(this));
        uint256 _token1Balance = IERC20Upgradeable(token1).balanceOf(address(this));

        _safeApproveHelper(token0, router, _token0Balance);
        _safeApproveHelper(token1, router, _token1Balance);

        IUniswapRouterV2(router).addLiquidity(token0, token1, _token0Balance, _token1Balance, 0, 0, address(this), block.timestamp);
    }

    function addMaxLiquidityEth(address router, address token0) public {
        require(badgerAccessControl.hasRole(UNI_V2_LIKE_ROUTER_ROLE, router), "Specified router not approved as UniV2 like router");
        uint256 _token0Balance = IERC20Upgradeable(token0).balanceOf(address(this));
        uint256 _ethBalance = address(this).balance;

        _safeApproveHelper(token0, router, _token0Balance);
        IUniswapRouterV2(router).addLiquidityETH{value: address(this).balance}(token0, _token0Balance, 0, 0, address(this), block.timestamp);
    }

    uint256[50] private __gap;
}
