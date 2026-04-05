from __future__ import annotations

from types import SimpleNamespace

from view.load_text_dialog import LoadTextDialog


def _build_dialog(files, selection=None):
    chooser = SimpleNamespace(files=files, selection=selection or [], focus=False)
    preview = SimpleNamespace(text="")
    choices = []
    dismissed = {"value": False}

    dialog = SimpleNamespace(
        ids=SimpleNamespace(filechooser=chooser, preview=preview),
        on_choice=lambda choice: choices.append(choice),
        dismiss=lambda: dismissed.__setitem__("value", True),
    )
    dialog._visible_text_files = lambda: LoadTextDialog._visible_text_files(dialog)
    dialog._on_file_select = lambda selection: LoadTextDialog._on_file_select(dialog, selection)
    dialog._move_selection = lambda step: LoadTextDialog._move_selection(dialog, step)
    dialog._load_selected = lambda: LoadTextDialog._load_selected(dialog)
    dialog._cancel = lambda: LoadTextDialog._cancel(dialog)
    dialog._initialize_selection = lambda *args: LoadTextDialog._initialize_selection(dialog, *args)

    return dialog, chooser, preview, choices, dismissed


def test_load_text_dialog_escape_matches_cancel(tmp_path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("alpha", encoding="utf-8")
    dialog, _chooser, _preview, choices, dismissed = _build_dialog([str(prompt_file)])

    handled = LoadTextDialog._on_key_down(dialog, None, (27, "escape"), "", [])

    assert handled is True
    assert choices == [None]
    assert dismissed["value"] is True


def test_load_text_dialog_arrow_keys_select_and_enter_load(tmp_path) -> None:
    first_file = tmp_path / "alpha.txt"
    second_file = tmp_path / "bravo.txt"
    first_file.write_text("alpha", encoding="utf-8")
    second_file.write_text("bravo", encoding="utf-8")

    dialog, chooser, preview, choices, dismissed = _build_dialog(
        [str(first_file), str(second_file)],
        selection=[str(first_file)],
    )
    LoadTextDialog._on_file_select(dialog, chooser.selection)

    handled = LoadTextDialog._on_key_down(dialog, None, (274, "down"), "", [])
    assert handled is True
    assert chooser.selection == [str(second_file)]
    assert preview.text == "bravo"

    handled = LoadTextDialog._on_key_down(dialog, None, (13, "enter"), "", [])
    assert handled is True
    assert choices == ["bravo"]
    assert dismissed["value"] is True


def test_load_text_dialog_initializes_first_visible_selection(tmp_path) -> None:
    first_file = tmp_path / "alpha.txt"
    second_file = tmp_path / "bravo.txt"
    first_file.write_text("alpha", encoding="utf-8")
    second_file.write_text("bravo", encoding="utf-8")

    dialog, chooser, preview, _choices, _dismissed = _build_dialog(
        [str(first_file), str(second_file)],
        selection=[],
    )

    LoadTextDialog._initialize_selection(dialog)

    assert chooser.focus is True
    assert chooser.selection == [str(first_file)]
    assert preview.text == "alpha"
