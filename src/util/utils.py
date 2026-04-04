"""General use utilities for BatLLM"""

from colorsys import rgb_to_hls, hls_to_rgb
from typing import Optional
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from configs.app_config import config


def _maybe_int(v):
    try:
        return None if v in (None, "") else int(v)
    except (TypeError, ValueError):
        return None

def _maybe_float(v):
    try:
        return None if v in (None, "") else float(v)
    except (TypeError, ValueError):
        return None



def find_id_in_parents(searcher, target_id):
    """
    Searches recursively for an element among the ancestors of a Kivy element by its id

    Args:
        searcher (_type_): the object that starts the search, usually a Kivy widget.
        target_id (_type_): the object's id to find.

    Returns:
        _type_: the found object or None
    """

    parent = searcher.parent
    while parent:
        if hasattr(parent, "ids") and target_id in parent.ids:
            return parent.ids[target_id]
        parent = parent.parent
    return None


def tame_color(color, desaturation=0.0, lighten=0.0):
    """
    Desaturates and lightens an RGB colour.

    Args:
        color (tuple): A 3-tuple representing an RGB colour in range 0–1, e.g., (0.5, 0.2, 0.8)
        desaturation (float): 0 = no change, 1 = fully desaturated (greyscale)
        lighten (float): 0 = no change, 1 = fully white

    Returns:
        tuple: Modified RGB tuple in range 0–1
    """
    r, g, b = color
    h, l, s = rgb_to_hls(r, g, b)

    s = s * (1 - desaturation)
    l = l + (1 - l) * lighten  # shift l toward 1 (white)

    r_out, g_out, b_out = hls_to_rgb(h, l, s)
    return (r_out, g_out, b_out)


def switch_screen(manager, target: str, direction: Optional[str] = None):
    """
    Navigates to another screen and optionally sets the transition direction first.

    Args:
        manager: ScreenManager-like object controlling the current screen.
        target (str): Target screen name.
        direction (Optional[str]): Transition direction such as "left" or "right".
    """

    if direction:
        transition = getattr(manager, "transition", None)
        if transition is not None and hasattr(transition, "direction"):
            transition.direction = direction

    manager.current = target


# ------ Dialogs ------------------------------------------


def show_confirmation_dialog(title, message, on_confirm, on_cancel=None):
    """
    Displays a modal confirmation pop-up with a title and message.

    Args:
        title (_type_): the title of the pop-up
        message (_type_): the message to display in the pop-up
        on_confirm (_type_): function to call when the user confirms
        on_cancel (_type_, optional): function to call when the user cancels. Defaults to None.
    """

    content = BoxLayout(orientation="vertical", spacing=10, padding=10)

    label = Label(text=message, halign="center")
    content.add_widget(label)

    button_box = BoxLayout(size_hint_y=0.5, spacing=10)

    yes_button = Button(text="Yes")
    no_button = Button(text="No")

    button_box.add_widget(yes_button)
    button_box.add_widget(no_button)

    content.add_widget(button_box)

    w = 400 + 20 * max(len(line) for line in message.splitlines())
    h = 400 + 20 * len(message.splitlines())
    keyboard = {"instance": None}
    completed = {"value": False}

    def finish(callback=None):
        if completed["value"]:
            return

        completed["value"] = True
        popup.dismiss()
        if callback:
            callback()

    def confirm(*args):
        finish(on_confirm)

    def cancel(*args):
        finish(on_cancel)

    def on_keyboard_closed():
        keyboard["instance"] = None

    def on_key_down(_keyboard, keycode, _text, _modifiers):
        key = keycode[1]
        if key in ("enter", "numpadenter"):
            confirm()
            return True
        if key == "escape":
            cancel()
            return True
        return False

    def attach_keyboard(*_args):
        keyboard["instance"] = Window.request_keyboard(on_keyboard_closed, popup)
        if keyboard["instance"]:
            keyboard["instance"].bind(on_key_down=on_key_down)

    def detach_keyboard(*_args):
        if keyboard["instance"]:
            keyboard["instance"].unbind(on_key_down=on_key_down)
            keyboard["instance"] = None

    popup = Popup(
        title=title,
        content=content,
        size_hint=(None, None),
        size=(w, h),
        auto_dismiss=False,
    )

    yes_button.bind(on_release=confirm)
    no_button.bind(on_release=cancel)
    popup.bind(on_open=attach_keyboard, on_dismiss=detach_keyboard)
    popup.confirm_action = confirm
    popup.cancel_action = cancel

    popup.open()
    return popup


