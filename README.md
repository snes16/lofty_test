# Web3 Portfolio Dashboard

A real-time Ethereum portfolio tracker that displays ETH balances, ERC-20 token holdings,
and Uniswap V2/V3 liquidity positions for any wallet address.

---

## Tech Stack

| Layer     | Technology                                          |
|-----------|-----------------------------------------------------|
| Backend   | Python 3.11, FastAPI, web3.py, httpx, Pydantic v2   |
| Frontend  | React 18, TypeScript, Vite, Tailwind CSS            |
| Data      | Alchemy (RPC + token balances), CoinGecko (prices), The Graph (Uniswap V2) |
| Infra     | Docker, docker-compose                              |

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Alchemy](https://alchemy.com) API key (free tier works)
- Optionally a [CoinGecko](https://coingecko.com) API key (free tier works without one)

---

### Option A: Docker Compose (Backend only)

```bash
# 1. Clone and enter the project
cd web3-portfolio

# 2. Create your .env file
cp backend/.env.example backend/.env
# Edit backend/.env and fill in your ALCHEMY_API_KEY

# 3. Start the backend
docker-compose up --build

# The API will be available at http://localhost:8000
```

Then start the frontend separately (see Manual Steps below).

---

### Option B: Manual Setup

#### Backend

```bash
cd web3-portfolio/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ALCHEMY_API_KEY

# Start the server
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd web3-portfolio/frontend

# Install dependencies
npm install

# Start the dev server (proxies /api to localhost:8000)
npm run dev

# Open http://localhost:3000
```

---

## API Documentation

The API auto-generates interactive docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

| Method | Path                         | Description                                  |
|--------|------------------------------|----------------------------------------------|
| GET    | `/health`                    | Health check                                 |
| GET    | `/balance/eth/{address}`     | ETH balance + USD value                      |
| GET    | `/balance/tokens/{address}`  | All ERC-20 token holdings                    |
| GET    | `/liquidity/{address}`       | Uniswap V2 + V3 LP positions                 |
| GET    | `/portfolio/{address}`       | Full portfolio (all of the above, parallel)  |

### Example

```bash
curl http://localhost:8000/portfolio/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

---

## Running Tests

```bash
cd web3-portfolio

# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v
```

### Test Coverage

- `tests/test_uniswap_math.py` — Unit tests for all V3 and V2 math (no RPC needed)
  - V3 in-range, below-range, above-range positions
  - V3 zero liquidity, proportional scaling, decimal handling
  - V2 share calculation, full share, zero total supply, decimal precision

- `tests/test_eth.py` — ETH service logic tests (web3 is mocked)
  - Wei-to-ETH conversion round trips
  - Address validation (valid, invalid, checksummed)
  - ETH balance fetching with mocked RPC

---

## Used APIs

| API           | Usage                                      | Docs                                              |
|---------------|--------------------------------------------|---------------------------------------------------|
| **Alchemy**   | ETH RPC, `alchemy_getTokenBalances`, `alchemy_getTokenMetadata` | https://docs.alchemy.com |
| **CoinGecko** | ETH price, token prices by contract address | https://www.coingecko.com/en/api             |
| **The Graph** | Uniswap V2 LP positions                    | https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v2 |
| **Uniswap V3** | On-chain: NonfungiblePositionManager, Factory, Pool | https://docs.uniswap.org/contracts/v3/reference |

---

## Test Addresses

These addresses have known balances and/or LP positions useful for testing:

| Address                                      | Notes                              |
|----------------------------------------------|------------------------------------|
| `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` | Vitalik Buterin — large ETH, tokens |
| `0x1a9C8182C09F50C8318d769245beA52c32BE35BC` | Uniswap Grants multisig            |
| `0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503` | Binance hot wallet — large balances |
| `0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8` | Binance 7 — many tokens            |

---

## Architecture Notes

### Caching

All API responses are cached in-memory with a configurable TTL (default: 60 seconds).
The `CACHE_TTL_SECONDS` environment variable controls this.

### Uniswap V3 Math

Token amounts for V3 positions are calculated using the standard Uniswap V3 tick math:

- **Below range** (`current_tick < tick_lower`): all liquidity in token0
- **In range** (`tick_lower <= current_tick <= tick_upper`): liquidity in both tokens
- **Above range** (`current_tick > tick_upper`): all liquidity in token1

See `backend/services/uniswap_v3.py` for the full implementation.

### Uniswap V2 Math

```
user_share = lp_balance / total_supply
amount0 = user_share * reserve0 / 10^decimals0
amount1 = user_share * reserve1 / 10^decimals1
```

V2 position data comes from The Graph subgraph, with an empty-list fallback if unavailable.
