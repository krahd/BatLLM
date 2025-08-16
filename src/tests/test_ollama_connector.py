import importlib.util
import sys
import types
from pathlib import Path

import pytest


def _stub_external_modules():
    # Stub 'ollama' with a minimal Client
    ollama_mod = types.ModuleType("ollama")

    class DummyClient:
        """
        A minimal test double that simulates a chat - capable client.

        This class mirrors the interface of a real chat client while avoiding any
        network calls. It captures initialization parameters and produces a fixed,
        deterministic response from chat(), making it suitable for use in unit tests.

        Parameters
        ----------
        host: str | None
            Optional base URL or host to associate with the client.
        timeout: float | int | None
            Optional request timeout in seconds.

        Attributes
        ----------
        host: str | None
            The host value provided at initialization.
        timeout: float | int | None
            The timeout value provided at initialization.

        Methods
        -------
        chat(**kwargs)
            Accepts arbitrary keyword arguments to resemble a real client API and
            returns a fixed response payload:
            {
                "message": {"role": "assistant", "content": "ok"},
                "context": [1, 2, 3],
            }

        Returns(chat)
        --------------
        dict
            A predictable response useful for assertions in tests.

        Examples
        --------
        >> > client = DummyClient(host="http://localhost:11434", timeout=30)
        >> > client.chat(model=\"foo\", messages=[{\"role\": \"user\", \"content\": \"Hi\"}])
        {'message': {'role': 'assistant', 'content': 'ok'}, 'context': [1, 2, 3]}
        """



        def __init__(self, host=None, timeout=None):
            self.host = host
            self.timeout = timeout



        def chat(self, **kwargs):
            """            Simulates a chat request and returns a fixed response.           
            Args:
                **kwargs: Arbitrary keyword arguments to mimic a real chat client API.
            Returns:
                dict: A fixed response payload.
            """
            return {"message": {"role": "assistant", "content": "ok"}, "context": [1, 2, 3]}


    ollama_mod.Client = DummyClient
    sys.modules["ollama"] = ollama_mod

    # Stub 'configs.app_config' with a minimal 'config'
    configs_pkg = types.ModuleType("configs")
    app_config_mod = types.ModuleType("configs.app_config")

    class DummyConfig:
        """        A minimal test double for the app configuration module.
        This class provides a simple interface to retrieve configuration values
        with sensible defaults for testing purposes.
        """

        def get(self, section, key):
            """get

            Args:
                section (_type_): _description_
                key (_type_): _description_

            Returns:
                _type_: _description_
            """

            # Provide sane defaults for any key lookup
            defaults = {
                "temperature": None,
                "top_p": None,
                "top_k": None,
                "timeout": None,
                "max_tokens": None,
                "stop": None,
                "seed": None,
                "num_thread": None,
                "model": "dummy-model",
                "url": "http://localhost",
                "port": "11434",
                "path": "",
                "num_ctx": None,
                "num_predict": None,
                # augmentation header files: point to a non-existent path not used in these tests
                "augmented_header_independent": "",
                "augmented_header_shared": "",
                "not_augmented_header_independent": "",
                "not_augmented_header_shared": "",
            }
            return defaults.get(key)

    app_config_mod.config = DummyConfig()

    sys.modules["configs"] = configs_pkg
    sys.modules["configs.app_config"] = app_config_mod


def _load_ollama_connector():
    _stub_external_modules()
    module_path = Path(__file__).with_name("ollama_connector.py")
    spec = importlib.util.spec_from_file_location("game.ollama_connector", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader, "Failed to create module spec for ollama_connector.py"
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod.OllamaConnector


def test_update_options_exposed_by_ui_sets_both_true():
    """_summary_
    """

    ollama_connector = _load_ollama_connector()
    conn = ollama_connector()

    # Initial defaults from __init__
    assert conn.augmenting_prompt is False
    assert conn.independent_contexts is False

    conn.update_options_exposed_by_ui(augmenting_prompt=True, independent_contexts=True)

    assert conn.augmenting_prompt is True
    assert conn.independent_contexts is True


@pytest.mark.parametrize(
    "initial_aug, initial_indep, new_aug, new_indep",
    [
        (False, False, False, True),
        (True, True, False, False),
        (True, False, True, False),
        (False, True, True, True),
    ],
)


def test_update_options_exposed_by_ui_overwrites_values(initial_aug: bool, initial_indep: bool, new_aug: bool, new_indep: bool):
    """_summary_
    """

    ollama_connector = _load_ollama_connector()
    conn = ollama_connector()

    # Manually set initial state
    conn.augmenting_prompt = initial_aug
    conn.independent_contexts = initial_indep

    conn.update_options_exposed_by_ui(augmenting_prompt=new_aug, independent_contexts=new_indep)

    assert conn.augmenting_prompt is new_aug
    assert conn.independent_contexts is new_indep
