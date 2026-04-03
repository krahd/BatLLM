from __future__ import annotations

import sys
from types import SimpleNamespace

import util.utils as utils
from view.home_screen import HomeScreen
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
    }

    monkeypatch.setattr("view.settings_screen.config.set", lambda section,
                        key, value: saved_values.append((section, key, value)))

    screen.update_config()

    assert ("ui", "confirm_on_exit", False) in saved_values
    assert ("ui", "prompt_save_on_exit", False) in saved_values
