from math import cos, sin

class bot:
    id = None
    prompt_history = None
    prompt_history_index = None
    prompt = None    
    llm_endpoint = None
    augment_prompts = None
    x = None
    y = None
    r = None
    shield = None
    health = None
    step = None
    
    
    
    def __init__(self, id):
        self.id = id
        self.prompt_history = [] 
        self.prompt_history_index = 0
    
        self.current_prompt = None
        self.llm_endpoint = "http://localhost:5000"
        self.augment_prompts = False
        
        
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


    def submit_prompt(self, new_prompt):
        self.prompt_history.append(new_prompt)
        self.prompt_history_index = len(self.prompt_history) - 1
        self.prompt = new_prompt

        print ("********** Submitting prompt **********")
        print (new_prompt)
        print ("********** End of prompt **********")

        
        
    def rewind_prompt_history(self):
        if self.prompt_history_index is not None and self.prompt_history_index > 0:
            self.prompt_history_index -= 1            
            print(f"Rewound to prompt: {self.prompt_history_index}")

    def forward_prompt_history(self):
        if self.prompt_history_index is not None and self.prompt_history_index < len(self.prompt_history) - 1:
            self.prompt_history_index += 1                        
            print(f"Forwarded to prompt: {self.prompt_history_index}")

    def get_current_prompt_history(self):
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
        
        return res
    
    def copy_prompt_history(self):
        res = ""
        try:        
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
            
        self.prompt = res

        
    def get_prompt(self):
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""
        return res