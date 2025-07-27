from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
import os

class FileDialogPopup(Popup):
    filechooser = ObjectProperty(None)
    preview = ObjectProperty(None)
    on_file_selected = ObjectProperty(None)
    history = []

    def __init__(self, on_file_selected, **kwargs):
        super().__init__(**kwargs)
        self.on_file_selected = on_file_selected
        self._bind_keyboard()

    def _bind_keyboard(self):
        Window.bind(on_key_down=self._on_key_down)

    def _unbind_keyboard(self):
        Window.unbind(on_key_down=self._on_key_down)

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        if key == 27:
            self.dismiss()
            return True
        return False

    def dismiss(self, *args, **kwargs):
        self._unbind_keyboard()
        super().dismiss(*args, **kwargs)

    def go_to_parent(self):
        parent = os.path.dirname(self.filechooser.path)
        if parent:
            self.history.append(self.filechooser.path)
            self.filechooser.path = parent

    def go_back(self):
        if self.history:
            last_path = self.history.pop()
            self.filechooser.path = last_path

    def update_preview(self, selection):
        if selection:
            path = selection[0]
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                text = f"[Error reading file: {e}]"
        else:
            text = ""
        self.preview.text = text

    def load_file(self):
        selection = self.filechooser.selection
        if selection:
            self.on_file_selected(selection[0])
            self.dismiss()

    def preview_double_tap(self, instance, touch):
        if instance.collide_point(*touch.pos) and touch.is_double_tap:
            self.load_file()


        