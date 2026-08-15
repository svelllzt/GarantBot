from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    admin_ids: str = ""
    support_username: str = "support"
    support_chat: str = ""
    commission_percent: float = 2.0
    currency: str = "USDT"
    min_deposit: float = 5.0
    min_withdraw: float = 10.0

    bank_api_id: int = 0
    bank_api_hash: str = ""
    bank_session: str = ""
    bank_username: str = ""

    ton_address: str = ""
    ton_api_key: str = ""
    ton_rate: float = 0.0
    ton_mnemonic: str = ""
    ton_network: str = "mainnet"
    ton_gas: float = 0.05
    min_ton_deal: float = 0.1
    min_rub_deal: float = 1.0

    db_path: str = "data/garant.db"

    @property
    def admins(self) -> frozenset[int]:
        ids = []
        for chunk in self.admin_ids.split(","):
            chunk = chunk.strip()
            if chunk.isdigit():
                ids.append(int(chunk))
        return frozenset(ids)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins


@lru_cache
def get_settings() -> Settings:
    return Settings()
