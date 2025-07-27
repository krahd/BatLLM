from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
from colorsys import rgb_to_hls, hls_to_rgb


def show_confirmation_dialog(title, message, on_confirm, on_cancel = None):
    """
    Displays a modal confirmation dialog with a title and message.

    Args:
        title (_type_): the title of the dialog
        message (_type_): the message to display in the dialog
        on_confirm (_type_): function to call when the user confirms
        on_cancel (_type_, optional): function to call when the user cancels. Defaults to None.    
    """    
    content = BoxLayout(orientation='vertical', spacing=10, padding=10)

    label = Label(text=message, halign='center')
    content.add_widget(label)

    button_box = BoxLayout(size_hint_y=0.5, spacing=10)
   
    yes_button = Button(text='Yes')
    no_button = Button(text='No')

    button_box.add_widget(yes_button)
    button_box.add_widget(no_button)

    content.add_widget(button_box)

    w = 400 + 20 * max(len(line) for line in message.splitlines())
    h = 400 + 20 * len(message.splitlines())
    
    popup = Popup(title=title, content=content,
                  size_hint=(None, None), size=(w, h),
                  auto_dismiss=False)

    def confirm(*args):
        if on_confirm:
            on_confirm()
        popup.dismiss()

    def cancel(*args):
        if on_cancel:
            on_cancel()
        popup.dismiss()

    yes_button.bind(on_release=confirm)
    no_button.bind(on_release=cancel)

    popup.open()



def show_fading_alert(title, message, duration=1.0, fade_duration=1.0):
    """
    Displays a modal alert with a title and message that fades out and closes itsel.

    Args:
        title (_type_): the title of the alert
        message (_type_): the message to display in the alert
        duration (float, optional): How long does it take for the alert to start fading out. Defaults to 1.0.
        fade_duration (float, optional): How long does the fade out process take. Defaults to 1.0.
    """    
    content = BoxLayout(orientation='vertical', spacing=10, padding=10)
    
    label = Label(text=message, halign='center')
    content.add_widget(label)

    w = 400 + 20 * max(len(line) for line in message.splitlines())
    h = 400 + 20 * len(message.splitlines())
    
    popup = Popup(title=title, content=content,
                  size_hint=(None, None), size=(w, h),
                  opacity=1)

    def fade_and_close(*args):
        anim = Animation(opacity=0, duration=fade_duration)
        anim.bind(on_complete=lambda *a: popup.dismiss())
        anim.start(popup)
   
    popup.open()
    Clock.schedule_once(fade_and_close, duration)



def show_text_input_dialog(on_confirm, on_cancel=None, title="", default_text="", input_hint="Enter a text"):
    """
    A modal dialog for the user to enter a text input.
    
    Args:
        on_confirm (_type_): function to call when the user confirms the filename
        on_cancel (_type_, optional): function to call when the user cancels. Defaults to None.
        title (str, optional): title of the dialog. Defaults to "".
        default_text (str, optional): default (pre-set) value for the text field). Defaults to "".
        input_hint (str, optional): hint text for the input field. Defaults to "Enter a text". It is only visible if the default value is empty
    """    
    
    layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

    input_field = TextInput(hint_text=input_hint, multiline = False) # 
    input_field.text = default_text
    input_field.font_size = 40
    layout.add_widget(Label(text="Please enter a filename:"))
    layout.add_widget(input_field)

    btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
    btn_ok = Button(text="Save")
    btn_cancel = Button(text="Cancel")

    popup = Popup(title=title, content=layout, size_hint=(None, None), size=(800, 400), auto_dismiss=False)

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
        if hasattr(parent, 'ids') and target_id in parent.ids:
            return parent.ids[target_id]
        parent = parent.parent
    return None




def tame_color(color, desaturation=0.0, lighten=0.0):
    """
    Desaturates and lightens an RGB color.

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