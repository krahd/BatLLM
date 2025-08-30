"""BatLLM Configuration GUI (Kivy) – Enhanced Usability Version.

Improvements:
  - Larger, consistent fonts & spacing.
  - Added llm.url and llm.port to editable core fields.
  - Graceful handling when Ollama is not running (no crashes; status + popup).
  - Central connection test button + live status.
  - Scrollable Raw YAML & Snapshot preview.
  - Connection auto‑refresh after saving LLM settings.
  - Unified error capture (no free variable lambda issues).
  - Friendlier instructions banner.
"""

from __future__ import annotations
import os
import re
import json
import shutil
import threading
from typing import Any, Dict, List, Optional

import requests
import yaml

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

# -------- Appearance constants --------
FONT_BASE = 38
FONT_SMALL = 32
ROW_HEIGHT = 70
PAD = 40
Window.minimum_width = 1150
Window.minimum_height = 760

# -------- Helper popups --------
def info_popup(title: str, msg: str):
    Popup(title=title, content=Label(text=msg, font_size=FONT_BASE),
          size_hint=(0.55, 0.55)).open()

def ensure_dir(p: str): os.makedirs(p, exist_ok=True)

def safe_float(v: str) -> Optional[float]:
    v = v.strip()
    if not v or v.lower() == "none":
        return None
    try:
        return float(v)
    except:
        return None

def safe_int(v: str) -> Optional[int]:
    v = v.strip()
    if not v or v.lower() == "none":
        return None
    try:
        return int(v)
    except:
        return None

def safe_any(v: str) -> Optional[Any]:
    v = v.strip()
    if not v or v.lower() == "none":
        return None
    try:
        return json.loads(v)
    except:
        return v

# -------- Config Manager --------
SNAPSHOT_HTML_TMPL = (
    "<!doctype html><html><head><meta charset='utf-8'><title>BatLLM Config Snapshot: {name}</title>"
    "</head><body><h1>BatLLM Config Snapshot: {name}</h1><hr>"
    "<!-- CONFIG_SNAPSHOT_START --><pre>{yaml_text}</pre><!-- CONFIG_SNAPSHOT_END -->"
    "</body></html>"
)

