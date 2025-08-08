import requests
import json
import time
from kivy.network.urlrequest import UrlRequest


class ConversationPrompter:

    def submit_prompt_to_llm(self, prompt):                              
        self.data["prompt"] = prompt
                
        UrlRequest(
            url = "localhost:6767",  # TODO get this from config
            req_body = json.dumps(self.data), 
            req_headers = self.headers,
            on_success = self._on_llm_response,
            on_failure = self._on_llm_failure,   # HTTP errors 4xx, 5xx
            on_error = self._on_llm_error,     # other errors (no connection, etc.)
            timeout = 30,
            method = 'POST'
        )
        
        
    def _on_llm_failure(self, request, error):
        """Error handler for HTTP errors 4xx, 5xx

        Args:
            request (_type_): the request objevt
            error (_type_): the error obtained
        """        
        
        print(f"LLM request failed: {error}")                
        
        
    def _on_llm_error(self, request, error):
        """Error handler for errors outside the web protocol (no connection, etc)

        Args:
            request (_type_): the request object
            error (_type_): the error obtained
        """        
            
        print(f"Error during LLM request: {error}")                 
        

                               
    def _on_llm_response(self, req, result):
        response = result.get("response", "").strip()  
        print (f"\n\n{response}\n\n")
        
        if user_input != "---":            
            self.submit_prompt_to_llm(user_input)
        

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}    
        self.data = {
            "model": "llama3.2:latest",  # TODO get this from config
            "prompt": "",
            "stream": False # TODO get this from config
        }


    def conversation_turn(self):
        
        print("OK\n")

    
        user_input = input("")
        



if __name__ == "__main__":
    print ("Enter prompts and wait for answers. Enter '---' to exit.\n")
    prompter = ConversationPrompter()
    prompter.conversation_turn()
