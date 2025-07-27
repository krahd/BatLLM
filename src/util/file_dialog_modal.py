
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

# KV Layout embedded directly in Python source
Builder.load_string("""
<FileDialogPopup>:
    BoxLayout:
        orientation: 'horizontal'
        padding: 10
        spacing: 10

        BoxLayout:
            orientation: 'vertical'
            size_hint_x: None
            width: min(self.parent.width * 0.4, 400)
            spacing: 5

            BoxLayout:
                size_hint_y: None
                height: '40dp'
                spacing: 5
                Button:
                    text: 'Parent'
                    on_release: root.go_to_parent()
                Button:
                    text: 'Back'
                    on_release: root.go_back()

            FileChooserListView:
                id: filechooser
                filters: ['*.txt']
                on_selection: root.update_preview(self.selection)
                on_submit: root.load_file()
                multiselect: False
                root.filechooser: self

            BoxLayout:
                size_hint_y: None
                height: '40dp'
                spacing: 5
                Button:
                    text: 'Cancel'
                    on_release: root.dismiss()
                Button:
                    text: 'Load'
                    on_release: root.load_file()

        ScrollView:
            bar_width: '10dp'
            do_scroll_x: False
            on_touch_down: root.preview_double_tap(*args)
            TextInput:
                id: preview
                readonly: True
                font_size: '14sp'
                background_color: 1,1,1,1
                foreground_color: 0,0,0,1
                text: ''
                size_hint_y: None
                height: self.minimum_height
                multiline: True
                word_wrap: True
                cursor_width: 0
                root.preview: self
""")

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

class FileDialogApp(App):
    def build(self):
        def handle_file(path):
            print(f"Selected file: {path}")
        dialog = FileDialogPopup(title="Open Text File", size_hint=(0.9, 0.9),
                                 auto_dismiss=False, on_file_selected=handle_file)
        dialog.open()
        return Label(text="Main App Window")

if __name__ == '__main__':
    FileDialogApp().run()
