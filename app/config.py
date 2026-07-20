import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    yandex_search_api_key: str = os.getenv("YANDEX_SEARCH_API_KEY", "")
    yandex_folder_id: str = os.getenv("YANDEX_FOLDER_ID", "")
    yandex_search_url: str = os.getenv(
        "YANDEX_SEARCH_URL", "https://searchapi.api.cloud.yandex.net/v2/web/search"
    )
    yandex_ai_api_key: str = os.getenv("YANDEX_AI_API_KEY", "")
    llm_base_url: str = os.getenv(
        "LLM_BASE_URL", "https://ai.api.cloud.yandex.net/v1"
    )
    llm_model: str = os.getenv(
        "LLM_MODEL", "gpt://{folder_id}/aliceai-llm-flash"
    )
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "30"))
    search_results: int = int(os.getenv("SEARCH_RESULTS", "8"))
    auth_username: str = os.getenv("AUTH_USERNAME", "")
    auth_password: str = os.getenv("AUTH_PASSWORD", "")
    auth_secret: str = os.getenv("AUTH_SECRET", "")
    auth_session_hours: int = int(os.getenv("AUTH_SESSION_HOURS", "24"))
    auth_cookie_secure: bool = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"

    @property
    def ai_api_key(self) -> str:
        return self.yandex_ai_api_key or self.yandex_search_api_key

    @property
    def resolved_llm_model(self) -> str:
        return self.llm_model.format(folder_id=self.yandex_folder_id)


settings = Settings()
