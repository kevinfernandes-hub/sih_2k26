import os
from pathlib import Path
from dotenv import load_dotenv
from sentinelhub import SHConfig

# Load .env from project root or backend directory
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def get_sh_config() -> SHConfig:
    config = SHConfig()
    config.sh_client_id = os.environ.get("SH_CLIENT_ID", "").strip()
    config.sh_client_secret = os.environ.get("SH_CLIENT_SECRET", "").strip()
    config.sh_base_url = "https://sh.dataspace.copernicus.eu"
    config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    return config

STATIC_DIR = Path(__file__).resolve().parent / "static"
RESULTS_DIR = STATIC_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
