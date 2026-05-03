import argparse
import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False


DEFAULT_RECEIVER = "yggcmm@outlook.com"
DEFAULT_LANGUAGE = "Chinese"
DEFAULT_ARXIV_QUERY = "cs.AI+cs.CV+cs.LG+cs.CL"
DEFAULT_MAX_PAPER_NUM = 5
DEFAULT_OPENAI_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL_NAME = "gpt-4o"


@dataclass
class AppConfig:
    zotero_id: str
    zotero_key: str
    zotero_ignore: str | None
    send_empty: bool
    max_paper_num: int
    arxiv_query: str
    smtp_server: str
    smtp_port: int
    sender: str
    receiver: str
    sender_password: str
    use_llm_api: bool
    openai_api_key: str | None
    openai_api_base: str
    model_name: str
    language: str
    debug: bool


def _env_value(name: str, default=None):
    value = os.environ.get(name)
    if value in ("", None):
        return default
    return value


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _resolve_zotero_user_id(api_key: str) -> str:
    request = Request(
        "https://api.zotero.org/keys/current",
        headers={"Zotero-API-Key": api_key, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(f"failed to resolve Zotero user ID: HTTP {exc.code} {detail}") from exc
    except URLError as exc:
        raise ValueError(f"failed to resolve Zotero user ID: {exc.reason}") from exc

    user_id = payload.get("userID")
    if user_id is None:
        raise ValueError("failed to resolve Zotero user ID: response does not contain userID")
    return str(user_id)


def _add_argument(parser: argparse.ArgumentParser, *args, **kwargs):
    parser.add_argument(*args, **kwargs)
    arg_name = kwargs.get("dest", args[-1][2:])
    env_name = arg_name.upper()
    env_value = _env_value(env_name)
    if env_value is None:
        return
    if kwargs.get("type") is bool:
        env_value = _to_bool(env_value)
    elif kwargs.get("type") is not None:
        env_value = kwargs["type"](env_value)
    parser.set_defaults(**{arg_name: env_value})


def load_config(argv: list[str] | None = None) -> AppConfig:
    load_dotenv(override=True)

    parser = argparse.ArgumentParser(description="Recommender system for academic papers")
    _add_argument(parser, "--zotero_id", type=str, help="Zotero user ID")
    _add_argument(parser, "--zotero_key", type=str, help="Zotero API key")
    _add_argument(
        parser,
        "--zotero_ignore",
        type=str,
        help="Zotero collection to ignore, using gitignore-style pattern.",
    )
    _add_argument(
        parser,
        "--send_empty",
        type=bool,
        help="Send an empty email when no new papers are available.",
        default=False,
    )
    _add_argument(
        parser,
        "--max_paper_num",
        type=int,
        help="Maximum number of papers to recommend.",
        default=DEFAULT_MAX_PAPER_NUM,
    )
    _add_argument(
        parser,
        "--arxiv_query",
        type=str,
        help="Arxiv category query.",
        default=DEFAULT_ARXIV_QUERY,
    )
    _add_argument(parser, "--smtp_server", type=str, help="SMTP server hostname.")
    _add_argument(parser, "--smtp_port", type=int, help="SMTP server port.")
    _add_argument(parser, "--sender", type=str, help="Sender email address.")
    _add_argument(
        parser,
        "--receiver",
        type=str,
        help="Receiver email address.",
        default=DEFAULT_RECEIVER,
    )
    _add_argument(parser, "--sender_password", type=str, help="Sender SMTP password.")
    _add_argument(
        parser,
        "--use_llm_api",
        type=bool,
        help="Use OpenAI-compatible API to generate TLDR.",
        default=False,
    )
    _add_argument(parser, "--openai_api_key", type=str, help="OpenAI-compatible API key.")
    _add_argument(
        parser,
        "--openai_api_base",
        type=str,
        help="OpenAI-compatible API base URL.",
        default=DEFAULT_OPENAI_API_BASE,
    )
    _add_argument(
        parser,
        "--model_name",
        type=str,
        help="LLM model name.",
        default=DEFAULT_MODEL_NAME,
    )
    _add_argument(
        parser,
        "--language",
        type=str,
        help="TLDR language.",
        default=DEFAULT_LANGUAGE,
    )
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    args = parser.parse_args(argv)

    required_fields = {
        "zotero_key": "ZOTERO_KEY",
        "smtp_server": "SMTP_SERVER",
        "smtp_port": "SMTP_PORT",
        "sender": "SENDER",
        "sender_password": "SENDER_PASSWORD",
    }
    missing = [env_name for field, env_name in required_fields.items() if not getattr(args, field)]
    if missing:
        raise ValueError(f"missing required configuration: {', '.join(missing)}")

    if not args.zotero_id:
        args.zotero_id = _resolve_zotero_user_id(args.zotero_key)

    if args.use_llm_api and not args.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when USE_LLM_API=true")

    return AppConfig(
        zotero_id=args.zotero_id,
        zotero_key=args.zotero_key,
        zotero_ignore=args.zotero_ignore,
        send_empty=args.send_empty,
        max_paper_num=args.max_paper_num,
        arxiv_query=args.arxiv_query,
        smtp_server=args.smtp_server,
        smtp_port=args.smtp_port,
        sender=args.sender,
        receiver=args.receiver,
        sender_password=args.sender_password,
        use_llm_api=args.use_llm_api,
        openai_api_key=args.openai_api_key,
        openai_api_base=args.openai_api_base,
        model_name=args.model_name,
        language=args.language,
        debug=args.debug,
    )
