from __future__ import annotations

import sys
from types import SimpleNamespace

import util.utils as utils
from view.home_screen import HomeScreen
from view.load_text_dialog import LoadTextDialog
from view.settings_screen import SettingsScreen


class FakeField:
    def __init__(self, value=None, active=None):
        self.value = value
        self.active = active


class FakeApp:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeKeyboard:
    def __init__(self):
        self.on_key_down = None

    def bind(self, on_key_down=None, **_kwargs):
        self.on_key_down = on_key_down

    def unbind(self, on_key_down=None, **_kwargs):
        if self.on_key_down == on_key_down:
            self.on_key_down = None


class FakeBoxLayout:
    def __init__(self, *args, **kwargs):
        self.children = []
        self.kwargs = kwargs

    def add_widget(self, widget):
        self.children.append(widget)


class FakeButton:
    instances = []

    def __init__(self, *args, text="", **kwargs):
        self.text = text
        self.kwargs = kwargs
        self._on_release = None
        FakeButton.instances.append(self)

    def bind(self, on_release=None, **_kwargs):
        if on_release is not None:
            self._on_release = on_release


class FakeTextInput:
    def __init__(self, *args, text="", hint_text="", **kwargs):
        self.text = text
        self.hint_text = hint_text
        self.kwargs = kwargs


class FakeLabel:
    def __init__(self, *args, text="", **kwargs):
        self.text = text
        self.kwargs = kwargs


class FakePopup:
    last = None

    def __init__(self, *args, title="", content=None, **kwargs):
        self.title = title
        self.content = content
        self.kwargs = kwargs
        self._on_open = None
        self._on_dismiss = None
        FakePopup.last = self

    def bind(self, on_open=None, on_dismiss=None, **_kwargs):
        if on_open is not None:
            self._on_open = on_open
        if on_dismiss is not None:
            self._on_dismiss = on_dismiss

    def open(self):
        if self._on_open is not None:
            self._on_open()

    def dismiss(self):
        if self._on_dismiss is not None:
            self._on_dismiss()


def test_show_text_input_dialog_escape_acts_like_cancel(monkeypatch) -> None:
    canceled = {"value": False}
    keyboard = FakeKeyboard()
    FakeButton.instances = []
    FakePopup.last = None

    monkeypatch.setattr(utils, "BoxLayout", FakeBoxLayout)
    monkeypatch.setattr(utils, "Button", FakeButton)
    monkeypatch.setattr(utils, "TextInput", FakeTextInput)
    monkeypatch.setattr(utils, "Label", FakeLabel)
    monkeypatch.setattr(utils, "Popup", FakePopup)
    monkeypatch.setattr(utils.Window, "request_keyboard", lambda _closed, _owner: keyboard)

    utils.show_text_input_dialog(
        on_confirm=lambda _value: None,
        on_cancel=lambda: canceled.__setitem__("value", True),
        title="Save As",
        message="Please enter a filename.",
        confirm_text="Save",
        cancel_text="Don't Save",
    )

    assert [button.text for button in FakeButton.instances] == ["Save", "Don't Save"]
    assert keyboard.on_key_down is not None

    keyboard.on_key_down(keyboard, (27, "escape"), "", [])

    assert canceled["value"] is True


def test_home_screen_close_uses_dont_save_label_when_prompt_enabled(monkeypatch) -> None:
    screen = HomeScreen()
    fake_app = FakeApp()
    captured = {}
    exited = {"code": None}

    config_values = {
        ("ui", "confirm_on_exit"): True,
        ("ui", "prompt_save_on_exit"): True,
    }

    monkeypatch.setattr(
        "view.home_screen.config.get",
        lambda section, key: config_values.get((section, key)),
    )
    monkeypatch.setattr("view.home_screen.show_confirmation_dialog", lambda title,
                        message, on_confirm, on_cancel=None: on_confirm())

    def fake_text_input_dialog(**kwargs):
        captured.update(kwargs)
        kwargs["on_cancel"]()

    monkeypatch.setattr("view.home_screen.show_text_input_dialog", fake_text_input_dialog)
    monkeypatch.setattr("view.home_screen.App.get_running_app", lambda: fake_app)
    monkeypatch.setattr(sys, "exit", lambda code=0: exited.__setitem__("code", code))

    assert screen.on_request_close() is True
    assert captured["confirm_text"] == "Save"
    assert captured["cancel_text"] == "Don't Save"
    assert fake_app.stopped is True
    assert exited["code"] == 0


def test_home_screen_escape_uses_close_flow(monkeypatch) -> None:
    screen = HomeScreen()
    close_called = {"value": False}

    monkeypatch.setattr(
        screen,
        "on_request_close",
        lambda *args, **kwargs: close_called.__setitem__("value", True) or True,
    )

    assert screen.handle_window_key_down(None, 27) is True
    assert close_called["value"] is True


