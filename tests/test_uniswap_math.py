"""
Tests for Uniswap V2 and V3 math calculations.
These tests do not require any network connections or RPC access.
"""
import math
import sys
from pathlib import Path

# Add backend to path so we can import the services
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest

from services.uniswap_v3 import get_amounts, tick_to_sqrt_price, Q96
from services.uniswap_v2 import _calculate_v2_position


# ---------------------------------------------------------------------------
# Uniswap V3 math tests
# ---------------------------------------------------------------------------

class TestV3TickToSqrtPrice:
    def test_tick_zero_returns_one(self):
        """At tick 0, sqrt price should be 1.0."""
        result = tick_to_sqrt_price(0)
        assert abs(result - 1.0) < 1e-10

    def test_positive_tick_greater_than_one(self):
        """Positive ticks should give sqrt price > 1."""
        result = tick_to_sqrt_price(100)
        assert result > 1.0

    def test_negative_tick_less_than_one(self):
        """Negative ticks should give sqrt price < 1."""
        result = tick_to_sqrt_price(-100)
        assert result < 1.0

    def test_tick_symmetry(self):
        """tick_to_sqrt_price(t) * tick_to_sqrt_price(-t) should be approx 1."""
        for tick in [100, 1000, 60000]:
            pos = tick_to_sqrt_price(tick)
            neg = tick_to_sqrt_price(-tick)
            assert abs(pos * neg - 1.0) < 1e-6


