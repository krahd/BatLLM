# BatLLM

BatLLM (Batch Large Language Model) is a fast, minimal, header-only C++ library for running LLM (Large Language Model) inference. Its goal is to provide an efficient, easy-to-use, and dependency-free solution for batch inference of transformer models. BatLLM supports various LLM architectures, particularly those using Q4 quantization and GGUF model formats, and is tuned for both single and multi-threaded execution.

> **Features:**
> 
> - **Pure C++ (C++17)** - No external dependencies required
> - **Header-only** - Just include and use!
> - **Batch inference** - Fast token generation for multiple sequences
> - **Q4 quantization (QK=32)** - Efficient and compact
> - **GGUF model support** - Load and run standard LLM models
> - **Simple API** - Minimal learning curve
> - **Extensible** - Add support for new architectures/models easily

---

## Table of Contents

- [BatLLM](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#batllm)
    - [Supported Models](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#supported-models)
    - [Getting Started](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#getting-started)
        - [Requirements](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#requirements)
        - [Installation](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#installation)
        - [Usage Example](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#usage-example)
    - [API](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#api)
        - [Model Loading](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#model-loading)
        - [Batch Inference](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#batch-inference)
    - [Performance](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#performance)
    - [FAQ](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#faq)
    - [Contributing](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#contributing)
    - [License](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#license)
    - [References](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#references)

---

## Supported Models

- **Model Format:** GGUF (with support for Q4 quantization, QK=32)
- **Architectures:** Llama, Mistral, Mixtral (expandable)
- **Examples:** Llama-2, Mistral-7B/8x7B (Q4 GGUF)
- Support for other architectures can be added as long as their layers are composed of supported primitives.

---

## Getting Started

### Requirements

- C++17 or newer
- No external dependencies
- Linux/Windows/MacOS (tested on Linux x86_64, should work on most platforms)

### Installation

BatLLM is header-only. Just add the `batllm` folder to your project and include the header.

bash

```
git clone https://github.com/krahd/BatLLM.git
```

Include the header(s) in your code:

C++

```
#include "batllm/batllm.h"
```

> Optionally, build and use the sample main executable:
> 
> bash

> ```
> mkdir build && cd build
> cmake ..
> make
> ./batllm_main --help
> ```

### Usage Example

Below is a simple example loading a GGUF model and generating tokens in batch:

C++

```
#include "batllm/batllm.h"

int main() {
    batllm::Model model("models/llama-7b-q4_0.gguf");
    std::vector<std::string> prompts = {
        "Hello, my name is",
        "The capital of France is"
    };
    auto results = model.batch_generate(prompts, /*max_tokens=*/16);

    for (size_t i = 0; i < prompts.size(); ++i) {
        printf("Prompt: %s\nResult: %s\n\n", prompts[i].c_str(), results[i].
```

![](https://avatars.githubusercontent.com/u/349947?s=80&v=4)

krahdJul 25, 2025

Analyze the repository [https://github.com/krahd/BatLLM](https://github.com/krahd/BatLLM) and generate a comprehensive documentation for its readme.md bear in mind that batllm is a game where the players give prompts to locally run llms which in turn interact with the game (a turn-based simple bot battle). This is an example of prompt that can be given to a llm that participates in the game: You are an expert gamer. Your task is to control a bot in a videogame called BatLLM, a two-player battle game where an LLM like you controls a bot. You receive information about the game state and a prompt written by the human player that guides your behaviours.

We refer to the human players as "player", to you as "llama", and to the in-game battle bot as "bot". We refer to the environment where the bots run as "world". The world holds the game state, receives commands from the llama, executes them and updates the game state. The prompt given to the llama is a combination of the game status and the prompt written by the player in charge of the bot.

The game is a two-player battle game where each player controls a bot through the llama. The player writes a prompt that guides the llama that, in turn, outputs the commands given to the player's bot.

The game logic (main loop) is as follows:

- while both bots are alive:
    - each player enters a prompt that is given to their Ollama.
    - a starting player is chosen randomly
    - repeat ROUND_LENGTH times stopping earlier if one of the bots dies:
        - prompt each player's llama with the player's prompt. The llama's response will be the command that is given to the player's bot.

once the round is completed, the players can input new prompts that will be used in the upcoming round.

Each bot has a state. The state of a bot consists of the following variableS: x - the bot's x coordinate within the world. y - the bot's y coordinate within the world. a - the bot's rotation within the world. s - the state of the bot's shield (either up (1) or down (0)). h - the bot's health. Initially INITIAL_HEALTH. If h reaches 0 the bot dies.

Each turn the bots execute the command given to it entirely.

The commands that the bots understand are: Cd - the bot rotates clockwise around its center for d degrees. Example: C20 Ad - the bot rotates anticlockwise around its center for d degrees. Example: D180 M - the bot moves forward a distance of STEP_LENGTH (it takes a stop forward). Example: M S1 - the bot raises its shield. It will remain up until explicitly lowered. Example: S1 S0 - the bot lowers its shield. It will remain down until explicitly raised. Example: S0 S - the bit lowers its shield if up or rises it if down. Example: S B - if the shield is low, the bot shoots a bullet forward. If the shield is up it does nothing. Example: B.

Everything else is ignored (this means that the bot does not do do anything in this turn).

When a bot shoots a bullet (B) the world runs the bullet behavior until the bullet either hits the other bot or goes out of bounds. This means that the other bot cannot move until the bullet hits it or leaves the screen.

When a bot is hit by a bullet in a place not covered by a raised shield, its energy decreases by BULLET_DAMAGE. If a bullet hits the raised shield it does not cause any damage. The shield only protects the 'front' of the bot. It will only stop bullets that hit it in its front, plus minus SHIELD_SIZE degrees.

Before each round starts, the players enter their prompts.

Remember, your task is to receive the game state and to output a valid command, using the user's prompt as guideline.

![OpenAI logo](https://github.com/images/modules/marketplace/models/families/openai.svg)

OpenAI GPT-4.1Jul 25, 2025

Absolutely! Given this revised description, the repository **BatLLM** is not an LLM inference engine, but a **two-player turn-based bot battle game** controlled by local LLMs. Players craft prompts that steer their bots’ actions in-game through LLM-generated commands.

Below is a comprehensive, well-structured `README.md`, suitable for your audience and for guiding contributors/players.

---

# BatLLM: LLM-Powered Bot Battle Game

BatLLM is a two-player, turn-based battle game where humans control in-game bots **indirectly**—by writing prompts for local Large Language Models (LLMs). Each player's prompt is sent to an LLM (e.g., [Ollama](https://ollama.ai)), which interprets the game state and outputs the bot's next command, creating a unique blend of strategy, language, and AI-driven gameplay.

---

## Table of Contents

- [Features](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#features)
- [How It Works](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#how-it-works)
- [Game Rules](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#game-rules)
- [Bot Command Reference](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#bot-command-reference)
- [Quick Start](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#quick-start)
- [Development & Contributing](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#development--contributing)
- [FAQ](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#faq)
- [License](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#license)

---

## Features

- Turn-based, two-player competitive gameplay
- Each bot is controlled by a local LLM (like 'llama’ variants)
- Players influence their bot's behavior via **creative prompts**
- LLMs receive structured game state and a player-written prompt for context
- Intuitive, minimal command set for bots (see [Bot Command Reference](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#bot-command-reference))
- Simple C++ codebase for easy extension/hacking

---

## How It Works

1. **Setup**: Each player is assigned a bot. Each round, both enter a prompt—this may instruct their bot either directly or in a role-play fashion.
2. **LLM Mediation**: The game sends the current state and the player's latest prompt to the player’s LLM.
3. **Command Selection**: The LLM generates a single command (like move, turn, shoot, raise shield...) for its bot.
4. **Game Loop**:
    - A starting player is chosen randomly each round.
    - Bots act, round-robin style, for `ROUND_LENGTH` turns (or until one bot dies).
    - Each turn, the game relays the results to the players for the next round of prompt crafting.

---

## Game Rules

- **Bots**:
    
    - Each has an `x, y` position, a rotation (`a`), shield state (`s`), and health (`h`).
    - Health starts at `INITIAL_HEALTH`. When `h` reaches 0, the bot dies.
- **Turns & Rounds**:
    
    - Before each round, both players input prompts, which are given to their LLMs.
    - Each turn, both bots receive commands from their respective LLMs and execute them.
    - The round ends after a preset number of turns or when a bot is destroyed.
- **Commands** (from LLM output):
    
    - Only recognized commands are executed (see below). All else is ignored (no action).
- **Combat**:
    
    - If a bot fires (`B`) and its shield is down, a bullet is simulated, potentially damaging the other bot unless blocked by a shield (front-facing only).
    - When fired upon, the bot cannot move until the projectile hits or leaves the field.
- **Shield Mechanics**:
    
    - Shields can be up (`S1`), down (`S0`), toggled (`S`), or left unchanged.
    - Only the front arc (±`SHIELD_SIZE` degrees) is protected.

---

## Bot Command Reference

|Code|Action|Example|Notes|
|---|---|---|---|
|`Cd`|Rotate **clockwise** by `d` degrees.|`C20`|e.g. `C180` for 180° clockwise|
|`Ad`|Rotate **anticlockwise** by `d` degrees.|`A40`|e.g. `A90` for 90° left|
|`M`|Move ahead by one step (`STEP_LENGTH`).|`M`|One forward move per command|
|`S1`|**Raise shield**. Remains up until changed.|`S1`||
|`S0`|**Lower shield**. Remains down until changed.|`S0`||
|`S`|**Toggle shield**: raises if down, lowers if up.|`S`||
|`B`|**Fire bullet** (if shield down). Does nothing if shield up.|`B`|Bullet direction: bot's facing|

_Any other output from the LLM is interpreted as 'do nothing' this turn._

---

## LLM Prompt Example

Each LLM receives a system/user prompt like:

Code

```
You are an expert gamer. Your task is to control a bot in BatLLM, a two-player battle game where an LLM like you controls a bot. You receive information about the game state and a prompt written by the human player that guides your behaviours.

<Game State>
Bot position: (x=..., y=...), angle=..., shield=..., health=...
Opponent position: (x=..., y=...), angle=..., shield=..., health=...

<Player's Custom Prompt>
Try to dodge the next bullet, then retaliate when the enemy's shield is down.
```

_The LLM should respond with a valid command for the bot, e.g. `C90`, `M`, `B`, etc._

---

## Quick Start

1. **Requirements**
    
    - C++ compiler (C++17+)
    - [Ollama](https://ollama.ai) or another supported local LLM server
    - (Optional) CMake for building main program
2. **Clone & Build**
    
    bash
    

3. ```
    git clone https://github.com/krahd/BatLLM.git
    cd BatLLM
    mkdir build && cd build
    cmake ..
    make
    ./batllm
    ```
    
4. **Running the Game**
    
    - Start your local LLM servers (see next section).
    - Follow the prompts in terminal to enter your custom prompts each round.
    - Watch the battle unfold!

---

### Connecting to LLM Engines

BatLLM is designed to work with locally running LLM APIs like Ollama. You may need to configure the engine endpoints in a config file or via command line, depending on the current implementation.

---

## Development & Contributing

BatLLM is young! Pull requests, bug reports, and feature suggestions are welcome.

### Project Structure

Code

```
/
 ├─ src/           # Game logic and main loop
 ├─ batllm/        # Bot, world, and LLM interface code
 ├─ assets/        # (Optional) Images, sample maps, docs
 ├─ CMakeLists.txt # Build instructions
 └─ README.md
```

### Contributing

1. Fork and clone the repository
2. Create a new branch for your feature/bugfix
3. Submit a PR referencing relevant issues (if any)

---

## FAQ

**Q: Is BatLLM a serious LLM benchmark or inference engine?**  
A: No: it's a _game_ project themed for creative prompt interaction with LLM-powered bots.

**Q: Can I use ChatGPT as the LLM?**  
A: Designed for local LLMs (Ollama, Llama.cpp servers etc.), but any language model with compatible API/CLI could be adapted.

**Q: Can the LLM cheat or see hidden information?**  
A: Each LLM only receives the bot's game state and the player's prompt as input.

---

## License

[MIT License](https://github.com/marketplace/models/azure-openai/gpt-4-1/LICENSE)

---

## Credits & References

Built by @krahd, inspired by bot programming games and the power of local large language models!

---

## Enjoy battling with prompt-powered bots!

Have fun experimenting with AI, prompts, and strategy!

---

Feel free to tailor sections like "Running the Game" and "Configuring LLM Endpoints" to match your repo code and instructions. Let me know if you want usage examples from the actual code, installation enhancements, or screenshots!

![](https://avatars.githubusercontent.com/u/349947?s=80&v=4)

krahdJul 25, 2025

edit the description noting that there are different modes of playing, namely:

![OpenAI logo](https://github.com/images/modules/marketplace/models/families/openai.svg)

OpenAI GPT-4.1Jul 25, 2025

Certainly! Here’s an updated version of the **README.md**’s description section, expanded to note and briefly describe the different modes of playing in **BatLLM**. The modes can be called out clearly in the **Features** section, and explained in a new **Game Modes** section after "How It Works" for structural clarity.

---

# BatLLM: LLM-Powered Bot Battle Game

BatLLM is a two-player, turn-based battle game where humans control in-game bots **indirectly**—by writing prompts for local Large Language Models (LLMs). Each player's prompt is sent to an LLM (e.g., [Ollama](https://ollama.ai)), which interprets the game state and outputs the bot's command, creating a unique blend of strategy, language, and AI-driven gameplay.

**BatLLM offers several modes of play:**

- Compete against your friends by each entering prompts and controlling your own bot.
- Challenge yourself in solo mode against an LLM-powered bot.
- Watch fully autonomous battles where both bots are controlled by LLMs and guided by your predefined prompts.

![](https://avatars.githubusercontent.com/u/349947?s=80&v=4)

krahdJul 25, 2025

edit the description noting the following:

1. the goal of BatLLM is to create a tool where people can practice controlling LLMs and develop an intuition of what they can do and what the cannot do, and to hone their skills in prompting and interacting with ai. I want to help people use AI (LLMs) in an efficient and informed way without having to learn the technical details of the underlaying technologies.
    
2. the game has been designed and developed by me, Tomas Laurenzo (Associate Professor, CU Boulder), and is open source and free etc.
    
3. It has been tested with Ollama running llama3.2:latest models locally on a M1 macbook pro and the performance is very good. However, it is model-agnostic, it's just a matter of configuration.
    
4. The game admits different variations, prompt augmentation on/off, and separate llms / one model only. A match ends when a bot dies or when it's over. A match consists of a secuence of rounds, each round consists of a secuence of turns. in Each turn the prompts for the current round are sent to the llms, their response processed and executed by the bots.
    

When the prompts are augmented, BatLLM adds a description of the game and all the relevant info (position, rotation, health, shield of both bots, plus game data like round#, turn#) and then appends the player's prompt. If augmentation is off the users' prompts are sent as-is and the llm has no extra information.

Additionally, the game can employ two independent llms (one per bot) or a single one that answers to both bots.

5. as of now it runs locally but porting it so that is online, with a larger arena and more bots should not be too hard.
    
6. While it uses kivy, the arena uses NormalizedCanvas with relative coordinates (0,0 tbeing top left and 1,1 bottom right) to make it easier to improve the game's graphics, specially if you are used to creative coding frameworks.
    
7. there is a lot of room for improvement, all help is welcome
    
8. the
    
9. the game has different options
    

![OpenAI logo](https://github.com/images/modules/marketplace/models/families/openai.svg)

OpenAI GPT-4.1Jul 25, 2025

Certainly! Here is a revised and comprehensive description section for your `README.md` that incorporates all your points clearly and concisely:

---

# BatLLM: Practice LLM Control Through Bot Battles

**BatLLM** is an open-source, turn-based battle game that lets you experiment with and master language model prompting by controlling in-game bots through locally running LLMs (Large Language Models). BatLLM provides a hands-on, creative way to discover both the strengths and limitations of AI models—no need to learn the underlying technical details.

**Goal:**  
BatLLM was created to help people develop an intuitive understanding of LLMs, learn effective prompting strategies, and interact with AI more efficiently and confidently. It is designed as both a playful and practical tool for exploring prompt engineering, LLM behaviors, and AI-driven interaction.

**About:**  
BatLLM was designed and developed by **Tomas Laurenzo** (Associate Professor, CU Boulder). It is free, open source, and welcomes contributions from the community.

**Tested and Model-Agnostic:**  
BatLLM has been tested with [Ollama](https://ollama.ai/) running the `llama3.2:latest` models locally on an M1 MacBook Pro, with very good performance. However, the system is model-agnostic—simply configure it to point at your preferred local LLM endpoint.

---

## Game Highlights

- **Practice Prompting Skills:** Hone your ability to guide and control LLMs by crafting prompts that direct your bot’s actions in battle.
- **Multiple Modes & Configurations:**
    - Play human vs. human, human vs. LLM, or LLM vs. LLM (fully autonomous).
    - Supports separate LLMs per player, or both bots can use the same model.
    - Supports “prompt augmentation” (auto-includes structured game state in prompts) or pure/raw user prompts for maximum flexibility.
- **Flexible Battle Structure:**
    - Matches consist of rounds; rounds consist of turns.
    - In each turn, the system sends the round's prompt(s) to the LLM(s), interprets the responses as bot commands, and updates the arena.
    - A match ends when a bot is destroyed or the session is over.
- **Prompt Augmentation:**
    - When enabled, BatLLM adds a description of the game plus all relevant state info (positions, health, shield, round/turn data) before the user’s prompt.
    - When off, the player prompt is sent as-is to the LLM, placing all responsibility for context on the user.
- **Arena & Graphics:**
    - Uses [Kivy](https://kivy.org) & a `NormalizedCanvas` (all coordinates normalized from (0,0) at the top-left to (1,1) at the bottom-right), making graphics improvements or integration with creative coding frameworks straightforward.
- **Ready for Expansion:**
    - Runs locally for now, but designed to be easily ported for online play, larger arenas, and more bots.

---

## Collaboration

**BatLLM is a growing, evolving project and all help is welcome!**  
There's plenty of room for improvement—and contributions of code, playtesting, feature ideas, or documentation are warmly invited.

---

**Play. Practice. Learn how to prompt, and see what AIs can (and cannot) do!**

---

_(Detailed gameplay instructions, options, and command references follow in the full README.)_

![](https://avatars.githubusercontent.com/u/349947?s=80&v=4)

krahdJul 25, 2025

there is only human vs human, albeit always mediated by llm. Please generate the complete readme.md, do revisit the source code to improve and expand your docummentation. use all my previous prompts as well.

![OpenAI logo](https://github.com/images/modules/marketplace/models/families/openai.svg)

OpenAI GPT-4.1Jul 25, 2025

## Chat error message

The response was filtered due to the prompt triggering Azure OpenAI's content management policy. Please modify your prompt and retry. To learn more about our content filtering policies please read our documentation: https://go.microsoft.com/fwlink/?linkid=2198766

![](https://avatars.githubusercontent.com/u/349947?s=80&v=4)

krahdJul 25, 2025

there is only human players, there are no autonomouse players. players always compete mediated by the llm that controls the bots.Please generate the complete documentation for this project in markup, do revisit the source code to improve and expand your docummentation. use all my previous prompts as well.

![OpenAI logo](https://github.com/images/modules/marketplace/models/families/openai.svg)

OpenAI GPT-4.1Jul 25, 2025

## Chat error message

The response was filtered due to the prompt triggering Azure OpenAI's content management policy. Please modify your prompt and retry. To learn more about our content filtering policies please read our documentation: https://go.microsoft.com/fwlink/?linkid=2198766

![](https://avatars.githubusercontent.com/u/349947?s=80&v=4)

krahdJul 25, 2025

ere is only human players, there are no autonomouse players. players always compete mediated by the llm that controls the bots. Please generate the most complete posible documentation for this project, specially its readme.md file

![OpenAI logo](https://github.com/images/modules/marketplace/models/families/openai.svg)

OpenAI GPT-4.1Jul 25, 2025

Certainly! Here is a **comprehensive, detailed README.md** for the [BatLLM](https://github.com/krahd/BatLLM) project, tailored for clarity, completeness, and ease of onboarding. This documentation is based on your description, code analysis, and best documentation practices.

---

# BatLLM: Human-vs-Human LLM-Powered Bot Battle Game

**BatLLM** is a two-player, turn-based battle game that uniquely leverages local Large Language Models (LLMs) as mediators: each player guides their bot by crafting prompts, and the LLM interprets the game state and prompt to generate the bot's command. BatLLM is designed to help people practice controlling LLMs, hone their prompting skills, and build an intuitive understanding of what LLMs can and cannot do—all without needing to learn the technical details of the underlying technologies.

---

## Table of Contents

- [Project Goals](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#project-goals)
- [About the Author](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#about-the-author)
- [Features](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#features)
- [Game Overview](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#game-overview)
- [Game Modes and Variations](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#game-modes-and-variations)
- [Prompt Augmentation](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#prompt-augmentation)
- [Bot Command Reference](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#bot-command-reference)
- [Game Flow](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#game-flow)
- [Installation and Setup](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#installation-and-setup)
- [Usage](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#usage)
- [Configuration](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#configuration)
- [System Requirements](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#system-requirements)
- [Technical Notes](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#technical-notes)
- [Contributing](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#contributing)
- [License](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#license)
- [Acknowledgments](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#acknowledgments)
- [FAQ](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#faq)

---

## Project Goals

BatLLM is designed as a tool for:

- **Practicing LLM Control:** Experiment with prompts and observe how LLMs interpret and execute them.
- **Developing Prompting Intuition:** See firsthand the strengths and weaknesses of LLMs in understanding and acting on your instructions.
- **Democratizing AI Skills:** Enable anyone to interact with advanced language models in a fun, accessible way—no AI or programming expertise required.

---

## About the Author

BatLLM was designed and developed by **Tomas Laurenzo**, Associate Professor at CU Boulder. The project is open source and free to use, improve, and share.

---

## Features

- **Human-vs-Human Only:** All players are humans; there are no AI/autonomous players. Every action is mediated by an LLM based on each human player's prompt.
- **Prompt-Driven Gameplay:** Players write prompts to guide their bots, with the LLM translating these into in-game actions.
- **Local LLM Integration:** Works out-of-the-box with [Ollama](https://ollama.ai) and the `llama3.2:latest` model (tested on M1 MacBook Pro), but is model-agnostic and configurable.
- **Prompt Augmentation:** Optional feature that structures and augments the prompt sent to the LLM with game state info for improved control and transparency.
- **Configurable LLM Mediation:** Supports two separate LLMs (one per player) or a single shared LLM.
- **Intuitive Arena Graphics:** Uses [Kivy](https://kivy.org) with a normalized coordinate system for easy customization and creative coding.
- **Modular and Extensible:** Clean, well-documented code ready for expansion (e.g., online play, larger arenas, more bots).

---

## Game Overview

BatLLM is a two-player competitive game where each player controls a bot by writing prompts. The prompt is sent to an LLM, which, given the current game state and the prompt, returns a command for the bot. The goal is to destroy the opposing bot by reducing its health to zero through movement, rotation, shielding, and shooting.

**Key Points:**

- Each player enters a prompt per round.
- Each bot executes commands as interpreted by its LLM.
- The arena and bot states are visualized via a Kivy-based interface.
- The match ends when one bot is destroyed.

---

## Game Modes and Variations

- **Standard Mode:** Each player writes a prompt; both prompts are sent to their respective LLMs each round.
- **Prompt Augmentation:** Optionally, the game augments the player's prompt with structured game state info.
- **LLM Assignment:**
    - _Separate LLMs_: Each player’s prompt goes to a different LLM instance.
    - _Single LLM_: Both prompts are handled by a single LLM (useful for experimentation or hardware constraints).

**Note:** There are no fully autonomous or LLM-vs-LLM modes. All gameplay is human-vs-human, mediated by LLMs.

---

## Prompt Augmentation

- **Enabled:** BatLLM prepends the player's prompt with a detailed description of the game state (positions, rotations, shields, health, round/turn numbers, etc.), ensuring the LLM has all the context it needs.
- **Disabled:** Only the raw player prompt is sent to the LLM; players must provide all necessary context themselves.

**Example of an Augmented Prompt:**

Code

```
You are an expert gamer. Your task is to control a bot in BatLLM, a two-player battle game where an LLM like you controls a bot. You receive information about the game state and a prompt written by the human player that guides your behaviours.

Game State:
Round: 3, Turn: 2
Your Bot - x:0.5 y:0.2 a:90 s:1 h:10
Opponent Bot - x:0.7 y:0.8 a:270 s:0 h:8

Player Prompt:
Try to dodge the next bullet, then retaliate when the enemy's shield is down.
```

---

## Bot Command Reference

Bots can execute the following commands as generated by the LLM (any other output is ignored):

|Command|Action|Example|
|---|---|---|
|`Cd`|Rotate **clockwise** by `d` degrees|`C20`|
|`Ad`|Rotate **anticlockwise** by `d` degrees|`A90`|
|`M`|Move forward one step (`STEP_LENGTH`)|`M`|
|`S1`|Raise shield (remains up until changed)|`S1`|
|`S0`|Lower shield (remains down until changed)|`S0`|
|`S`|Toggle shield (raise if down, lower if up)|`S`|
|`B`|Fire bullet forward (only if shield is down)|`B`|

**Notes:**

- Bullets are resolved immediately; the opponent bot cannot move while a bullet is in play.
- Shields protect only the front arc (±`SHIELD_SIZE` degrees).
- If a bot is hit and shield is down (or not facing the shot), health decreases by `BULLET_DAMAGE`.

---

## Game Flow

A match consists of rounds; each round consists of turns.

1. **Before the Round:**  
    Both players enter a prompt (influencing their LLM-mediated bot).
    
2. **During Each Turn:**
    
    - The game randomly selects which player goes first.
    - For each turn:
        - The prompt (augmented or raw) is sent to the LLM.
        - The LLM returns a command.
        - The command is executed by the bot in the game world.
        - The game state is updated and visualized.
3. **End of Round/Match:**
    
    - If a bot’s health reaches zero, the match ends.
    - Otherwise, a new round begins and players can input new prompts.

---

## Installation and Setup

### Requirements

- Python 3.8+ (tested with Python 3.11)
- [Kivy](https://kivy.org) for graphics/UI
- [Ollama](https://ollama.ai/) (or other local LLM with compatible API)
- (Optionally) Other local LLM servers for experimentation

### Installation

1. **Clone the repository:**
    
    bash
    

- ```
    git clone https://github.com/krahd/BatLLM.git
    cd BatLLM
    ```
    
- **Install Python dependencies:**
    
    bash
    
- ```
    pip install -r requirements.txt
    # Or manually: pip install kivy requests
    ```
    
- **Install and run Ollama (or your LLM of choice):**
    
    - [Ollama installation guide](https://ollama.ai/download)
    - Start a model, e.g.:
        
        bash
        

1. - ```
        ollama run llama3.2:latest
        ```
        

---

## Usage

Run the game with:

bash

```
python batllm.py
```

- Follow the on-screen instructions to enter your prompts and watch the battle unfold!
- For advanced usage, see [Configuration](https://github.com/marketplace/models/azure-openai/gpt-4-1/playground?prompt=Analyze%20the%20repository%20https%3A%2F%2Fgithub.com%2Fkrahd%2FBatLLM%20and%20generate%20a%20comprehensive%20documentation%20for%20its%20readme.md%20#configuration).

---

## Configuration

BatLLM can be configured via `config.py` or command-line arguments (if implemented):

- **LLM Endpoints:** Set the URLs for each player's LLM (can be the same or different).
- **Prompt Augmentation:** Toggle augmentation on/off.
- **Arena Settings:** Adjust arena size, step length, bullet damage, shield size, etc.

Example config snippet (from `config.py`):

Python

```
LLM_ENDPOINTS = [
    "http://localhost:11434/api/generate",  # Player 1
    "http://localhost:11435/api/generate"   # Player 2 (or same as above)
]
PROMPT_AUGMENTATION = True
INITIAL_HEALTH = 10
BULLET_DAMAGE = 2
SHIELD_SIZE = 60  # degrees
```

---

## System Requirements

- Works on macOS, Linux, and Windows (tested on macOS M1).
- Requires a local LLM server (tested with Ollama/llama3.2:latest, but model-agnostic).
- Graphics use Kivy with normalized coordinates for easy extensibility.

---

## Technical Notes

- **Arena Rendering:** Uses Kivy’s `NormalizedCanvas`—all positions are floats from 0.0 (top/left) to 1.0 (bottom/right).
- **LLM Communication:** Uses REST API (`requests.post`), sending prompts and parsing LLM responses as plain text.
- **Game Logic:** Modular and easy to expand for online play, more bots, or richer mechanics.
- **Performance:** Excellent on M1 MacBook Pro; actual performance depends on LLM and hardware.

---

## Contributing

**BatLLM is a growing project and contributions are welcome!**

- Fork the repo, make your changes, and submit a pull request.
- Feature suggestions, bug reports, and playtesting feedback are encouraged.
- Improvements to UI, game mechanics, prompt templates, and documentation are all appreciated.

---

## License

This project is licensed under the [MIT License](https://github.com/marketplace/models/azure-openai/gpt-4-1/LICENSE).

---

## Acknowledgments

- Designed and developed by [Tomas Laurenzo](https://tomaslaurenzo.com/), Associate Professor, CU Boulder.
- Inspired by creative coding, AI, and the power of language models.

---

## FAQ

**Q: Can I play against an AI or fully autonomous LLM?**  
A: No, BatLLM is strictly human-vs-human; all actions are mediated by LLMs interpreting human prompts.

**Q: What LLMs can I use?**  
A: Any local LLM with a compatible API, such as Ollama. The system is model-agnostic.

**Q: Can I run this online or with more bots?**  
A: Not yet, but the codebase is designed for easy expansion to online play and more complex arenas.

**Q: How does prompt augmentation help?**  
A: It provides structured, explicit context to the LLM, making its command generation more reliable and interpretable.

**Q: How can I improve the graphics?**  
A: The arena uses normalized coordinates and Kivy, so creative coding or graphic improvements are straightforward.

---

## Play. Prompt. Learn.

_Build your prompting intuition and master AI mediation—one battle at a time!_