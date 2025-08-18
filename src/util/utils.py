from colorsys import rgb_to_hls, hls_to_rgb
from typing import Optional
from kivy.animation import Animation
from kivy.clock import Clock
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
        color (tuple): A 3-tuple of RGB in range 0–1, e.g., (0.5, 0.2, 0.8)
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


# ------ Dialogs ------------------------------------------


def show_confirmation_dialog(title, message, on_confirm, on_cancel=None):
    """
    Displays a modal confirmation dialog with a title and message.

    Args:
        title (_type_): the title of the dialog
        message (_type_): the message to display in the dialog
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

    def confirm(*args):
        print("dos ")
        if on_confirm:
            print("tres")
            on_confirm()
        popup.dismiss()

    def cancel(*args):
        if on_cancel:
            on_cancel()
        popup.dismiss()

    popup = Popup(
        title=title,
        content=content,
        size_hint=(None, None),
        size=(w, h),
        auto_dismiss=False,
    )

    yes_button.bind(on_release=confirm)
    no_button.bind(on_release=cancel)

    popup.open()


def show_fading_alert(title, message, duration=1.5, fade_duration=2.0):
    """
    Displays a modal alert with a title and message that fades out and closes itself.

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
    Clock.schedule_once(fade_and_close, duration)


def show_text_input_dialog(
    on_confirm,
    on_cancel=None,
    title="",
    message="",
    default_text="",
    input_hint="Enter a text",
):
    """
    A modal dialog for the user to enter a text input.

    Args:
        on_confirm (_type_): function to call when the user confirms the filename
        on_cancel (_type_, optional): function to call when the user cancels. Defaults to None.
        title (str, optional): title of the dialog. Defaults to "".
        default_text (str, optional): default (pre-set) value for the text field). Defaults to "".
        input_hint (str, optional): hint text for the input field. Defaults to "Enter a text". It is only visible if the default value is empty
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
    btn_ok = Button(text="Save")
    btn_cancel = Button(text="Cancel")

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

    btn_ok.bind(on_release=confirm_action)
    btn_cancel.bind(on_release=cancel_action)
    btn_layout.add_widget(btn_ok)
    btn_layout.add_widget(btn_cancel)

    layout.add_widget(btn_layout)
    popup.open()



def markup(text: str, font_size: Optional[int] = None, color="#000000", bold=False, italic=False) -> str:
    """
    Wraps the given text in Kivy markup tags for font size, color, bold, and italic.

    Args:
        text (str): The text to be wrapped.
        font_size (int, optional): The font size to apply. Defaults to config value "ui"/"font_size".
        color (str, optional): The color to apply in hex format (e.g., "#ff0000"). Defaults to black ("#000000").
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
