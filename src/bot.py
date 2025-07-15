from math import cos, sin

class bot:
    promtp_history = []
    current_prompt = None    
    llm_endpoint= "http://localhost:5000"  # Example LLM endpoint
    augment_prompts = True  # Whether to augment prompts with additional context
    x, y = 0, 0  # Coordinates for the bot's position in the game
    r = 0  # Rotation angle for the bot
    shield = False  # Whether the bot has an active shield
    health = 100  # Health of the bot
    step = 10  # Step size for movement
    
    
    
    def __init__(self):
        self.prompt_history = []
        self.current_prompt = None
        self.llm_endpoint = "http://localhost:5000"
        self.augment_prompts = True
        self.x = 0
        self.y = 0
        self.r = 0
        self.shield = False
        self.health = 100       
        self.step = 10
    def move(self):
        # Logic to move the bot
        self.x += self.step * cos(self.r)
        self.y += self.step * sin(self.r)
        print(f"Bot moved to position: ({self.x}, {self.y})")   

    