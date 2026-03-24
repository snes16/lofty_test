from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    alchemy_api_key: str = ""
    eth_rpc_url: str = "https://eth-mainnet.g.alchemy.com/v2/demo"
    coingecko_api_key: str = ""
    cache_ttl_seconds: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
