import os
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.core.window import Window

# Load the KV definition (assumes load_text_dialog.kv is alongside this file)
Builder.load_file(os.path.join(os.path.dirname(__file__), "load_text_dialog.kv"))

class LoadTextDialog(Popup):
    """
    A modal, two-pane dialog to choose and preview .txt files.
    When the user loads or cancels, `on_choice` is called with the file's
    text (str) or None.
    """

    on_choice = ObjectProperty(lambda choice: None)

    def __init__(self, on_choice, start_dir: str = None, **kwargs):
        super().__init__(**kwargs)
        self.on_choice = on_choice
        self._keyboard = None

        # Attach/detach keyboard events for Enter/Esc
        self.bind(on_open=self._attach_keyboard, on_dismiss=self._detach_keyboard)

        # If a start_dir is provided and exists, set it when the popup opens
        if start_dir and os.path.isdir(start_dir):
            self.bind(on_open=lambda *a: setattr(self.ids.filechooser, "path", start_dir))

    def _attach_keyboard(self, *args):
        """Request keyboard to capture Enter/Esc when dialog is open."""
        self._keyboard = Window.request_keyboard(self._on_keyboard_closed, self)
        if self._keyboard:
            self._keyboard.bind(on_key_down=self._on_key_down)

    def _detach_keyboard(self, *args):
        """Release keyboard when dialog closes."""
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_key_down)
            self._keyboard = None

    def _on_keyboard_closed(self):
        self._keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key in ("enter", "numpadenter"):
            self._load_selected()
            return True
        if key == "escape":
            self._cancel()
            return True
        return False

    def _on_file_select(self, selection):
        """
        Called when the FileChooser selection changes.
        Loads and shows the text of a `.txt` file in the preview pane.
        """
        if not selection:
            self.ids.preview.text = ""
            return
        path = selection[0]
        if not path.lower().endswith(".txt"):
            self.ids.preview.text = ""
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.ids.preview.text = f.read()
        except Exception:
            self.ids.preview.text = ""

    def _load_selected(self):
        """
        User confirmed loading the selected file.
        Reads the file, calls the callback, and closes the dialog.
        """
        sel = self.ids.filechooser.selection
        if not sel:
            return

        path = sel[0]
        print(f"XXX Loading file: {path}")
        if not path.lower().endswith(".txt"):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

        except Exception:
            content = ""

        # Invoke the callback, then close
        try:
            self.on_choice(content)
        finally:
            self.dismiss()

    def _cancel(self):
        """
        User cancelled. Calls callback with None and closes.
        """
        try:
            self.on_choice(None)
        finally:
            self.dismiss()

    def on_touch_down(self, touch):
        """
        Detect a double‐tap on the preview pane as a quick 'load'.
        """
        preview = self.ids.preview
        if preview.collide_point(*touch.pos) and touch.is_double_tap:
            if preview.text:
                self._load_selected()
                return True
        return super().on_touch_down(touch)
