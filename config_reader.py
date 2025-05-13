from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

class TelegramConfig(Settings):
    bot_token: SecretStr
    kassa_token: SecretStr
    receiver: SecretStr

    photo1: str
    photo2: str
    photo3: str


# При импорте файла сразу создастся 
# и провалидируется объект конфига, 
# который можно далее импортировать из разных мест
config = TelegramConfig()