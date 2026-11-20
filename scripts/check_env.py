import re
from pathlib import Path
from typing import cast

from dotenv import dotenv_values
from pydantic_settings import BaseSettings
from tyche_ai.job_search.settings import JobSearchSettings
from worker.settings import Settings as WorkerSettings

from api.settings import Settings as ApiSettings

ROOT = Path(__file__).resolve().parent.parent
example = {key: value or "" for key, value in dotenv_values(ROOT / ".env.example").items()}


def aliases(settings: type[BaseSettings]) -> set[str]:
    return {
        cast(str, field.validation_alias or name).upper()
        for name, field in settings.model_fields.items()
    }


runtime_keys = (
    aliases(ApiSettings) | aliases(WorkerSettings) | aliases(JobSearchSettings) | {"VITE_API_URL"}
)
compose = (ROOT / "docker-compose.yaml").read_text()
compose_keys = set(re.findall(r"\$\{([A-Z_][A-Z0-9_]*)", compose))
missing = sorted(runtime_keys - example.keys())
unknown = sorted(example.keys() - runtime_keys - compose_keys)

if missing or unknown:
    raise RuntimeError(f"Environment documentation drift: missing {missing}; unknown {unknown}.")

ApiSettings.model_validate(example)
WorkerSettings.model_validate(example)
JobSearchSettings.model_validate(example)
print("Environment example matches application schemas.")
