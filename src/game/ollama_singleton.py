"""Ollama Connector singleton"""
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import atexit

from configs.app_config import config
from game.ollama_connector import OllamaConnector


# TODO call reset_contexts() or reset_singletons() after any changes in Settings_Screen
# TODO add a button "refresh to Settings_Screen to reload parameters for the connector
# TODO add a button in home screen to open a new window with the contet and a CLI conversation so that the players can investigate the LLM

@lru_cache(maxsize=1)
def get_connector() -> OllamaConnector:
    """Singleton for the Ollama connector."""

    conn = OllamaConnector()
    conn.load_options()

    return conn

@lru_cache(maxsize=1)
def get_executor(*_args, **_kwargs) -> ThreadPoolExecutor:
    """Singleton for the Ollama connector thread pool executor."""
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ollama")
    atexit.register(pool.shutdown, wait=False, cancel_futures=True)
    return pool



def reset_singletons() -> None:
    """Reset the singleton instances."""
    info = get_executor.cache_info()
    if info.hits or info.misses:
        pool = get_executor()
        shutdown = getattr(pool, "shutdown", None)
        if callable(shutdown):
            shutdown(wait=False, cancel_futures=True)

    get_executor.cache_clear()
    get_connector.cache_clear()