class ConfigManager:
    def __init__(self, path: str):
        self.path = path
        self.backup_path = os.path.join(os.path.dirname(path), 'config.yaml.bak')
    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            raise FileNotFoundError(self.path)
        with open(self.path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    def save(self, data: Dict[str, Any]):
        with open(self.path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, sort_keys=False)
    def backup(self):
        if os.path.exists(self.path):
            shutil.copy2(self.path, self.backup_path)
    def undo(self):
        if not os.path.exists(self.backup_path):
            raise FileNotFoundError('No backup to restore')
        shutil.copy2(self.backup_path, self.path)
    def save_snapshot_html(self, name: str, data: Dict[str, Any], directory: str) -> str:
        ensure_dir(directory)
        out = os.path.join(directory, f'config_{name}.html')
        with open(out, 'w', encoding='utf-8') as f:
            f.write(SNAPSHOT_HTML_TMPL.format(name=name,
                                              yaml_text=yaml.safe_dump(data, sort_keys=False)))
        return out
    def list_snapshots(self, directory: str) -> List[str]:
        if not os.path.isdir(directory):
            return []
        return sorted([fn for fn in os.listdir(directory) if re.match(r'config_.+\.html$', fn)])
    def load_snapshot_yaml_from_html(self, path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        m = re.search(r'<!-- CONFIG_SNAPSHOT_START -->\s*<pre>(.*?)</pre>\s*<!-- CONFIG_SNAPSHOT_END -->',
                      html, flags=re.DOTALL) or re.search(r'<pre>(.*?)</pre>', html, flags=re.DOTALL)
        if not m:
            raise ValueError('No snapshot YAML in file')
        return yaml.safe_load(m.group(1)) or {}
    def activate_snapshot(self, path: str):
        data = self.load_snapshot_yaml_from_html(path)
        self.backup()
        self.save(data)

# -------- Ollama Client --------
class OllamaClient:
    def __init__(self, base_url: str = 'http://localhost', port: int = 11434, timeout: float = 10.0):
        self.base_url = base_url.rstrip('/')
        self.port = port
        self.timeout = timeout
    def _u(self, path: str) -> str: return f"{self.base_url}:{self.port}{path}"
    def list_local_models(self) -> List[Dict[str, Any]]:
        r = requests.get(self._u('/api/tags'), timeout=self.timeout)
        r.raise_for_status()
        return r.json().get('models', [])
    def run_once(self, model: str, prompt: str = 'test', num_predict: Optional[int] = 8) -> str:
        payload = {'model': model, 'prompt': prompt}
        if num_predict is not None:
            payload['options'] = {'num_predict': num_predict}
        r = requests.post(self._u('/api/generate'), json=payload, timeout=self.timeout, stream=True)
        r.raise_for_status()
        out = ''
        for line in r.iter_lines():
            if not line:
                continue
            obj = json.loads(line.decode('utf-8'))
            out += obj.get('response', '')
            if obj.get('done'):
                break
        return out
    def stop(self, model: Optional[str] = None) -> Dict[str, Any]:
        payload = {'model': model} if model else {}
        r = requests.post(self._u('/api/stop'), json=payload, timeout=self.timeout)
        if r.status_code >= 400:
            return {'error': f'stop failed {r.status_code}', 'text': r.text}
        return r.json() if r.text else {'ok': True}
    def delete_model(self, name: str) -> Dict[str, Any]:
        r = requests.delete(self._u('/api/delete'), json={'name': name}, timeout=self.timeout)
        if r.status_code >= 400:
            return {'error': f'delete failed {r.status_code}', 'text': r.text}
        return r.json() if r.text else {'ok': True}
    def pull_model(self, name: str, stream_callback=None) -> Dict[str, Any]:
        r = requests.post(self._u('/api/pull'),
                          json={'name': name}, timeout=self.timeout, stream=True)
        r.raise_for_status()
        last = {}
        for line in r.iter_lines():
            if not line:
                continue
            obj = json.loads(line.decode('utf-8'))
            last = obj
            if stream_callback:
                stream_callback(obj)
        return last
    @staticmethod
    def list_remote_models() -> List[Dict[str, Any]]:
        r = requests.get('https://ollamadb.dev/api/v1/models', timeout=12)
        r.raise_for_status()
        data = r.json()
        return data.get('data', []) if isinstance(data, dict) else []

# -------- UI Panels --------
# Added url & port to core LLM fields
LLM_FIELDS = [
    ('url', str), ('port', int),
    ('model', str), ('temperature', float), ('top_p', float), ('top_k', int),
    ('timeout', float), ('max_tokens', int), ('stop', Any), ('seed', int),
    ('num_thread', int), ('num_ctx', int), ('num_predict', int),
]

class OtherSettingsPanel(ScrollView):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bar_width = 12
        self.grid = GridLayout(cols=2, size_hint_y=None, padding=6, spacing=6)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.add_widget(self.grid)
        self.inputs: Dict[str, TextInput] = {}
    def load_from_config(self, cfg: Dict[str, Any]):
        self.grid.clear_widgets()
        self.inputs.clear()
        core = {k for k, _ in LLM_FIELDS}
        llm = cfg.get('llm', {}) if isinstance(cfg.get('llm'), dict) else {}
        flat: Dict[str, Any] = {}
        for sec, val in cfg.items():
            if sec == 'llm':
                continue
            if isinstance(val, dict):
                for k, v in val.items():
                    flat[f'{sec}.{k}'] = v
            else:
                flat[sec] = val
        for k, v in llm.items():
            if k not in core:
                flat[f'llm.{k}'] = v
        for key in sorted(flat):
            self.grid.add_widget(Label(text=key, size_hint_y=None, height=30, font_size=FONT_SMALL))
            v = flat[key]
            txt = json.dumps(v) if isinstance(v, (dict, list)) else ('' if v is None else str(v))
            ti = TextInput(text=txt, multiline=False, size_hint_y=None,
                           height=30, font_size=FONT_SMALL)
            self.inputs[key] = ti
            self.grid.add_widget(ti)
    def apply_to_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        for full, ti in self.inputs.items():
            raw = ti.text.strip()
            if '.' in full:
                sec, key = full.split('.', 1)
                if sec == 'llm' and key in {k for k, _ in LLM_FIELDS}:
                    continue
                sec_dict = cfg.get(sec, {}) if isinstance(cfg.get(sec), dict) else {}
                if raw.lower() in ('', 'none'):
                    val = None
                else:
                    try:
                        val = json.loads(raw)
                    except:
                        if re.fullmatch(r'-?\d+', raw):
                            val = int(raw)
                        else:
                            try:
                                val = float(raw)
                            except:
                                val = raw
                sec_dict[key] = val
                cfg[sec] = sec_dict
            else:
                cfg[full] = raw
        return cfg

class LLMPanel(ScrollView):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bar_width = 12
        self.grid = GridLayout(cols=2, size_hint_y=None, padding=10, spacing=8)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.add_widget(self.grid)
        self.inputs: Dict[str, TextInput] = {}
        title = Label(text='Core LLM Parameters', size_hint_y=None, height=36,
                      font_size=FONT_BASE + 2, bold=True)
        self.grid.add_widget(title)
        self.grid.add_widget(Label(text=''))
        for k, _ in LLM_FIELDS:
            self.grid.add_widget(Label(text=k, size_hint_y=None, height=34, font_size=FONT_SMALL))
            ti = TextInput(text='', multiline=False, size_hint_y=None,
                           height=34, font_size=FONT_SMALL)
            self.inputs[k] = ti
            self.grid.add_widget(ti)
    def load_from_config(self, cfg: Dict[str, Any]):
        llm = cfg.get('llm', {}) if isinstance(cfg.get('llm'), dict) else {}
        for k, _ in LLM_FIELDS:
            v = llm.get(k)
            self.inputs[k].text = '' if v is None else (
                json.dumps(v) if isinstance(v, (dict, list)) else str(v))
    def write_to_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        llm = cfg.get('llm', {}) if isinstance(cfg.get('llm'), dict) else {}
        for k, t in LLM_FIELDS:
            raw = self.inputs[k].text
            if t is float:
                llm[k] = safe_float(raw)
            elif t is int:
                llm[k] = safe_int(raw)
            elif t is Any:
                llm[k] = safe_any(raw)
            else:
                llm[k] = raw.strip() or None
        cfg['llm'] = llm
        return cfg

class RawYAMLPanel(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        wrapper = ScrollView(size_hint=(1, 1), bar_width=12)
        self.editor = TextInput(text='', multiline=True, font_size=FONT_SMALL)
        wrapper.add_widget(self.editor)
        self.add_widget(wrapper)
    def load_from_config(self, cfg: Dict[str, Any]):
        self.editor.text = yaml.safe_dump(cfg, sort_keys=False)
    def read_yaml(self) -> Dict[str, Any]:
        return yaml.safe_load(self.editor.text) or {}

class SnapshotPanel(BoxLayout):
    def __init__(self, list_fn, activate_fn, save_fn, undo_fn, get_directory_fn, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.list_fn = list_fn
        self.activate_fn = activate_fn
        self.save_fn = save_fn
        self.undo_fn = undo_fn
        self.get_directory_fn = get_directory_fn
        r1 = BoxLayout(size_hint_y=None, height=ROW_HEIGHT - 4, spacing=6)
        self.snap_name = TextInput(hint_text='snapshot name', multiline=False, font_size=FONT_SMALL)
        r1.add_widget(self.snap_name)
        sb = Button(text='Save', size_hint_x=None, width=110, font_size=FONT_SMALL)
        sb.bind(on_release=lambda *_: self.save())
        r1.add_widget(sb)
        self.add_widget(r1)
        r2 = BoxLayout(size_hint_y=None, height=ROW_HEIGHT - 4, spacing=6)
        self.spinner = Spinner(text='(select)', values=[], size_hint_x=0.45, font_size=FONT_SMALL)
        r2.add_widget(self.spinner)
        for label, cb in [('Refresh', self.refresh), ('Activate', self.activate), ('Undo', self.undo)]:
            b = Button(text=label, size_hint_x=None, width=110, font_size=FONT_SMALL)
            b.bind(on_release=lambda *_, _cb=cb: _cb())
            r2.add_widget(b)
        self.add_widget(r2)
        pv_wrap = ScrollView(size_hint=(1, 1), bar_width=12)
        self.preview = TextInput(text='', readonly=True, font_size=FONT_SMALL)
        pv_wrap.add_widget(self.preview)
        self.add_widget(pv_wrap)
    def refresh(self):
        try:
            vals = self.list_fn()
            self.spinner.values = vals
            self.spinner.text = vals[0] if vals else '(select)'
            if vals:
                p = os.path.join(self.get_directory_fn(), self.spinner.text)
                try:
                    self.preview.text = open(p, 'r', encoding='utf-8').read()
                except Exception as e:
                    self.preview.text = f'(preview error: {e})'
        except Exception as e:
            info_popup('Error', f'Snapshot list failed: {e}')
    def activate(self):
        n = self.spinner.text
        if not n or n.startswith('('):
            return info_popup('Activate', 'Choose snapshot')
        try:
            self.activate_fn(os.path.join(self.get_directory_fn(), n))
            info_popup('Activated', n)
        except Exception as e:
            info_popup('Error', str(e))
    def save(self):
        n = self.snap_name.text.strip()
        if not n:
            return info_popup('Save', 'Enter name')
        try:
            out = self.save_fn(n)
            info_popup('Saved', out)
            self.refresh()
        except Exception as e:
            info_popup('Error', str(e))
    def undo(self):
        try:
            self.undo_fn()
            info_popup('Undo', 'Backup restored')
        except Exception as e:
            info_popup('Error', str(e))

class LocalModelsPanel(BoxLayout):
    def __init__(self, list_fn, run_fn, stop_fn, delete_fn, set_model_fn, set_and_snapshot_fn, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.list_fn = list_fn
        self.run_fn = run_fn
        self.stop_fn = stop_fn
        self.delete_fn = delete_fn
        self.set_model_fn = set_model_fn
        self.set_and_snapshot_fn = set_and_snapshot_fn
        row = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=6)
        self.spinner = Spinner(text='(refresh)', values=[], size_hint_x=0.35, font_size=FONT_SMALL)
        row.add_widget(self.spinner)
        for label, cb in [('Refresh', self.refresh), ('Run', self.run), ('Stop', self.stop),
                          ('Delete', self.delete), ('Set', self.set_model), ('Set+Snap', self.set_model_snapshot)]:
            b = Button(text=label, size_hint_x=None, width=100, font_size=FONT_SMALL)
            b.bind(on_release=lambda *_, _cb=cb: _cb())
            row.add_widget(b)
        self.add_widget(row)
        out_wrap = ScrollView(size_hint=(1, 1), bar_width=12)
        self.output = TextInput(text='', readonly=True, font_size=FONT_SMALL)
        out_wrap.add_widget(self.output)
        self.add_widget(out_wrap)
    def refresh(self):
        def work():
            try:
                models = self.list_fn()
                names = [m.get('name', '') for m in models if m.get('name')]
                Clock.schedule_once(lambda *_: self._update(names))
            except Exception as e:
                msg = f'List failed: {e}'
                Clock.schedule_once(lambda *_: info_popup('Error', msg))
        threading.Thread(target=work, daemon=True).start()
    def _update(self, names):
        self.spinner.values = names
        self.spinner.text = names[0] if names else '(refresh)'
        self.output.text = f'Found {len(names)} local models.'
    def run(self):
        n = self.spinner.text
        if not n or n.startswith('('):
            return info_popup('Run', 'Select model')
        def work():
            try:
                out = self.run_fn(n)
                Clock.schedule_once(lambda *_: setattr(self.output, 'text', f'Output:\n{out}'))
            except Exception as e:
                msg = f'Run failed: {e}'
                Clock.schedule_once(lambda *_: info_popup('Error', msg))
        threading.Thread(target=work, daemon=True).start()
    def stop(self):
        n = self.spinner.text if self.spinner.text and not self.spinner.text.startswith(
            '(') else None
        def work():
            try:
                out = self.stop_fn(n)
                Clock.schedule_once(lambda *_: setattr(self.output, 'text', f'Stop: {out}'))
            except Exception as e:
                msg = f'Stop failed: {e}'
                Clock.schedule_once(lambda *_: info_popup('Error', msg))
        threading.Thread(target=work, daemon=True).start()
    def delete(self):
        n = self.spinner.text
        if not n or n.startswith('('):
            return info_popup('Delete', 'Select model')
        def work():
            try:
                out = self.delete_fn(n)
                Clock.schedule_once(lambda *_: setattr(self.output, 'text', f'Delete: {out}'))
                self.refresh()
            except Exception as e:
                msg = f'Delete failed: {e}'
                Clock.schedule_once(lambda *_: info_popup('Error', msg))
        threading.Thread(target=work, daemon=True).start()
    def set_model(self):
        n = self.spinner.text
        if not n or n.startswith('('):
            return info_popup('Set', 'Select model')
        try:
            self.set_model_fn(n)
            info_popup('Updated', f'llm.model={n}')
        except Exception as e:
            info_popup('Error', str(e))
    def set_model_snapshot(self):
        n = self.spinner.text
        if not n or n.startswith('('):
            return info_popup('Set+Snap', 'Select model')
        try:
            snap = self.set_and_snapshot_fn(n)
            info_popup('Updated', f'Snapshot {snap}')
        except Exception as e:
            info_popup('Error', str(e))

class RemoteModelsPanel(BoxLayout):
    def __init__(self, list_fn, pull_fn, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.list_fn = list_fn
        self.pull_fn = pull_fn
        row = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=6)
        self.spinner = Spinner(text='(refresh)', values=[], size_hint_x=0.55, font_size=FONT_SMALL)
        row.add_widget(self.spinner)
        for label, cb in [('Refresh', self.refresh), ('Pull', self.pull)]:
            b = Button(text=label, size_hint_x=None, width=110, font_size=FONT_SMALL)
            b.bind(on_release=lambda *_, _cb=cb: _cb())
            row.add_widget(b)
        self.add_widget(row)
        out_wrap = ScrollView(size_hint=(1, 1), bar_width=12)
        self.output = TextInput(text='', readonly=True, font_size=FONT_SMALL)
        out_wrap.add_widget(self.output)
        self.add_widget(out_wrap)
    def refresh(self):
        def work():
            try:
                models = self.list_fn()
                names = []
                for m in models:
                    nm = m.get('name') or m.get('id') or ''
                    if nm:
                        names.append(nm)
                Clock.schedule_once(lambda *_: self._update(names))
            except Exception as e:
                msg = f'Remote list failed: {e}'
                Clock.schedule_once(lambda *_: info_popup('Error', msg))
        threading.Thread(target=work, daemon=True).start()
    def _update(self, names):
        self.spinner.values = names
        self.spinner.text = names[0] if names else '(refresh)'
        self.output.text = f'Found {len(names)} remote models.'
    def pull(self):
        n = self.spinner.text
        if not n or n.startswith('('):
            return info_popup('Pull', 'Select model')
        self.output.text = f'Pulling {n}...\n'
        def work():
            try:
                last = self.pull_fn(n, stream_callback=lambda obj: Clock.schedule_once(
                    lambda *_: self._append(json.dumps(obj))))
                Clock.schedule_once(lambda *_: self._append(f'Done: {last}'))
            except Exception as e:
                msg = f'Pull failed: {e}'
                Clock.schedule_once(lambda *_: info_popup('Error', msg))
        threading.Thread(target=work, daemon=True).start()
    def _append(self, text): self.output.text += text + '\n'

class ConsolePanel(BoxLayout):
    """Interactive prompt for quick test generations."""
    def __init__(self, app_ref: 'BatLLMConfigApp', **kw):
        super().__init__(**kw)
        self.app_ref = app_ref
        self.orientation = 'vertical'
        top = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=6)
        self.model_spinner = Spinner(text='(models)', values=[],
                                     size_hint_x=0.35, font_size=FONT_SMALL)
        btn_refresh = Button(text='Refresh', size_hint_x=None, width=110, font_size=FONT_SMALL)
        btn_run = Button(text='Generate', size_hint_x=None, width=110, font_size=FONT_SMALL)
        btn_stop = Button(text='Stop', size_hint_x=None, width=90, font_size=FONT_SMALL)
        btn_refresh.bind(on_release=lambda *_: self.refresh_models())
        btn_run.bind(on_release=lambda *_: self.generate())
        btn_stop.bind(on_release=lambda *_: self.stop())
        for w in [Label(text='Model:', size_hint_x=None, width=70, font_size=FONT_SMALL),
                  self.model_spinner, btn_refresh, btn_run, btn_stop]:
            top.add_widget(w)
        self.add_widget(top)
        self.prompt = TextInput(hint_text='Enter prompt', multiline=True,
                                size_hint_y=0.38, font_size=FONT_SMALL)
        self.add_widget(self.prompt)
        out_wrap = ScrollView(size_hint=(1, 1), bar_width=12)
        self.output = TextInput(text='', readonly=True, font_size=FONT_SMALL)
        out_wrap.add_widget(self.output)
        self.add_widget(out_wrap)
        self._gen_thread = None
        self._stop_flag = False
    def refresh_models(self):
        def work():
            try:
                models = self.app_ref._local_models()
                names = [m.get('name', '') for m in models if m.get('name')]
                Clock.schedule_once(lambda *_: self._set_models(names))
            except Exception as e:
                msg = f'Model list failed: {e}'
                Clock.schedule_once(lambda *_: info_popup('Error', msg))
        threading.Thread(target=work, daemon=True).start()
    def _set_models(self, names: List[str]):
        self.model_spinner.values = names
        self.model_spinner.text = names[0] if names else '(models)'
    def stop(self):
        self._stop_flag = True
        try:
            self.app_ref._stop_models(None)
        except:
            pass
    def generate(self):
        if self._gen_thread and self._gen_thread.is_alive():
            return info_popup('Busy', 'Generation already running')
        model = self.model_spinner.text
        if not model or model.startswith('('):
            return info_popup('Generate', 'Select model')
        prompt = self.prompt.text.strip()
        if not prompt:
            return info_popup('Generate', 'Enter prompt')
        self.output.text = ''
        self._stop_flag = False
        def work():
            try:
                url = self.app_ref.ollama._u('/api/generate')
                payload = {'model': model, 'prompt': prompt, 'stream': True}
                r = requests.post(url, json=payload,
                                  timeout=self.app_ref.ollama.timeout, stream=True)
                r.raise_for_status()
                for line in r.iter_lines():
                    if self._stop_flag:
                        break
                    if not line:
                        continue
                    obj = json.loads(line.decode('utf-8'))
                    if 'response' in obj:
                        frag = obj['response']
                        Clock.schedule_once(lambda _dt, _frag=frag: self._append(_frag))
                    if obj.get('done'):
                        break
            except Exception as e:
                msg = f'Generate failed: {e}'
                Clock.schedule_once(lambda *_: info_popup('Error', msg))
        self._gen_thread = threading.Thread(target=work, daemon=True)
        self._gen_thread.start()
    def _append(self, text: str): self.output.text += text

# -------- Main App --------
class BatLLMConfigApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Predefine attributes used later to avoid AttributeError during early calls
        self.status: Label = Label()
        self.ollama = OllamaClient()

    def build(self):
        root = BoxLayout(orientation='vertical', padding=PAD, spacing=PAD)

        banner = Label(
            text='BatLLM Configurator – Edit LLM params, manage models, snapshots, and run quick tests.',
            size_hint_y=None, height=40, font_size=FONT_BASE, bold=True)
        root.add_widget(banner)

        # Path row
        path_row = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=8)
        path_row.add_widget(Label(text='Config:', size_hint_x=None, width=80, font_size=FONT_SMALL))
        default_cfg = self._default_config_path()
        self.cfg_path = TextInput(text=default_cfg, multiline=False, font_size=FONT_SMALL)
        path_row.add_widget(self.cfg_path)
        btn_load = Button(text='Load', size_hint_x=None, width=120, font_size=FONT_SMALL)
        btn_load.bind(on_release=lambda *_: self.load_config())
        btn_test = Button(text='Test Conn', size_hint_x=None, width=140, font_size=FONT_SMALL)
        btn_test.bind(on_release=lambda *_: self.test_connection())
        path_row.add_widget(btn_load)
        path_row.add_widget(btn_test)
        root.add_widget(path_row)

        # Save row
        save_row = BoxLayout(size_hint_y=None, height=ROW_HEIGHT - 4, spacing=8)
        for label, cb in [('Save LLM', self.save_llm), ('Save RAW', self.save_raw_yaml),
                          ('Save Other', self.save_other), ('Undo', self._snap_undo)]:
            b = Button(text=label, size_hint_x=None, width=150, font_size=FONT_SMALL)
            b.bind(on_release=lambda *_, _cb=cb: _cb())
            save_row.add_widget(b)
        root.add_widget(save_row)

        tabs = TabbedPanel(do_default_tab=False, tab_height=38)

        self.llm_panel = LLMPanel()
        self._add_tab(tabs, 'LLM', self.llm_panel)
        self.raw_panel = RawYAMLPanel()
        self._add_tab(tabs, 'YAML', self.raw_panel)
        self.snap_panel = SnapshotPanel(self._snap_list, self._snap_activate,
                                        self._snap_save, self._snap_undo, self._snapshot_dir)
        self._add_tab(tabs, 'Snapshots', self.snap_panel)
        self.other_panel = OtherSettingsPanel()
        self._add_tab(tabs, 'Other', self.other_panel)
        self.local_panel = LocalModelsPanel(self._local_models, self._run_model,
                                            self._stop_models, self._delete_model,
                                            self._set_llm_model, self._set_llm_model_and_snapshot)
        self._add_tab(tabs, 'Local Models', self.local_panel)
        self.remote_panel = RemoteModelsPanel(self._remote_models, self._pull_model)
        self._add_tab(tabs, 'Remote Models', self.remote_panel)
        self.console_panel = ConsolePanel(self)
        self._add_tab(tabs, 'Console', self.console_panel)

        root.add_widget(tabs)
        self.status = Label(text='Ready.', size_hint_y=None, height=32,
                            font_size=FONT_SMALL, halign='left', valign='middle')
        self.status.bind(size=lambda *_: setattr(self.status, 'text_size', self.status.size))
        root.add_widget(self.status)

        # Schedule after status exists
        Clock.schedule_once(lambda dt: self.load_config(), 0)
        Clock.schedule_once(lambda dt: self.console_panel.refresh_models(), 0.8)
        return root

    # ---- Config helpers (added ensure) ----
    def _ensure_config_file(self, path: str):
        if not os.path.exists(path):
            base_dir = os.path.dirname(path)
            if base_dir:
                os.makedirs(base_dir, exist_ok=True)
            minimal = {
                'llm': {
                    'url': 'http://localhost',
                    'port': 11434,
                    'model': '',
                    'temperature': None,
                    'top_p': None,
                    'top_k': None,
                    'timeout': 10.0,
                    'max_tokens': None,
                    'stop': None,
                    'seed': None,
                    'num_thread': None,
                    'num_ctx': None,
                    'num_predict': None
                }
            }
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(minimal, f, sort_keys=False)

    # ---- Load & Save (patched load_config guarding status) ----
    def load_config(self):
        path = self.cfg_path.text.strip()
        try:
            self._ensure_config_file(path)
            cfg = self._read_cfg()
            self.llm_panel.load_from_config(cfg)
            self.raw_panel.load_from_config(cfg)
            self.other_panel.load_from_config(cfg)
            self._update_ollama_from_cfg(cfg)
            if self.status:
                self.status.text = f'Loaded {path}'
            self.snap_panel.refresh()
        except Exception as e:
            info_popup('Error', f'Load failed: {e}')
            if self.status:
                self.status.text = 'Load failed'
            else:
                print('Load failed (status not ready):', e)

    # (Minor: after each save also refresh model spinner in console if model changed)
    def _post_save_refresh(self, cfg: Dict[str, Any]):
        try:
            model = (cfg.get('llm') or {}).get('model')
            if model:
                Clock.schedule_once(lambda dt: self.console_panel.refresh_models(), 0.2)
        except Exception:
            pass

    def save_llm(self):
        try:
            cfg = self._read_cfg()
            cfg = self.llm_panel.write_to_config(cfg)
            self._mgr().backup()
            self._write_cfg(cfg)
            self.raw_panel.load_from_config(cfg)
            self.other_panel.load_from_config(cfg)
            self._update_ollama_from_cfg(cfg)
            if self.status:
                self.status.text = 'LLM saved'
            self._post_save_refresh(cfg)
        except Exception as e:
            info_popup('Error', f'Save LLM failed: {e}')

    def save_raw_yaml(self):
        try:
            cfg = self.raw_panel.read_yaml()
            self._mgr().backup()
            self._write_cfg(cfg)
            self.llm_panel.load_from_config(cfg)
            self.other_panel.load_from_config(cfg)
            self._update_ollama_from_cfg(cfg)
            if self.status:
                self.status.text = 'Raw YAML saved'
            self._post_save_refresh(cfg)
        except Exception as e:
            info_popup('Error', f'Save RAW failed: {e}')

    def save_other(self):
        try:
            cfg = self._read_cfg()
            cfg = self.other_panel.apply_to_config(cfg)
            self._mgr().backup()
            self._write_cfg(cfg)
            self.llm_panel.load_from_config(cfg)
            self.raw_panel.load_from_config(cfg)
            self.other_panel.load_from_config(cfg)
            self._update_ollama_from_cfg(cfg)
            if self.status:
                self.status.text = 'Other settings saved'
            self._post_save_refresh(cfg)
        except Exception as e:
            info_popup('Error', f'Save Other failed: {e}')

    # ---- Utility UI helpers
    def _add_tab(self, tabs: TabbedPanel, name: str, widget):
        ti = TabbedPanelItem(text=name)
        ti.add_widget(widget)
        tabs.add_widget(ti)

    # ---- Config helpers
    def _default_config_path(self) -> str:
        # Try project default; adjust if running from inside project
        candidates = [
            os.path.join(os.getcwd(), 'src', 'configs', 'config.yaml'),
            os.path.join(os.getcwd(), 'config.yaml'),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return candidates[0]

    def _mgr(self) -> ConfigManager: return ConfigManager(self.cfg_path.text.strip())
    def _snapshot_dir(self) -> str: return os.path.dirname(self.cfg_path.text.strip()) or '.'
    def _read_cfg(self) -> Dict[str, Any]: return self._mgr().load()
    def _write_cfg(self, cfg: Dict[str, Any]): self._mgr().save(cfg)

    # ---- Load & Save
    def load_config(self):
        try:
            cfg = self._read_cfg()
            self.llm_panel.load_from_config(cfg)
            self.raw_panel.load_from_config(cfg)
            self.other_panel.load_from_config(cfg)
            self._update_ollama_from_cfg(cfg)
            self.status.text = f'Loaded {self.cfg_path.text}'
            self.snap_panel.refresh()
        except Exception as e:
            info_popup('Error', f'Load failed: {e}')
            self.status.text = 'Load failed'

    def save_llm(self):
        try:
            cfg = self._read_cfg()
            cfg = self.llm_panel.write_to_config(cfg)
            self._mgr().backup()
            self._write_cfg(cfg)
            self.raw_panel.load_from_config(cfg)
            self.other_panel.load_from_config(cfg)
            self._update_ollama_from_cfg(cfg)
            self.status.text = 'LLM saved'
        except Exception as e:
            info_popup('Error', f'Save LLM failed: {e}')

    def save_raw_yaml(self):
        try:
            cfg = self.raw_panel.read_yaml()
            self._mgr().backup()
            self._write_cfg(cfg)
            self.llm_panel.load_from_config(cfg)
            self.other_panel.load_from_config(cfg)
            self._update_ollama_from_cfg(cfg)
            self.status.text = 'Raw YAML saved'
        except Exception as e:
            info_popup('Error', f'Save RAW failed: {e}')

    def save_other(self):
        try:
            cfg = self._read_cfg()
            cfg = self.other_panel.apply_to_config(cfg)
            self._mgr().backup()
            self._write_cfg(cfg)
            self.llm_panel.load_from_config(cfg)
            self.raw_panel.load_from_config(cfg)
            self.other_panel.load_from_config(cfg)
            self._update_ollama_from_cfg(cfg)
            self.status.text = 'Other settings saved'
        except Exception as e:
            info_popup('Error', f'Save Other failed: {e}')

    # ---- Ollama connection
    def _update_ollama_from_cfg(self, cfg: Dict[str, Any]):
        llm = cfg.get('llm', {}) if isinstance(cfg.get('llm'), dict) else {}
        url = (llm.get('url') or 'http://localhost').rstrip('/')
        port = int(llm.get('port') or 11434)
        timeout = float(llm.get('timeout') or 10.0)
        self.ollama = OllamaClient(url, port, timeout)

    def test_connection(self):
        def work():
            try:
                self.ollama.list_local_models()
                Clock.schedule_once(lambda *_: self._set_status('Ollama OK'))
            except Exception as e:
                msg = str(e)
                Clock.schedule_once(lambda *_: (self._set_status('Ollama unavailable'),
                                    info_popup('Ollama', f'Unavailable: {msg}')))
        threading.Thread(target=work, daemon=True).start()
    def _set_status(self, msg: str): self.status.text = msg

    # ---- Snapshot ops
    def _snap_list(self) -> List[str]: return self._mgr().list_snapshots(self._snapshot_dir())
    def _snap_activate(self, path: str):
        self._mgr().activate_snapshot(path)
        self.load_config()
    def _snap_save(self, name: str) -> str:
        return self._mgr().save_snapshot_html(name, self._read_cfg(), self._snapshot_dir())
    def _snap_undo(self):
        try:
            self._mgr().undo()
            self.load_config()
            self.status.text = 'Undo restored'
        except Exception as e:
            info_popup('Error', f'Undo failed: {e}')

    # ---- Model ops (safe wrappers)
    def _local_models(self) -> List[Dict[str, Any]]:
        try:
            return self.ollama.list_local_models()
        except Exception:
            return []
    def _run_model(self, name: str) -> str:
        try:
            return self.ollama.run_once(model=name, prompt='ping', num_predict=8)
        except Exception as e:
            return f'Error: {e}'
    def _stop_models(self, name: Optional[str] = None) -> Dict[str, Any]:
        try:
            return self.ollama.stop(model=name)
        except Exception as e:
            return {'error': str(e)}
    def _delete_model(self, name: str) -> Dict[str, Any]:
        try:
            return self.ollama.delete_model(name)
        except Exception as e:
            return {'error': str(e)}
    def _set_llm_model(self, name: str):
        cfg = self._read_cfg()
        llm = cfg.get('llm', {}) or {}
        llm['model'] = name
        cfg['llm'] = llm
        self._mgr().backup()
        self._write_cfg(cfg)
        self.llm_panel.load_from_config(cfg)
        self.raw_panel.load_from_config(cfg)
        self.other_panel.load_from_config(cfg)
    def _set_llm_model_and_snapshot(self, name: str) -> str:
        self._set_llm_model(name)
        snap = name
        self._mgr().save_snapshot_html(snap, self._read_cfg(), self._snapshot_dir())
        self.snap_panel.refresh()
        return snap
    def _remote_models(self) -> List[Dict[str, Any]]:
        try:
            return OllamaClient.list_remote_models()
        except Exception:
            return []
    def _pull_model(self, name: str, stream_callback=None) -> Dict[str, Any]:
        try:
            return self.ollama.pull_model(name, stream_callback=stream_callback)
        except Exception as e:
            return {'error': str(e)}

if __name__ == '__main__':
    BatLLMConfigApp().run()
