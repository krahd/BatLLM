import os
import tempfile
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import StringProperty
from util.paths import prompt_asset_dir

# Load the KV file in the same folder
Builder.load_file(os.path.join(os.path.dirname(__file__), "save_dialog.kv"))

class SaveDialog(Popup):
    """
    A Popup to choose a folder, enter a filename, and save `content_to_save` as a .txt file.
    
    You can control the initial folder via `start_folder`.
    """
    content_to_save = StringProperty('')
    start_folder    = StringProperty(str(prompt_asset_dir()))

    def __init__(self, *, content_to_save: str, start_folder: str = None, **kwargs):
        super().__init__(**kwargs)
        self.content_to_save = content_to_save
        if start_folder:
            fallback = str(prompt_asset_dir())
            self.start_folder = start_folder if os.path.isdir(start_folder) else fallback

    def _save(self):
        folder = self.ids.filechooser.path
        fn     = self.ids.filename.text.strip()
        if not fn:
            return  # optionally pop a warning

        if not fn.lower().endswith('.txt'):
            fn += '.txt'
        full_path = os.path.join(folder, fn)

        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(prefix=".batllm-prompt-", suffix=".tmp", dir=folder)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(self.content_to_save)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, full_path)
        except Exception as e:
            if temporary:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
            Popup(
                title="Prompt save failed",
                content=Label(text=str(e)),
                size_hint=(None, None),
                size=(520, 240),
            ).open()
        else:
            self.dismiss()
