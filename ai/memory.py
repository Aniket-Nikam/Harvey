class ConversationMemory:
    def __init__(self):
        self.history = []
        self.contexts = []
    
    def add_exchange(self, question, response):
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": response})
        if len(self.history) > 20:  # Keep recent
            self.history = self.history[-20:]
    
    def get_history(self):
        return self.history
    
    def add_context(self, context):
        self.contexts.append(context)
    
    def get_latest_context(self):
        return self.contexts[-1] if self.contexts else None