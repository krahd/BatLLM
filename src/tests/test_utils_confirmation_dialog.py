from __future__ import annotations

from util import utils


class FakeBoxLayout:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.children = []

    def add_widget(self, widget):
        self.children.append(widget)


class FakeLabel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeButton:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._bindings = {}
        FakeButton.instances.append(self)

    def bind(self, **kwargs):
        self._bindings.update(kwargs)


class FakeKeyboard:
    def __init__(self):
        self._bindings = {}

    def bind(self, **kwargs):
        self._bindings.update(kwargs)

    def unbind(self, **kwargs):
        for key, callback in kwargs.items():
            if self._bindings.get(key) == callback:
                del self._bindings[key]

    def press(self, key: str):
        return self._bindings["on_key_down"](self, (None, key), "", [])


class FakePopup:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._bindings = {}
        self.dismissed = False
        FakePopup.instances.append(self)

    def bind(self, **kwargs):
        self._bindings.update(kwargs)

    def open(self):
        on_open = self._bindings.get("on_open")
        if on_open:
            on_open(self)

    def dismiss(self):
        self.dismissed = True
        on_dismiss = self._bindings.get("on_dismiss")
        if on_dismiss:
            on_dismiss(self)


class FakeWindow:
    def __init__(self, keyboard):
        self.keyboard = keyboard

    def request_keyboard(self, _closed, _widget):
        return self.keyboard


def test_confirmation_dialog_enter_confirms(monkeypatch) -> None:
    keyboard = FakeKeyboard()
    confirmed = {"value": False}
    cancelled = {"value": False}

    FakePopup.instances.clear()
    FakeButton.instances.clear()
    monkeypatch.setattr(utils, "BoxLayout", FakeBoxLayout)
    monkeypatch.setattr(utils, "Label", FakeLabel)
    monkeypatch.setattr(utils, "Button", FakeButton)
    monkeypatch.setattr(utils, "Popup", FakePopup)
    monkeypatch.setattr(utils, "Window", FakeWindow(keyboard))

    utils.show_confirmation_dialog(
        "Confirm",
        "Proceed?",
        on_confirm=lambda: confirmed.__setitem__("value", True),
        on_cancel=lambda: cancelled.__setitem__("value", True),
    )

    handled = keyboard.press("enter")

    assert handled is True
    assert confirmed["value"] is True
    assert cancelled["value"] is False
    assert FakePopup.instances[0].dismissed is True
    assert "on_key_down" not in keyboard._bindings


def test_confirmation_dialog_escape_cancels(monkeypatch) -> None:
    keyboard = FakeKeyboard()
    confirmed = {"value": False}
    cancelled = {"value": False}

    FakePopup.instances.clear()
    FakeButton.instances.clear()
    monkeypatch.setattr(utils, "BoxLayout", FakeBoxLayout)
    monkeypatch.setattr(utils, "Label", FakeLabel)
    monkeypatch.setattr(utils, "Button", FakeButton)
    monkeypatch.setattr(utils, "Popup", FakePopup)
    monkeypatch.setattr(utils, "Window", FakeWindow(keyboard))

    utils.show_confirmation_dialog(
        "Confirm",
        "Proceed?",
        on_confirm=lambda: confirmed.__setitem__("value", True),
        on_cancel=lambda: cancelled.__setitem__("value", True),
    )

    handled = keyboard.press("escape")

    assert handled is True
    assert confirmed["value"] is False
    assert cancelled["value"] is True
    assert FakePopup.instances[0].dismissed is True
    assert "on_key_down" not in keyboard._bindings


def test_confirmation_dialog_cancel_action_matches_no(monkeypatch) -> None:
    keyboard = FakeKeyboard()
    confirmed = {"value": False}
    cancelled = {"value": False}

    FakePopup.instances.clear()
    FakeButton.instances.clear()
    monkeypatch.setattr(utils, "BoxLayout", FakeBoxLayout)
    monkeypatch.setattr(utils, "Label", FakeLabel)
    monkeypatch.setattr(utils, "Button", FakeButton)
    monkeypatch.setattr(utils, "Popup", FakePopup)
    monkeypatch.setattr(utils, "Window", FakeWindow(keyboard))

    popup = utils.show_confirmation_dialog(
        "Confirm",
        "Proceed?",
        on_confirm=lambda: confirmed.__setitem__("value", True),
        on_cancel=lambda: cancelled.__setitem__("value", True),
    )

    popup.cancel_action()

    assert confirmed["value"] is False
    assert cancelled["value"] is True
    assert popup.dismissed is True
    assert "on_key_down" not in keyboard._bindings