def test_home_screen_escape_cancels_save_session_confirmation(monkeypatch) -> None:
    screen = HomeScreen()
    close_called = {"value": False}
    filename_dialog_called = {"value": False}

    class FakeConfirmationPopup:
        def __init__(self, cancel_action):
            self.cancel_action = cancel_action
            self._on_dismiss = None

        def bind(self, on_dismiss=None, **_kwargs):
            if on_dismiss is not None:
                self._on_dismiss = on_dismiss

        def dismiss(self):
            if self._on_dismiss is not None:
                self._on_dismiss(self)

    def fake_show_confirmation_dialog(_title, _message, _on_confirm, on_cancel=None):
        popup = None

        def cancel_action(*_args):
            popup.dismiss()
            if on_cancel is not None:
                on_cancel()

        popup = FakeConfirmationPopup(cancel_action)
        return popup

    monkeypatch.setattr("view.home_screen.show_confirmation_dialog", fake_show_confirmation_dialog)
    monkeypatch.setattr(
        "view.home_screen.show_text_input_dialog",
        lambda **_kwargs: filename_dialog_called.__setitem__("value", True),
    )
    monkeypatch.setattr(
        screen,
        "on_request_close",
        lambda *args, **kwargs: close_called.__setitem__("value", True) or True,
    )

    screen.save_session()

    assert getattr(screen, "_active_confirmation_popup", None) is not None
    assert screen.handle_window_key_down(None, 27) is True
    assert close_called["value"] is False
    assert filename_dialog_called["value"] is False
    assert getattr(screen, "_active_confirmation_popup", None) is None


def test_home_screen_load_prompt_suspends_escape_close_handler(monkeypatch) -> None:
    screen = HomeScreen()
    window_calls = []

    class FakeLoadPromptDialog:
        last = None

        def __init__(self, on_choice, start_dir=None, **_kwargs):
            self.on_choice = on_choice
            self.start_dir = start_dir
            self._on_dismiss = None
            self.opened = False
            self.dismissed = False
            FakeLoadPromptDialog.last = self

        def bind(self, on_dismiss=None, **_kwargs):
            if on_dismiss is not None:
                self._on_dismiss = on_dismiss

        def open(self):
            self.opened = True

        def dismiss(self):
            self.dismissed = True
            if self._on_dismiss is not None:
                self._on_dismiss(self)

    monkeypatch.setattr("view.home_screen.LoadTextDialog", FakeLoadPromptDialog)
    monkeypatch.setattr("view.home_screen.prompt_asset_dir", lambda: "/tmp/prompts")
    monkeypatch.setattr(
        "view.home_screen.Window.unbind",
        lambda **kwargs: window_calls.append(("unbind", kwargs.get("on_key_down"))),
    )
    monkeypatch.setattr(
        "view.home_screen.Window.bind",
        lambda **kwargs: window_calls.append(("bind", kwargs.get("on_key_down"))),
    )

    screen.load_prompt(1)

    assert FakeLoadPromptDialog.last is not None
    assert FakeLoadPromptDialog.last.opened is True
    assert getattr(screen, "_active_load_prompt_dialog", None) is FakeLoadPromptDialog.last
    assert [call[0] for call in window_calls] == ["unbind"]

    FakeLoadPromptDialog.last.dismiss()

    assert getattr(screen, "_active_load_prompt_dialog", None) is None
    assert [call[0] for call in window_calls] == ["unbind", "unbind", "bind"]


def test_home_screen_escape_dismisses_active_load_prompt_dialog(monkeypatch) -> None:
    screen = HomeScreen()
    close_called = {"value": False}
    dismissed = {"value": False}

    class FakeLoadPromptDialog:
        def dismiss(self):
            dismissed["value"] = True

    screen._active_load_prompt_dialog = FakeLoadPromptDialog()
    monkeypatch.setattr(
        screen,
        "on_request_close",
        lambda *args, **kwargs: close_called.__setitem__("value", True) or True,
    )

    assert screen.handle_window_key_down(None, 27) is True
    assert dismissed["value"] is True
    assert close_called["value"] is False
    assert getattr(screen, "_active_load_prompt_dialog", None) is None



def test_home_screen_close_skips_save_prompt_when_disabled(monkeypatch) -> None:
    screen = HomeScreen()
    fake_app = FakeApp()
    exited = {"code": None}
    text_prompt_called = {"value": False}

    config_values = {
        ("ui", "confirm_on_exit"): True,
        ("ui", "prompt_save_on_exit"): False,
    }

    monkeypatch.setattr(
        "view.home_screen.config.get",
        lambda section, key: config_values.get((section, key)),
    )
    monkeypatch.setattr("view.home_screen.show_confirmation_dialog", lambda title,
                        message, on_confirm, on_cancel=None: on_confirm())
    monkeypatch.setattr("view.home_screen.show_text_input_dialog", lambda **
                        _kwargs: text_prompt_called.__setitem__("value", True))
    monkeypatch.setattr("view.home_screen.App.get_running_app", lambda: fake_app)
    monkeypatch.setattr(sys, "exit", lambda code=0: exited.__setitem__("code", code))

    assert screen.on_request_close() is True
    assert text_prompt_called["value"] is False
    assert fake_app.stopped is True
    assert exited["code"] == 0


