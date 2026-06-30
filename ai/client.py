import groq
import time

class AIClient:
    def __init__(self, config):
        self.config = config
        self.groq_client = groq.Groq(api_key=config['api']['groq_key'])
        # Gemini setup similarly
    
    def get_response(self, question, history, screen_context=None, system_instruction=None):
        """Streaming response from Groq preferred."""
        if system_instruction:
            system_prompt = system_instruction
        else:
            system_prompt = f"""You are an elite real-time QnA assistant... 
Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}. Stay helpful."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        if screen_context:
            messages.append({"role": "user", "content": f"Screen context: {screen_context}"})
        messages.append({"role": "user", "content": question})
        
        try:
            # Groq call with streaming
            stream = self.groq_client.chat.completions.create(
                model=self.config['api']['model'],
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                stream=True
            )
            response = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    response += chunk.choices[0].delta.content
                    # Could update UI incrementally
            return response
        except Exception as e:
            # Fallback to Gemini
            return f"Fallback response: Groq API failed ({str(e)}). Implement Gemini."