class TestV3GetAmounts:
    """
    Tests for the core V3 liquidity math function.
    """

    def _make_sqrt_price_x96(self, tick: int) -> int:
        """Convert a tick to a sqrtPriceX96 integer value."""
        sqrt_price = tick_to_sqrt_price(tick)
        return int(sqrt_price * Q96)

    def test_v3_in_range(self):
        """
        When current_tick is within [tick_lower, tick_upper],
        both token amounts should be > 0.
        """
        tick_lower = -1000
        tick_upper = 1000
        current_tick = 0  # In range
        liquidity = 1_000_000_000_000_000_000  # 1e18

        sqrt_price_x96 = self._make_sqrt_price_x96(current_tick)

        amount0, amount1 = get_amounts(
            liquidity=liquidity,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )

        assert amount0 > 0, f"Expected amount0 > 0 when in range, got {amount0}"
        assert amount1 > 0, f"Expected amount1 > 0 when in range, got {amount1}"

    def test_v3_below_range(self):
        """
        When current_tick < tick_lower, all liquidity is in token0
        so amount1 should be 0.
        """
        tick_lower = 1000
        tick_upper = 2000
        current_tick = 500  # Below range
        liquidity = 1_000_000_000_000_000_000

        sqrt_price_x96 = self._make_sqrt_price_x96(current_tick)

        amount0, amount1 = get_amounts(
            liquidity=liquidity,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )

        assert amount0 > 0, f"Expected amount0 > 0 when below range, got {amount0}"
        assert amount1 == 0.0, f"Expected amount1 == 0 when below range, got {amount1}"

    def test_v3_above_range(self):
        """
        When current_tick > tick_upper, all liquidity is in token1
        so amount0 should be 0.
        """
        tick_lower = -2000
        tick_upper = -1000
        current_tick = -500  # Above range
        liquidity = 1_000_000_000_000_000_000

        sqrt_price_x96 = self._make_sqrt_price_x96(current_tick)

        amount0, amount1 = get_amounts(
            liquidity=liquidity,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )

        assert amount0 == 0.0, f"Expected amount0 == 0 when above range, got {amount0}"
        assert amount1 > 0, f"Expected amount1 > 0 when above range, got {amount1}"

    def test_v3_zero_liquidity(self):
        """With zero liquidity, both amounts should be 0."""
        tick_lower = -1000
        tick_upper = 1000
        current_tick = 0
        liquidity = 0

        sqrt_price_x96 = self._make_sqrt_price_x96(current_tick)

        amount0, amount1 = get_amounts(
            liquidity=liquidity,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )

        assert amount0 == 0.0
        assert amount1 == 0.0

    def test_v3_amounts_increase_with_liquidity(self):
        """Higher liquidity should result in proportionally higher amounts."""
        tick_lower = -1000
        tick_upper = 1000
        current_tick = 0

        sqrt_price_x96 = self._make_sqrt_price_x96(current_tick)

        liquidity_small = 1_000_000_000
        liquidity_large = 10_000_000_000  # 10x larger

        a0_small, a1_small = get_amounts(
            liquidity=liquidity_small,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )

        a0_large, a1_large = get_amounts(
            liquidity=liquidity_large,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )

        assert a0_large > a0_small, "Larger liquidity should give more token0"
        assert a1_large > a1_small, "Larger liquidity should give more token1"

        # Should be proportional (within floating point tolerance)
        ratio0 = a0_large / a0_small
        ratio1 = a1_large / a1_small
        assert abs(ratio0 - 10.0) < 0.001, f"Expected 10x ratio for amount0, got {ratio0}"
        assert abs(ratio1 - 10.0) < 0.001, f"Expected 10x ratio for amount1, got {ratio1}"

    def test_v3_decimals_scaling(self):
        """Different decimals should correctly scale the output amounts."""
        tick_lower = -1000
        tick_upper = 1000
        current_tick = 0
        liquidity = 1_000_000_000_000_000_000

        sqrt_price_x96 = self._make_sqrt_price_x96(current_tick)

        amount0_18, _ = get_amounts(
            liquidity=liquidity,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )

        amount0_6, _ = get_amounts(
            liquidity=liquidity,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=6,
            decimals1=18,
        )

        # With 6 decimals, the human-readable amount should be much larger
        assert amount0_6 > amount0_18 * 1e10

    def test_v3_at_boundary_tick_lower(self):
        """When current_tick == tick_lower, position is in range."""
        tick_lower = -500
        tick_upper = 500
        current_tick = -500  # exactly at lower boundary (in range by <=)

        sqrt_price_x96 = self._make_sqrt_price_x96(current_tick)
        liquidity = 1_000_000_000_000_000_000

        amount0, amount1 = get_amounts(
            liquidity=liquidity,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )
        # At lower boundary, mostly token0, but both should be >= 0
        assert amount0 >= 0
        assert amount1 >= 0

    def test_v3_at_boundary_tick_upper(self):
        """When current_tick == tick_upper, position is in range."""
        tick_lower = -500
        tick_upper = 500
        current_tick = 500  # exactly at upper boundary

        sqrt_price_x96 = self._make_sqrt_price_x96(current_tick)
        liquidity = 1_000_000_000_000_000_000

        amount0, amount1 = get_amounts(
            liquidity=liquidity,
            sqrt_price_x96=sqrt_price_x96,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            current_tick=current_tick,
            decimals0=18,
            decimals1=18,
        )
        assert amount0 >= 0
        assert amount1 >= 0


# ---------------------------------------------------------------------------
# Uniswap V2 math tests
# ---------------------------------------------------------------------------

