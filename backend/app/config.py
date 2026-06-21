from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_host: str = "localhost"
    database_port: int = 3306
    database_user: str = "root"
    database_password: str = "password"
    database_name: str = "fish_tank_db"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    tank_id: str = "main_tank_01"

    optimal_temp: float = 26.0
    optimal_ph: float = 7.0
    optimal_do: float = 7.0

    temp_upper_limit: float = 30.0
    temp_lower_limit: float = 22.0
    ph_upper_limit: float = 8.0
    ph_lower_limit: float = 6.0
    do_lower_limit: float = 5.0

    air_pump_base_duration: int = 10
    air_pump_max_duration: int = 60

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
