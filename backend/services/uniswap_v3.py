import json
import logging
import math
from pathlib import Path

from web3 import Web3

from models import UniswapV3Position
from services.cache import cache
from services.eth import get_web3
from services.prices import get_token_prices

logger = logging.getLogger(__name__)

ABI_DIR = Path(__file__).parent.parent / "abi"

with open(ABI_DIR / "univ3_position_manager.json") as f:
    POSITION_MANAGER_ABI = json.load(f)

with open(ABI_DIR / "univ3_pool.json") as f:
    POOL_ABI = json.load(f)

with open(ABI_DIR / "univ3_factory.json") as f:
    FACTORY_ABI = json.load(f)

with open(ABI_DIR / "erc20.json") as f:
    ERC20_ABI = json.load(f)

# Uniswap V3 contract addresses (mainnet)
POSITION_MANAGER_ADDRESS = Web3.to_checksum_address(
    "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
)
FACTORY_ADDRESS = Web3.to_checksum_address(
    "0x1F98431c8aD98523631AE4a59f267346ea31F984"
)

Q96 = 2 ** 96


def tick_to_sqrt_price(tick: int) -> float:
    """Convert a Uniswap V3 tick to sqrt price."""
    return math.sqrt(1.0001 ** tick)


def get_amounts(
    liquidity: int,
    sqrt_price_x96: int,
    tick_lower: int,
    tick_upper: int,
    current_tick: int,
    decimals0: int,
    decimals1: int,
) -> tuple[float, float]:
    """
    Calculate token amounts for a Uniswap V3 position.

    Args:
        liquidity: Position liquidity
        sqrt_price_x96: Current pool sqrt price as Q64.96 fixed point
        tick_lower: Lower tick of the position
        tick_upper: Upper tick of the position
        current_tick: Current tick of the pool
        decimals0: Decimals of token0
        decimals1: Decimals of token1

    Returns:
        Tuple of (amount0, amount1) in human-readable units
    """
    sqrt_price = sqrt_price_x96 / Q96
    sqrt_lower = tick_to_sqrt_price(tick_lower)
    sqrt_upper = tick_to_sqrt_price(tick_upper)
    L = liquidity

    if current_tick < tick_lower:
        # All liquidity in token0
        amount0_raw = L * (sqrt_upper - sqrt_lower) / (sqrt_lower * sqrt_upper)
        amount1_raw = 0.0
    elif current_tick <= tick_upper:
        # In-range: liquidity in both tokens
        amount0_raw = L * (sqrt_upper - sqrt_price) / (sqrt_price * sqrt_upper)
        amount1_raw = L * (sqrt_price - sqrt_lower)
    else:
        # All liquidity in token1
        amount0_raw = 0.0
        amount1_raw = L * (sqrt_upper - sqrt_lower)

    amount0 = amount0_raw / 10 ** decimals0
    amount1 = amount1_raw / 10 ** decimals1
    return amount0, amount1


def _get_token_info(w3: Web3, token_address: str) -> tuple[str, str, int]:
    """Get token symbol, name, and decimals from on-chain ERC20 contract."""
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
        )
        symbol = contract.functions.symbol().call()
        name = contract.functions.name().call()
        decimals = contract.functions.decimals().call()
        return symbol, name, decimals
    except Exception as exc:
        logger.warning("Failed to get token info for %s: %s", token_address, exc)
        return "UNKNOWN", "Unknown", 18