def show_fading_alert(title, message, duration=1.5, fade_duration=2.0):
    """
    Displays a modal alert pop-up with a title and message that fades out and closes itself.

    Args:
        title (_type_): the title of the alert
        message (_type_): the message to display in the alert
        duration (float, optional): How long does it take for the alert to start fading out. Defaults to 1.0.
        fade_duration (float, optional): How long does the fade out process take. Defaults to 1.0.
    """
    content = BoxLayout(orientation="vertical", spacing=10, padding=10)

    label = Label(text=message, halign="center")
    content.add_widget(label)

    w = 400 + 20 * max(len(line) for line in message.splitlines())
    h = 400 + 20 * len(message.splitlines())

    popup = Popup(
        title=title, content=content, size_hint=(None, None), size=(w, h), opacity=1
    )

    def fade_and_close(*args):
        anim = Animation(opacity=0, duration=fade_duration)
        anim.bind(on_complete=lambda *a: popup.dismiss())
        anim.start(popup)

    popup.open()
    # TODO check if duration means what it should
    Clock.schedule_once(fade_and_close, duration)


def show_text_input_dialog(
    on_confirm,
    on_cancel=None,
    title="",
    message="",
    default_text="",
    input_hint="Enter a text",
    confirm_text="Save",
    cancel_text="Cancel",
):
    """
    A modal pop-up for the user to enter text input.

    Args:
        on_confirm (_type_): function to call when the user confirms the filename
        on_cancel (_type_, optional): function to call when the user cancels. Defaults to None.
        title (str, optional): title of the pop-up. Defaults to "".
        default_text (str, optional): default (pre-set) value for the text field). Defaults to "".
        input_hint (str, optional): hint text for the input field. Defaults to "Enter a text". 
        It is only visible if the default value is empty
        confirm_text (str, optional): label for the confirm button. Defaults to "Save".
        cancel_text (str, optional): label for the cancel button. Defaults to "Cancel".
    """

    layout = BoxLayout(orientation="vertical", spacing=25, padding=10)

    input_field = TextInput(hint_text=input_hint, multiline=False, height=50)
    input_field.font_size = 40
    input_field.text = default_text

    message_label = Label(
        text=message,
        size_hint_y=None,
        height=120,
        font_size=40,
        halign="center",
        valign="middle",
    )

    layout.add_widget(message_label)
    layout.add_widget(input_field)

    btn_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
    btn_ok = Button(text=confirm_text)
    btn_cancel = Button(text=cancel_text)

    keyboard = {"instance": None}

    popup = Popup(
        title=title,
        content=layout,
        size_hint=(None, None),
        size=(800, 600),
        auto_dismiss=False,
    )

    def confirm_action(*args):
        value = input_field.text.strip()
        if value:
            popup.dismiss()
            on_confirm(value)

    def cancel_action(*args):
        popup.dismiss()
        if on_cancel:
            on_cancel()

    def on_keyboard_closed():
        keyboard["instance"] = None

    def on_key_down(_keyboard, keycode, _text, _modifiers):
        key = keycode[1]
        if key in ("enter", "numpadenter"):
            confirm_action()
            return True
        if key == "escape":
            cancel_action()
            return True
        return False

    def attach_keyboard(*_args):
        keyboard["instance"] = Window.request_keyboard(on_keyboard_closed, popup)
        if keyboard["instance"]:
            keyboard["instance"].bind(on_key_down=on_key_down)

    def detach_keyboard(*_args):
        if keyboard["instance"]:
            keyboard["instance"].unbind(on_key_down=on_key_down)
            keyboard["instance"] = None

    btn_ok.bind(on_release=confirm_action)
    btn_cancel.bind(on_release=cancel_action)
    btn_layout.add_widget(btn_ok)
    btn_layout.add_widget(btn_cancel)

    layout.add_widget(btn_layout)
    popup.bind(on_open=attach_keyboard, on_dismiss=detach_keyboard)
    popup.open()



def markup(text: str, font_size: Optional[int] = None, color="#000000", bold=False, italic=False) -> str:
    """
    Wraps the given text in Kivy markup tags for font size, colour, bold, and italic.

    Args:
        text (str): The text to be wrapped.
        font_size (int, optional): The font size to apply. Defaults to config value "ui"/"font_size".
        color (str, optional): The colour to apply in hex format (e.g., "#ff0000"). Defaults to black ("#000000").
        bold (bool, optional): Whether to apply bold formatting. Defaults to False.
        italic (bool, optional): Whether to apply italic formatting. Defaults to False.

    Returns:
        str: The text wrapped in Kivy markup tags.
    """
    if font_size is None:
        font_size = config.get("ui", "font_size")  # evaluated per call

    if not text:
        return ""

    if font_size <= 0 or not isinstance(font_size, int):
        font_size = config.get("ui", "font_size")
    else:
        font_size = 18

    if not color.startswith("#") or len(color) != 7:
        color = "#000000"  # default to black if invalid


    return f"[size={font_size}sp][color={color}]{'[b]' if bold else ''}{'[i]' if italic else ''}{text}{'[/i]' if italic else ''}{'[/b]' if bold else ''}[/color][/size]"
