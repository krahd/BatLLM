 
>
>  ![BatLLM's logo](./images/logo-small.png) **[Readme](README.md) &mdash; [Documentation](DOCUMENTATION.md)  &mdash; [User Guide](USER_GUIDE.md)  &mdash; [Contributing](CONTRIBUTING.md)  &mdash; [FAQ](FAQ.md)  &mdash; [Credits](CREDITS.md)** 
>
>

## FAQ

**Q: Is BatLLM a serious LLM benchmark or inference engine?**  
A: No: it's an *experimental education game* project themed for creative prompt interaction with LLM-powered bots.

**Q: Can I use ChatGPT or a another model as the LLM?**  
A: It is designed for local LLMs (Ollama, Llama.cpp servers etc.), but any language model with compatible API/CLI could be adapted. Check the  [User Guide](USER_GUIDE.md)  for more information on this topic.

**Q: Can the LLM cheat or see hidden information?**  
A: It depends on the playing mode chosen. Players can either share a single LLM or use two completely isolated ones. The current mode can be changed in the Settings screen.

**Q: Can I play against an AI or fully autonomous LLM?**
A: No, BatLLM is strictly human-vs-human; all actions are mediated by LLMs interpreting human prompts.

**Q: Can I run this online or with more bots?**
A: Not yet, but the codebase is designed for easy expansion to online play and more complex arenas.  

**Q: How does prompt augmentation help?**
A: It provides structured, explicit context to the LLM, making its command generation more reliable and interpretable.

**Q: How can I improve the graphics?**
A: The arena uses normalized coordinates and Kivy, so creative coding or graphic improvements should be quite straightforward.

**Q: Can I play BatLLM over the internet or do both players have to be at the same computer?**
A: Right now, both players share one screen on a single computer, so typically you’d be in the same room taking turns typing prompts. There’s no built-in network play yet. You could use screen-sharing as a workaround, but an online mode is something for the future.

**Q: Is there a way to play single-player (against an AI)?**
A: Not yet. When (or if) we get better at prompting, then adding autonomous AI would be immediate. 

**Q: The LLM sometimes outputs something like "I move forward (M)" and my bot does nothing. Why?**
A: The game only understands the very specific command format (e.g., exactly "M" to move). If the model’s output isn’t exactly one of the commands (possibly with a parameter), the command will be ignored as unrecognized. As a player, you *will* need to tweak your prompt to get a direct answer. For example, saying something like *"Output just the command you will execute, no explanation."* may help in your prompt. 

**Q: How does prompt augmentation actually improve gameplay?**
A: It only does if your prompt allows the LLM to process the information and still output a valid command. With augmentation on, the model gets a structured dump of the game state every turn. This means it doesn’t have to rely on memory of previous turns (which it might not have, since each turn’s prompt is separate) or on the player describing the state, which may lead to more relevant and valid commands. Without augmentation, the model might not know where the enemy is or that its health is low, etc., unless the player explicitly writes that in the prompt. 

Augmentation may make the game more about strategy (“what high-level instruction do I give the bot”) and less about manual bookkeeping. 

Both modes of playing, with our without augmentation are exercises in prompt engineering, as you must manage the AI’s behaviour carefully and craftully.

**Q: Can I modify the game to have more than 2 players or different arenas?**
A: The code is written with some consideration to these potential paths. However, there are several places where it has been assumed that there are only two players (i.e. the GUI). In any case, they would not be anytime soon.

**Q: My model is taking a long time to respond or times out. What can I do?**
A: Smaller or quantized models will respond faster. If using Ollama, ensure the model is running properly. The game sets a timeout of 30 seconds for the LLM response; if it’s too slow, the turn might effectively be skipped. You can increase the timeout in code (Bot.submit\_prompt\_to\_llm).

*More coming soon...*



