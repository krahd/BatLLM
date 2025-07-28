
```
![alt text](https://github.com/krahd/BatLLM/blob/e3d2fbbd7c3f2837a3fed7c0c8808172dc7eee82/docs/images/logo-small.png "BatLLM")
```
# BatLLM
*What we do not understand we do not posses* - Goethe.

> [! NOTE] 
>**[Documentation](DOCUMENTATION.md)  &mdash; [User Guide](USER_GUIDE.md)  &mdash; [Software](SOFTWARE.md) &mdash; [Contributing](CONTRIBUTIN%20c1.md)  &mdash; [FAQ](FAQ.md)  &mdash; [Credits](CREDITS.md)**


**BatLLM** is an open-source, two-player, turn-based battle game with a twist: instead of interacting directly with the game, players must use an AI model to interact on their behalf. 

Designing the best strategy is not enough to win, players also need to communicate effectively with their AI. During a match, players can submit prompts, see the results and improve their process. 

By combining language, strategy, and AI-driven gameplay, **BatLLM** offers a safe, engaging, and hands-on way to explore and understand the capabilities and limitations of AI. 

**In a world increasingly shaped by AI, and marked by profound asymmetries of power, knowledge, and access, developing critical and practical AI literacy is both urgent and necessary.**

**BatLLM** aims to support a broader social understanding of AI by fostering intuitive, experiential learning, hopefully helping players to build practical prompting skills while also encouraging reflection on the assumptions, processes, and power dynamics embedded in generative AI systems.

This document provides a rather superficial overview of the project. To know more about **BatLLM**, its objectives and technical details, please refer to the [[#BatLLM|main documentation files]].

> [! NOTE!]
> **BatLLM** was developed as part of a project supported by the [2024 Arts & Humanities Grant Program](https://www.colorado.edu/researchinnovation/2024/05/03/seventeen-arts-humanities-projects-receive-grants-advance-scholarship-research-and) of the [Research & Innovation Office](https://www.colorado.edu/researchinnovation/) at the University of Colorado Boulder.



## Quick Start

### System Requirements

1. **Python:** 3.8 or higher. Python 3.11 is recommended. 

2. **Operating System:** It should work everywhere but it has only been tested on an Apple laptop with an M1 and MacOS 15.5. 

 3. **Hardware:** While BotLLM itself is extremely light, either the same computer or any other accessible directly via http must be able to run the desired LLM models locally.  

### Models

As of now, BatLLM needs to be able to prompt two LLMs using POST. Everything, most importantly the GUI, assumes that players and LLMs share a single machine.

BatLLM does not care about the local architecture. All it needs is two local endpoints to post queries to the LLM. That said, the easiest way to have a running environment is to use [Ollama](https://ollama.com/) to install and run [llama3.2:latest](https://ollama.com/library/llama3.2), on a mac computer.

With [Homebrew](https://formulae.brew.sh/formula/ollama), installing Ollama on a mac means executing `brew install ollama`. After installing Ollama, you can download the model with `ollama pull llama3.2:latest` (it takes a little bit to download but you only do it once).

To control the models you may run the scripts `start_ollamas.sh` and `stop_ollamas.sh` in the project's root. 

### Installation

To run **BatLLM** on your computer you must download the project and run it using Python. To achieve this you may:

**Clone this repository, create and activate a Python virtual environment. Install the project requirements using PIP.
```bash
git clone https://github.com/krahd/batllm.git
cd batllm
python -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
pip install -o requirements.txt
```
 
**Start two Ollama instances each one running one LLM:**
```bash
./start_ollamas.sh
```

**Use python to start BatLLM:**
```bash
python src/main.py
```

To stop the Ollama instances you may run:
```bash
./stop_ollamas.sh
```

### How to Play

For a better explanation of the game –including the Bot commands reference– please read the [User Guide](USER_GUIDE.md)

**A super compressed explanation:** Each match is divided into rounds. At the start of every round, players submit prompts that guide their AI-controlled bots for the duration of that round. To win, players need to both come up with a winning strategy and figure out ways to make the AI follow it correctly, solely by feeding it well-crafted prompts.

Each player has a text bot where they can add prompts to their collection. After both players click on their corresponding submit button, BatLLM gathers the current text in the player's text field and uses that text as prompt.

In addition, you may use the buttons at the bottom right to change some of BatLLM's options, to start a new game, or to save the information of the current execution of BatLLM as a JSON file.

> [! NOTE]  
> **[Readme](README.md) &mdash; [Documentation](docs/DOCUMENTATION.md)  &mdash; [User Guide](docs/USER_GUIDE.md)  &mdash; [Contributing](docs/CONTRIBUTIN%20c1.md)  &mdash; [docs/FAQ](FAQ.md)  &mdash; [docs/Credits](CREDITS.md)**
