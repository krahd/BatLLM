# BatLLM's API 
This file was generated using docstrings and pydoc-markdown. 
BatLLM's docstrings do need work.

## Table of Contents

* [normalized\_canvas](#normalized_canvas)
  * [NormalizedCanvas](#normalized_canvas.NormalizedCanvas)
* [util](#util)
  * [show\_confirmation\_dialog](#util.show_confirmation_dialog)
  * [show\_fading\_alert](#util.show_fading_alert)
  * [show\_text\_input\_dialog](#util.show_text_input_dialog)
  * [find\_id\_in\_parents](#util.find_id_in_parents)
* [bot](#bot)
  * [Bot](#bot.Bot)
    * [rot](#bot.Bot.rot)
    * [\_\_init\_\_](#bot.Bot.__init__)
    * [render](#bot.Bot.render)
    * [move](#bot.Bot.move)
    * [rotate](#bot.Bot.rotate)
    * [append\_prompt\_to\_history](#bot.Bot.append_prompt_to_history)
    * [rewind\_prompt\_history](#bot.Bot.rewind_prompt_history)
    * [forward\_prompt\_history](#bot.Bot.forward_prompt_history)
    * [get\_current\_prompt\_from\_history](#bot.Bot.get_current_prompt_from_history)
    * [get\_current\_prompt](#bot.Bot.get_current_prompt)
    * [get\_prompt](#bot.Bot.get_prompt)
    * [augmenting\_prompt](#bot.Bot.augmenting_prompt)
    * [prepare\_prompt\_submission](#bot.Bot.prepare_prompt_submission)
    * [submit\_prompt\_to\_llm](#bot.Bot.submit_prompt_to_llm)
    * [damage](#bot.Bot.damage)
    * [toggle\_shield](#bot.Bot.toggle_shield)
    * [shoot](#bot.Bot.shoot)
* [history\_manager](#history_manager)
  * [HistoryManager](#history_manager.HistoryManager)
    * [\_\_init\_\_](#history_manager.HistoryManager.__init__)
    * [start\_game](#history_manager.HistoryManager.start_game)
    * [end\_game](#history_manager.HistoryManager.end_game)
    * [start\_round](#history_manager.HistoryManager.start_round)
    * [end\_round](#history_manager.HistoryManager.end_round)
    * [start\_turn](#history_manager.HistoryManager.start_turn)
    * [end\_turn](#history_manager.HistoryManager.end_turn)
    * [save\_session](#history_manager.HistoryManager.save_session)
    * [to\_json](#history_manager.HistoryManager.to_json)
    * [to\_text](#history_manager.HistoryManager.to_text)
* [main](#main)
  * [BattleLLM](#main.BattleLLM)
* [bullet](#bullet)
  * [Bullet](#bullet.Bullet)
    * [update](#bullet.Bullet.update)
    * [segment\_hits\_bot](#bullet.Bullet.segment_hits_bot)
* [app\_config](#app_config)

<a id="normalized_canvas"></a>

# normalized\_canvas

<a id="normalized_canvas.NormalizedCanvas"></a>

## NormalizedCanvas Objects

```python
class NormalizedCanvas()
```

Context manager for normalized (0 to 1) coordinate drawing in a Kivy widget.

<a id="util"></a>

# util

<a id="util.show_confirmation_dialog"></a>

#### show\_confirmation\_dialog

```python
def show_confirmation_dialog(title, message, on_confirm, on_cancel=None)
```

Displays a modal confirmation dialog with a title and message.

Args:
    title (_type_): the title of the dialog
    message (_type_): the message to display in the dialog
    on_confirm (_type_): function to call when the user confirms
    on_cancel (_type_, optional): function to call when the user cancels. Defaults to None.

<a id="util.show_fading_alert"></a>

#### show\_fading\_alert

```python
def show_fading_alert(title, message, duration=1.0, fade_duration=1.0)
```

Displays a modal alert with a title and message that fades out and closes itsel.

Args:
    title (_type_): the title of the alert
    message (_type_): the message to display in the alert
    duration (float, optional): How long does it take for the alert to start fading out. Defaults to 1.0.
    fade_duration (float, optional): How long does the fade out process take. Defaults to 1.0.

<a id="util.show_text_input_dialog"></a>

#### show\_text\_input\_dialog

```python
def show_text_input_dialog(on_confirm,
                           on_cancel=None,
                           title="",
                           default_text="",
                           input_hint="Enter a text")
```

A modal dialog to enter a filename for saving. # TODO change it into a generic dialog for entering text.

Args:
    on_confirm (_type_): function to call when the user confirms the filename
    on_cancel (_type_, optional): function to call when the user cancels. Defaults to None.
    title (str, optional): title of the dialog. Defaults to "".
    default_text (str, optional): default (pre-set) value for the text field). Defaults to "".
    input_hint (str, optional): hint text for the input field. Defaults to "Enter a text". It is only visible if the default value is empty

<a id="util.find_id_in_parents"></a>

#### find\_id\_in\_parents

```python
def find_id_in_parents(self, target_id)
```

Searches for an element among the ancestors of a Kivy element by its id

Args:
    target_id (_type_): the id of the object to find.

Returns:
_type_: The found object or None

<a id="bot"></a>

# bot

<a id="bot.Bot"></a>

## Bot Objects

```python
class Bot(Widget)
```

This class models a game bot.

Args:
    Widget (_type_): Kivy's base Widget class

<a id="bot.Bot.rot"></a>

#### rot

in radians

<a id="bot.Bot.__init__"></a>

#### \_\_init\_\_

```python
def __init__(id, board_widget, **kwargs)
```

Constructor

Args:
    id (_type_): the bot id
    board_widget (_type_): its parent, that is the game board where the bot lives.

<a id="bot.Bot.render"></a>

#### render

```python
def render()
```

Draws itself. It assumes a NormalizedCanvas.

<a id="bot.Bot.move"></a>

#### move

```python
def move()
```

The bot takes a step. Corresponds to the command 'M'

<a id="bot.Bot.rotate"></a>

#### rotate

```python
def rotate(angle)
```

The bot rotates by a given angle. Corresponds to the commands 'C' and 'A'

<a id="bot.Bot.append_prompt_to_history"></a>

#### append\_prompt\_to\_history

```python
def append_prompt_to_history(new_prompt)
```

Adds the new prompt to the prompt.history object.
It is now ready to run it.

Args:
    new_prompt (_type_): the new prompt

<a id="bot.Bot.rewind_prompt_history"></a>

#### rewind\_prompt\_history

```python
def rewind_prompt_history()
```

Rewinds

<a id="bot.Bot.forward_prompt_history"></a>

#### forward\_prompt\_history

```python
def forward_prompt_history()
```

Forwards

<a id="bot.Bot.get_current_prompt_from_history"></a>

#### get\_current\_prompt\_from\_history

```python
def get_current_prompt_from_history()
```

Returns a prompt from the history using a cursor. Rewind and Forward move the cursor.

Returns:
    _type_: a string with the prompt

<a id="bot.Bot.get_current_prompt"></a>

#### get\_current\_prompt

```python
def get_current_prompt()
```

Returns the current prompt. It is equivalent to get_prompt.

Returns:
    _type_: a string with the prompt

<a id="bot.Bot.get_prompt"></a>

#### get\_prompt

```python
def get_prompt()
```

Returns the current prompt. It is equivalent to get_current_prompt_from_history.
Returns:
    _type_: a string with the prompt

<a id="bot.Bot.augmenting_prompt"></a>

#### augmenting\_prompt

```python
def augmenting_prompt(augmenting)
```

Toggles the flag indicating if the player prompts are augmented with game info.

Args:
    augmenting (_type_): the new flag value

<a id="bot.Bot.prepare_prompt_submission"></a>

#### prepare\_prompt\_submission

```python
def prepare_prompt_submission(new_prompt)
```

Gets ready to execute

Args:
    new_prompt (_type_): the prompt to use

<a id="bot.Bot.submit_prompt_to_llm"></a>

#### submit\_prompt\_to\_llm

```python
def submit_prompt_to_llm()
```

Takes care of the interaction with the LLM

<a id="bot.Bot.damage"></a>

#### damage

```python
def damage()
```

The bot's been hitl

<a id="bot.Bot.toggle_shield"></a>

#### toggle\_shield

```python
def toggle_shield()
```

Toggles the shield state.

<a id="bot.Bot.shoot"></a>

#### shoot

```python
def shoot()
```

Tries to shoot a bullet. It will only succeed if the shield is down.

Returns:
    _type_: the bullet shot or None

<a id="history_manager"></a>

# history\_manager

<a id="history_manager.HistoryManager"></a>

## HistoryManager Objects

```python
class HistoryManager()
```

<a id="history_manager.HistoryManager.__init__"></a>

#### \_\_init\_\_

```python
def __init__()
```

Initialize a new HistoryManager with no active game.

<a id="history_manager.HistoryManager.start_game"></a>

#### start\_game

```python
def start_game(game)
```

Start a new game. Initialize the game log with start time and initial bot states.
`game` is the BoardGameWidget

<a id="history_manager.HistoryManager.end_game"></a>

#### end\_game

```python
def end_game(game, force=False)
```

End the current game. This can be called at any time (e.g., normal game end or aborted mid-round).
It finalizes any ongoing round/turn and records the end time and final outcome.
The parameter `force` is used internally to finalize a game without double-calling end_game recursively.

<a id="history_manager.HistoryManager.start_round"></a>

#### start\_round

```python
def start_round(game)
```

Start a new round within the current session. Should be called at the beginning of each round.
Records the round start and the initial state at this point.

<a id="history_manager.HistoryManager.end_round"></a>

#### end\_round

```python
def end_round(game)
```

End the current round. Records the end time and round winner.

<a id="history_manager.HistoryManager.start_turn"></a>

#### start\_turn

```python
def start_turn(game)
```

Start a new turn within the current round. Called at the beginning of a turn.
Records the pre-turn state and which bot is acting (if available).

<a id="history_manager.HistoryManager.end_turn"></a>

#### end\_turn

```python
def end_turn(game, action_description=None)
```

End the current turn. Called after the turn's action is resolved.
Records the post-turn state and (optionally) the action description.

<a id="history_manager.HistoryManager.save_session"></a>

#### save\_session

```python
def save_session(filepath)
```

Save the entire session history to a JSON file.
This will include all games played in this session.

<a id="history_manager.HistoryManager.to_json"></a>

#### to\_json

```python
def to_json()
```

Get the full history as a JSON string.

<a id="history_manager.HistoryManager.to_text"></a>

#### to\_text

```python
def to_text()
```

Get the full history in a human-readable indented text format (key: value style).
Returns a multi-line string.

<a id="main"></a>

# main

<a id="main.BattleLLM"></a>

## BattleLLM Objects

```python
class BattleLLM(App)
```

This is the main application class for BattleLLM.
Using Kivy, it initializes the screen manager and sets up the application's windows


Args:
    App (_type_): Kivy's base application class.

<a id="bullet"></a>

# bullet

<a id="bullet.Bullet"></a>

## Bullet Objects

```python
class Bullet()
```

This class models the bullets shot by the bots. It takes care of its own rendering and the detection of collission against the opponent and the arena's limits.

<a id="bullet.Bullet.update"></a>

#### update

```python
def update(bots)
```

Check for out of bounds and collisions with bots.

Args:
    bots (_type_): all the game bots 

Returns:
    _type_: (alive, damaged_bot_id).

<a id="bullet.Bullet.segment_hits_bot"></a>

#### segment\_hits\_bot

```python
def segment_hits_bot(bot, p1, p2)
```

Determines if the line segment from p1 to p2 hits the bot in an unshielded area.

Args:
    bot (_type_): the bot
    p1 (_type_): segment start
    p2 (_type_): segment end

Returns:
    _type_: True if the bot is hit (taking damage), or False if no hit or the hit is blocked by the shield

<a id="app_config"></a>

# app\_config