class TestV2ShareCalculation:
    """Tests for Uniswap V2 LP share and amount calculation."""

    def test_v2_share_calculation(self):
        """
        Test basic share calculation: 10 LP / 1000 total supply = 1% share.
        """
        position = _calculate_v2_position(
            lp_balance=10.0,
            total_supply=1000.0,
            reserve0=500_000 * 10 ** 18,  # 500,000 token0 raw
            reserve1=1_000_000 * 10 ** 6,  # 1,000,000 USDC raw
            decimals0=18,
            decimals1=6,
            price0_usd=2000.0,
            price1_usd=1.0,
            pair_address="0x0000000000000000000000000000000000000001",
            token0_symbol="WETH",
            token1_symbol="USDC",
        )

        assert abs(position.share_percent - 1.0) < 1e-9
        assert abs(position.lp_balance - 10.0) < 1e-9

        # 1% of 500,000 token0 = 5,000
        assert abs(position.token0_amount - 5_000.0) < 1e-6
        # 1% of 1,000,000 token1 = 10,000
        assert abs(position.token1_amount - 10_000.0) < 1e-6

        # total_usd = 5000 * 2000 + 10000 * 1 = 10,000,000 + 10,000 = 10,010,000
        assert abs(position.total_usd - 10_010_000.0) < 1.0

    def test_v2_zero_total_supply(self):
        """With zero total supply, share should be 0 and amounts should be 0."""
        position = _calculate_v2_position(
            lp_balance=10.0,
            total_supply=0.0,
            reserve0=1000 * 10 ** 18,
            reserve1=1000 * 10 ** 18,
            decimals0=18,
            decimals1=18,
            price0_usd=1.0,
            price1_usd=1.0,
            pair_address="0x0000000000000000000000000000000000000001",
            token0_symbol="TOKEN0",
            token1_symbol="TOKEN1",
        )
        assert position.share_percent == 0.0
        assert position.token0_amount == 0.0
        assert position.token1_amount == 0.0
        assert position.total_usd == 0.0

    def test_v2_full_share(self):
        """If lp_balance == total_supply, share should be 100%."""
        position = _calculate_v2_position(
            lp_balance=1000.0,
            total_supply=1000.0,
            reserve0=500 * 10 ** 18,
            reserve1=500 * 10 ** 18,
            decimals0=18,
            decimals1=18,
            price0_usd=1.0,
            price1_usd=1.0,
            pair_address="0x0000000000000000000000000000000000000001",
            token0_symbol="TOKEN0",
            token1_symbol="TOKEN1",
        )
        assert abs(position.share_percent - 100.0) < 1e-9
        assert abs(position.token0_amount - 500.0) < 1e-9
        assert abs(position.token1_amount - 500.0) < 1e-9

    def test_v2_zero_prices(self):
        """With zero prices, total_usd should be 0 but amounts should still be correct."""
        position = _calculate_v2_position(
            lp_balance=100.0,
            total_supply=1000.0,
            reserve0=1000 * 10 ** 18,
            reserve1=1000 * 10 ** 18,
            decimals0=18,
            decimals1=18,
            price0_usd=0.0,
            price1_usd=0.0,
            pair_address="0x0000000000000000000000000000000000000001",
            token0_symbol="TOKEN0",
            token1_symbol="TOKEN1",
        )
        assert position.total_usd == 0.0
        assert position.token0_amount > 0
        assert position.token1_amount > 0

    def test_v2_decimal_precision(self):
        """Test with typical USDC (6 decimals) and WETH (18 decimals) pair."""
        # Typical WETH/USDC pool with $1 liquidity each side:
        # reserve0 = 0.5 WETH = 5e17 wei
        # reserve1 = 1000 USDC = 1e9 micro-USDC
        position = _calculate_v2_position(
            lp_balance=1.0,
            total_supply=100.0,
            reserve0=50 * 10 ** 18,   # 50 WETH
            reserve1=100_000 * 10 ** 6,  # 100,000 USDC
            decimals0=18,
            decimals1=6,
            price0_usd=2000.0,
            price1_usd=1.0,
            pair_address="0x0000000000000000000000000000000000000001",
            token0_symbol="WETH",
            token1_symbol="USDC",
        )
        # 1% share
        assert abs(position.token0_amount - 0.5) < 1e-9   # 0.5 WETH
        assert abs(position.token1_amount - 1000.0) < 1e-6  # 1000 USDC
        # USD = 0.5 * 2000 + 1000 * 1 = 1000 + 1000 = 2000
        assert abs(position.total_usd - 2000.0) < 0.01