async def get_v3_positions(address: str) -> list[UniswapV3Position]:
    """
    Fetch all Uniswap V3 NFT liquidity positions for the given address.
    """
    checksum_address = Web3.to_checksum_address(address)
    cache_key = f"v3_positions:{checksum_address.lower()}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    w3 = get_web3()
    positions: list[UniswapV3Position] = []

    try:
        position_manager = w3.eth.contract(
            address=POSITION_MANAGER_ADDRESS, abi=POSITION_MANAGER_ABI
        )
        factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)

        # Get number of NFT positions owned
        nft_count = position_manager.functions.balanceOf(checksum_address).call()
        logger.info("Address %s owns %d V3 NFT positions", address, nft_count)

        if nft_count == 0:
            cache.set(cache_key, positions)
            return positions

        # Collect token IDs
        token_ids = []
        for i in range(nft_count):
            try:
                token_id = position_manager.functions.tokenOfOwnerByIndex(
                    checksum_address, i
                ).call()
                token_ids.append(token_id)
            except Exception as exc:
                logger.warning("Failed to get token ID at index %d: %s", i, exc)

        # Gather unique token addresses for price fetching
        token_addresses_set: set[str] = set()
        position_data_list = []

        for token_id in token_ids:
            try:
                pos = position_manager.functions.positions(token_id).call()
                # positions() returns: nonce, operator, token0, token1, fee,
                # tickLower, tickUpper, liquidity, feeGrowthInside0LastX128,
                # feeGrowthInside1LastX128, tokensOwed0, tokensOwed1
                (
                    nonce,
                    operator,
                    token0_addr,
                    token1_addr,
                    fee,
                    tick_lower,
                    tick_upper,
                    liquidity,
                    _fee_growth0,
                    _fee_growth1,
                    tokens_owed0,
                    tokens_owed1,
                ) = pos

                token_addresses_set.add(token0_addr.lower())
                token_addresses_set.add(token1_addr.lower())

                position_data_list.append(
                    {
                        "token_id": token_id,
                        "token0_addr": token0_addr,
                        "token1_addr": token1_addr,
                        "fee": fee,
                        "tick_lower": tick_lower,
                        "tick_upper": tick_upper,
                        "liquidity": liquidity,
                        "tokens_owed0": tokens_owed0,
                        "tokens_owed1": tokens_owed1,
                    }
                )
            except Exception as exc:
                logger.warning(
                    "Failed to get position data for token ID %d: %s", token_id, exc
                )

        if not position_data_list:
            cache.set(cache_key, positions)
            return positions

        # Fetch prices for all tokens
        prices = await get_token_prices(list(token_addresses_set))

        # Token info cache to avoid repeated RPC calls
        token_info_cache: dict[str, tuple[str, str, int]] = {}

        def get_cached_token_info(addr: str) -> tuple[str, str, int]:
            key = addr.lower()
            if key not in token_info_cache:
                token_info_cache[key] = _get_token_info(w3, addr)
            return token_info_cache[key]

        for pos_data in position_data_list:
            try:
                token0_addr = pos_data["token0_addr"]
                token1_addr = pos_data["token1_addr"]
                fee = pos_data["fee"]
                tick_lower = pos_data["tick_lower"]
                tick_upper = pos_data["tick_upper"]
                liquidity = pos_data["liquidity"]
                tokens_owed0 = pos_data["tokens_owed0"]
                tokens_owed1 = pos_data["tokens_owed1"]

                # Get pool address
                pool_address = factory.functions.getPool(
                    Web3.to_checksum_address(token0_addr),
                    Web3.to_checksum_address(token1_addr),
                    fee,
                ).call()

                if pool_address == "0x0000000000000000000000000000000000000000":
                    logger.warning(
                        "No pool found for %s/%s fee=%d",
                        token0_addr,
                        token1_addr,
                        fee,
                    )
                    continue

                # Get current pool state
                pool_contract = w3.eth.contract(
                    address=Web3.to_checksum_address(pool_address), abi=POOL_ABI
                )
                slot0 = pool_contract.functions.slot0().call()
                sqrt_price_x96 = slot0[0]
                current_tick = slot0[1]

                # Get token decimals
                symbol0, _, decimals0 = get_cached_token_info(token0_addr)
                symbol1, _, decimals1 = get_cached_token_info(token1_addr)

                # Calculate amounts
                amount0, amount1 = get_amounts(
                    liquidity=liquidity,
                    sqrt_price_x96=sqrt_price_x96,
                    tick_lower=tick_lower,
                    tick_upper=tick_upper,
                    current_tick=current_tick,
                    decimals0=decimals0,
                    decimals1=decimals1,
                )

                # Calculate earned fees
                fees0 = tokens_owed0 / (10 ** decimals0)
                fees1 = tokens_owed1 / (10 ** decimals1)

                price0 = prices.get(token0_addr.lower(), 0.0)
                price1 = prices.get(token1_addr.lower(), 0.0)

                total_usd = (
                    (amount0 + fees0) * price0 + (amount1 + fees1) * price1
                )

                in_range = tick_lower <= current_tick <= tick_upper

                positions.append(
                    UniswapV3Position(
                        token_id=pos_data["token_id"],
                        token0_symbol=symbol0,
                        token1_symbol=symbol1,
                        fee_tier=fee,
                        token0_amount=amount0,
                        token1_amount=amount1,
                        fees0_earned=fees0,
                        fees1_earned=fees1,
                        total_usd=total_usd,
                        in_range=in_range,
                        tick_lower=tick_lower,
                        tick_upper=tick_upper,
                        current_tick=current_tick,
                    )
                )

            except Exception as exc:
                logger.warning(
                    "Failed to process V3 position token_id=%d: %s",
                    pos_data.get("token_id", -1),
                    exc,
                )

    except Exception as exc:
        logger.error("Failed to fetch V3 positions for %s: %s", address, exc)

    cache.set(cache_key, positions)
    return positions