def test_home_screen_close_skips_confirmation_but_still_prompts_to_save(monkeypatch) -> None:
    screen = HomeScreen()
    fake_app = FakeApp()
    confirmation_called = {"value": False}
    prompt_called = {"value": False}
    exited = {"code": None}

    config_values = {
        ("ui", "confirm_on_exit"): False,
        ("ui", "prompt_save_on_exit"): True,
    }

    monkeypatch.setattr(
        "view.home_screen.config.get",
        lambda section, key: config_values.get((section, key)),
    )
    monkeypatch.setattr(
        "view.home_screen.show_confirmation_dialog",
        lambda *args, **kwargs: confirmation_called.__setitem__("value", True),
    )

    def fake_text_input_dialog(**kwargs):
        prompt_called["value"] = True
        kwargs["on_cancel"]()

    monkeypatch.setattr("view.home_screen.show_text_input_dialog", fake_text_input_dialog)
    monkeypatch.setattr("view.home_screen.App.get_running_app", lambda: fake_app)
    monkeypatch.setattr(sys, "exit", lambda code=0: exited.__setitem__("code", code))

    assert screen.on_request_close() is True
    assert confirmation_called["value"] is False
    assert prompt_called["value"] is True
    assert fake_app.stopped is True
    assert exited["code"] == 0


def test_home_screen_close_skips_all_prompts_when_both_disabled(monkeypatch) -> None:
    screen = HomeScreen()
    fake_app = FakeApp()
    confirmation_called = {"value": False}
    prompt_called = {"value": False}
    exited = {"code": None}

    config_values = {
        ("ui", "confirm_on_exit"): False,
        ("ui", "prompt_save_on_exit"): False,
    }

    monkeypatch.setattr(
        "view.home_screen.config.get",
        lambda section, key: config_values.get((section, key)),
    )
    monkeypatch.setattr(
        "view.home_screen.show_confirmation_dialog",
        lambda *args, **kwargs: confirmation_called.__setitem__("value", True),
    )
    monkeypatch.setattr(
        "view.home_screen.show_text_input_dialog",
        lambda **_kwargs: prompt_called.__setitem__("value", True),
    )
    monkeypatch.setattr("view.home_screen.App.get_running_app", lambda: fake_app)
    monkeypatch.setattr(sys, "exit", lambda code=0: exited.__setitem__("code", code))

    assert screen.on_request_close() is True
    assert confirmation_called["value"] is False
    assert prompt_called["value"] is False
    assert fake_app.stopped is True
    assert exited["code"] == 0


def test_settings_escape_matches_cancel(monkeypatch) -> None:
    screen = SettingsScreen()
    screen.manager = SimpleNamespace(current="settings")
    cancel_called = {"value": False}

    monkeypatch.setattr(
        screen,
        "cancel_and_return",
        lambda: cancel_called.__setitem__("value", True) or setattr(
            screen.manager, "current", "home"),
    )

    assert screen.handle_window_key_down(None, 27) is True
    assert cancel_called["value"] is True
    assert screen.manager.current == "home"



def test_settings_update_config_persists_save_on_exit_flag(monkeypatch) -> None:
    screen = SettingsScreen()
    saved_values = []
    screen.ids = {
        "rounds_slider": FakeField(value=2),
        "turns_slider": FakeField(value=8),
        "health_slider": FakeField(value=30),
        "damage_slider": FakeField(value=5),
        "shield_slider": FakeField(value=70),
        "step_slider": FakeField(value=0.03),
        "independent_checkbox": FakeField(active=True),
        "augmentation_checkbox": FakeField(active=True),
        "confirm_on_exit_checkbox": FakeField(active=False),
        "save_on_exit_checkbox": FakeField(active=False),
        "auto_start_ollama_checkbox": FakeField(active=True),
        "stop_ollama_on_exit_checkbox": FakeField(active=True),
    }

    monkeypatch.setattr("view.settings_screen.config.set", lambda section,
                        key, value: saved_values.append((section, key, value)))

    screen.update_config()

    assert ("ui", "confirm_on_exit", False) in saved_values
    assert ("ui", "prompt_save_on_exit", False) in saved_values
    assert ("ui", "auto_start_ollama", True) in saved_values
    assert ("ui", "stop_ollama_on_exit", True) in saved_values
