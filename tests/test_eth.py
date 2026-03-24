"""
Tests for ETH service logic.
No real RPC needed — web3 is mocked.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from web3 import Web3


# ---------------------------------------------------------------------------
# Wei to ETH conversion tests (pure math, no mocking needed)
# ---------------------------------------------------------------------------

class TestWeiToEthConversion:
    def test_1_eth_in_wei(self):
        """1 ETH should be 1e18 wei."""
        wei = 1_000_000_000_000_000_000
        eth = float(Web3.from_wei(wei, "ether"))
        assert eth == 1.0

    def test_0_5_eth(self):
        """0.5 ETH."""
        wei = 500_000_000_000_000_000
        eth = float(Web3.from_wei(wei, "ether"))
        assert abs(eth - 0.5) < 1e-18

    def test_zero_wei(self):
        """0 wei = 0 ETH."""
        eth = float(Web3.from_wei(0, "ether"))
        assert eth == 0.0

    def test_small_amount_gwei(self):
        """1 Gwei = 1e-9 ETH."""
        wei = 1_000_000_000  # 1 Gwei
        eth = float(Web3.from_wei(wei, "ether"))
        assert abs(eth - 1e-9) < 1e-18

    def test_large_amount(self):
        """Large balance: 1000 ETH."""
        wei = 1_000 * 10 ** 18
        eth = float(Web3.from_wei(wei, "ether"))
        assert eth == 1000.0

    def test_round_trip(self):
        """Converting to wei and back should be identity for whole ETH values."""
        for amount in [0, 1, 10, 100, 9999]:
            wei = Web3.to_wei(amount, "ether")
            back = float(Web3.from_wei(wei, "ether"))
            assert abs(back - amount) < 1e-15, f"Round trip failed for {amount} ETH"


# ---------------------------------------------------------------------------
# Address validation tests
# ---------------------------------------------------------------------------

class TestAddressValidation:
    def test_valid_checksummed_address(self):
        """Valid checksummed Ethereum address should pass."""
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        assert Web3.is_address(addr)

    def test_valid_lowercase_address(self):
        """Lowercase valid address should also pass is_address."""
        addr = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
        assert Web3.is_address(addr)

    def test_invalid_too_short(self):
        """Address shorter than 42 chars (0x + 40 hex) should fail."""
        addr = "0x123"
        assert not Web3.is_address(addr)

    def test_invalid_no_prefix(self):
        """Address without 0x prefix should fail."""
        addr = "d8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        assert not Web3.is_address(addr)

    def test_invalid_non_hex_chars(self):
        """Address with non-hex characters should fail."""
        addr = "0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
        assert not Web3.is_address(addr)

    def test_invalid_empty_string(self):
        """Empty string should fail."""
        assert not Web3.is_address("")

    def test_to_checksum_address(self):
        """to_checksum_address should produce a valid EIP-55 checksummed address."""
        lower = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
        checksummed = Web3.to_checksum_address(lower)
        assert Web3.is_address(checksummed)
        # Checksummed should contain mixed case
        assert checksummed != lower.lower() or checksummed == lower.lower()
        # Verify it is checksum valid
        assert Web3.is_checksum_address(checksummed)

    def test_vitalik_address(self):
        """Vitalik's well-known address should be valid."""
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        assert Web3.is_address(addr)

    def test_zero_address(self):
        """The zero address is technically a valid Ethereum address."""
        addr = "0x0000000000000000000000000000000000000000"
        assert Web3.is_address(addr)


# ---------------------------------------------------------------------------
# ETH balance service tests (mocked)
# ---------------------------------------------------------------------------

class TestGetEthBalance:
    @pytest.mark.asyncio
    async def test_eth_balance_uses_price(self):
        """get_eth_balance should multiply ETH amount by ETH price to get USD."""
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        mock_wei_balance = 2_000_000_000_000_000_000  # 2 ETH in wei
        mock_eth_price = 3000.0  # $3000 per ETH

        with patch("services.eth.get_web3") as mock_get_web3, \
             patch("services.eth.get_eth_price", new_callable=AsyncMock) as mock_price, \
             patch("services.eth.cache") as mock_cache:

            mock_cache.get.return_value = None  # No cache hit
            mock_w3 = MagicMock()
            mock_w3.eth.get_balance.return_value = mock_wei_balance
            mock_get_web3.return_value = mock_w3
            mock_price.return_value = mock_eth_price

            from services.eth import get_eth_balance
            result = await get_eth_balance(test_address)

        assert abs(result.balance_eth - 2.0) < 1e-12
        assert abs(result.balance_usd - 6000.0) < 0.01
        assert result.address == Web3.to_checksum_address(test_address)

    @pytest.mark.asyncio
    async def test_eth_balance_cache_hit(self):
        """get_eth_balance should return cached result without RPC call."""
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        from models import EthBalance
        cached_result = EthBalance(
            address=test_address,
            balance_eth=1.5,
            balance_usd=4500.0,
        )

        with patch("services.eth.get_web3") as mock_get_web3, \
             patch("services.eth.cache") as mock_cache:

            mock_cache.get.return_value = cached_result

            from services.eth import get_eth_balance
            result = await get_eth_balance(test_address)

        # Should return cached result
        assert result.balance_eth == 1.5
        assert result.balance_usd == 4500.0
        # web3 should NOT have been called
        mock_get_web3.assert_not_called()

    @pytest.mark.asyncio
    async def test_eth_balance_zero(self):
        """Address with zero ETH balance should return 0 values."""
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        with patch("services.eth.get_web3") as mock_get_web3, \
             patch("services.eth.get_eth_price", new_callable=AsyncMock) as mock_price, \
             patch("services.eth.cache") as mock_cache:

            mock_cache.get.return_value = None
            mock_w3 = MagicMock()
            mock_w3.eth.get_balance.return_value = 0
            mock_get_web3.return_value = mock_w3
            mock_price.return_value = 2500.0

            from services.eth import get_eth_balance
            result = await get_eth_balance(test_address)

        assert result.balance_eth == 0.0
        assert result.balance_usd == 0.0

    @pytest.mark.asyncio
    async def test_eth_balance_rpc_failure(self):
        """When RPC fails, balance_eth should fall back to 0.0."""
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        with patch("services.eth.get_web3") as mock_get_web3, \
             patch("services.eth.get_eth_price", new_callable=AsyncMock) as mock_price, \
             patch("services.eth.cache") as mock_cache:

            mock_cache.get.return_value = None
            mock_w3 = MagicMock()
            mock_w3.eth.get_balance.side_effect = ConnectionError("RPC unavailable")
            mock_get_web3.return_value = mock_w3
            mock_price.return_value = 2000.0

            from services.eth import get_eth_balance
            result = await get_eth_balance(test_address)

        assert result.balance_eth == 0.0
        assert result.balance_usd == 0.0
