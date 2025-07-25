from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


def show_confirmation_dialog(title, message, on_confirm, on_cancel = None):
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




def show_filename_dialog(on_confirm, on_cancel=None, title="Save As", default_filename="session.json"):
    layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

    input_field = TextInput(hint_text="Enter filename", multiline = False)
    input_field.text = default_filename
    layout.add_widget(Label(text="Please enter a filename:"))
    layout.add_widget(input_field)

    btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
    btn_ok = Button(text="Save")
    btn_cancel = Button(text="Cancel")

    popup = Popup(title=title, content=layout, size_hint=(None, None), size=(800, 400), auto_dismiss=False)

    def confirm_action(*args):
        filename = input_field.text.strip()
        if filename:
            popup.dismiss()
            on_confirm(filename)

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