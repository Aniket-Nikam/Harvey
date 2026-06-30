#!/usr/bin/env python3
"""
Harvey - Real-time AI for screen-shared meetings.
Production-grade, low-latency, user-only visibility.
"""

import os
import sys
import time
import threading
import yaml
from pynput import keyboard as pynput_keyboard
import logging
from dotenv import load_dotenv
from pathlib import Path

# Import modules
from audio.listener import AudioListener
from audio.processor import AudioProcessor
from display.window_manager import AssistantWindow
from display.share_safe import ShareSafeManager
from stealth.detector import ScreenShareDetector
from ai.client import AIClient
from ai.memory import ConversationMemory
from vision.capture import ScreenCapturer
from utils.helpers import setup_logging, get_timestamp

class StealthQnAAssistant:
    def __init__(self):
        load_dotenv()
        self.config = self.load_config()
        self.config['api']['groq_key'] = os.environ.get("GROQ_API_KEY", self.config['api'].get('groq_key', ''))
        
        setup_logging(self.config['general']['log_level'])
        self.logger = logging.getLogger(__name__)  # assume setup
        
        # Setup crash logging for main thread and child threads
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            self.logger.critical("Uncaught exception in main thread", exc_info=(exc_type, exc_value, exc_traceback))

        def handle_thread_exception(args):
            self.logger.critical("Uncaught exception in background thread", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

        sys.excepthook = handle_exception
        threading.excepthook = handle_thread_exception
        
        self.memory = ConversationMemory()
        self.ai_client = AIClient(self.config)
        self.detector = ScreenShareDetector(self.config)
        self.share_safe = ShareSafeManager(self.config)
        self.window = AssistantWindow(self.config, self.share_safe)
        self.audio_listener = AudioListener(self.config)
        self.audio_processor = AudioProcessor(self.config, self.memory)
        self.screen_capturer = ScreenCapturer(self.config)
        
        self.running = True
        self.is_sharing = False
        
        # Setup Auto-Pilot state
        self.autopilot_running = False
        self.autopilot_stop_event = threading.Event()
        self.window.autopilot_callback = self.toggle_autopilot
        self.window.clear_callback = self.clear_conversation_memory
        
        # Setup hotkeys and connect trigger callback
        self.window.trigger_callback = self.run_mode_action
        self.setup_hotkeys()
        
        self.logger.info("Harvey initialized.")
        self.window.show_message("=== Harvey Initialized ===\n"
                                 f"• F2: Listen to Meeting Partner (Loopback)\n"
                                 f"• F3: Listen to Yourself (Microphone)\n"
                                 f"• F4: Capture Screen Context (Local OCR)\n"
                                 f"• F5: Run Active Mode (From settings panel)\n"
                                 "========================================\n")
    
    def load_config(self):
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_hotkeys(self):
        try:
            hotkey_map = {
                f"<{self.config['hotkeys']['listen_other'].lower()}>": lambda: self.run_mode_action("listen_other"),
                f"<{self.config['hotkeys']['listen_self'].lower()}>": lambda: self.run_mode_action("listen_self"),
                f"<{self.config['hotkeys']['screen_capture'].lower()}>": lambda: self.run_mode_action("screenshot"),
                "<f5>": lambda: self.run_mode_action(self.window.mode_var.get())
            }
            self.hotkey_listener = pynput_keyboard.GlobalHotKeys(hotkey_map)
            self.hotkey_listener.start()
            self.logger.info("Single-key global hotkeys bound successfully.")
        except Exception as e:
            self.logger.error(f"Failed to bind hotkeys: {e}")
    
    def run_mode_action(self, mode):
        # Update the UI selection radio buttons to match the trigger action
        self.window.root.after(0, lambda: self.window.mode_var.set(mode))
        
        if mode == "screenshot":
            threading.Thread(target=self.capture_screen_context, daemon=True).start()
        elif mode == "listen_other":
            threading.Thread(target=self.process_audio_query, args=(True,), daemon=True).start()
        elif mode == "listen_self":
            threading.Thread(target=self.process_audio_query, args=(False,), daemon=True).start()
            
    def capture_screen_context(self):
        self.window.show_message("Capturing screen for context...")
        
        # Hide window temporarily to avoid feedback loop (reading itself)
        self.window.hide()
        # Allow Windows Desktop Manager a brief moment to redraw the screen underneath
        time.sleep(0.15)
        
        try:
            screenshot = self.screen_capturer.capture()
        finally:
            # Always restore the window, even if capture fails
            self.window.show()
            
        if not screenshot:
            self.window.show_message("Failed to capture screen.")
            return
            
        context = self.screen_capturer.analyze(screenshot)
        if "Failed to analyze" in context or "OCR Error" in context or "Failed to run local OCR" in context or "No screen content" in context:
            self.window.show_message(context)
            return
            
        self.memory.add_context(context)
        self.window.show_message("Screen context added.")
        self.window.show_message("AI analyzing screen content...")
        
        try:
            # Read styles and word limits dynamically from UI
            style = self.window.style_var.get()
            word_limit = self.window.words_var.get()
            
            system_instruction = (
                "You are Harvey, an expert real-time assistant for developers and presenters.\n"
                "Your task is to analyze the screen content and solve, answer, or explain any questions or code visible on the screen.\n"
                f"Answering Style: {style}\n"
                f"Word Limit: Max {word_limit} words. Be highly precise, direct, and concise."
            )
            
            response = self.ai_client.get_response(
                question="Please analyze the screen context and provide answers, solutions, or summaries for any questions or code visible on the screen.",
                history=self.memory.get_history(),
                screen_context=context,
                system_instruction=system_instruction
            )
            self.memory.add_exchange("[Screen Capture Query]", response)
            self.window.display_qa("Screen Context", "Local OCR Capture", response)
        except Exception as e:
            self.logger.error(f"Error analyzing screen independently: {e}")
            self.window.show_message("Error analyzing screen content.")
    
    def process_audio_query(self, is_other=True):
        """Main pipeline: listen, transcribe, AI respond, display."""
        try:
            mode_desc = "Partner (Loopback)" if is_other else "Self (Microphone)"
            duration = self.window.duration_var.get()
            self.window.show_message(f"Listening to {mode_desc} for {duration}s...")
            
            if is_other:
                # Capture system audio loopback
                audio_data = self.audio_listener.listen_for_question(duration=duration)
            else:
                # Capture microphone audio
                audio_data = self.audio_listener.listen_via_microphone(duration=duration)
                
            if audio_data is None:
                self.window.show_message("No audio detected.")
                return
                
            self.window.show_message("Transcribing audio...")
            transcription = self.audio_processor.transcribe(audio_data)
            if not transcription or not transcription.strip():
                self.window.show_message("Could not transcribe speech.")
                return
                
            self.window.show_message("Generating AI response...")
            
            # Read styles and word limits dynamically from UI
            style = self.window.style_var.get()
            word_limit = self.window.words_var.get()
            
            system_instruction = (
                "You are Harvey, an expert real-time assistant for developers and presenters.\n"
                "Your primary task is to solve, answer, or explain the user's SPEECH QUERY directly.\n"
                "The 'Screen Context' contains text/code extracted from their display. Use it ONLY as supporting background if the user explicitly asks about what is on their screen.\n"
                "If the speech query is unrelated to the screen context (or if the screen context is an old error message and the user is speaking about a business/different topic), IGNORE the screen context entirely.\n"
                "Do not reference screen context errors or mention them unless the speech query is about them.\n"
                f"Answering Style: {style}\n"
                f"Word Limit: Max {word_limit} words. Be highly precise, direct, and concise."
            )
            
            screen_ctx = self.memory.get_latest_context()
            response = self.ai_client.get_response(
                question=f"User Speech Query: {transcription}\nProvide the solution/answer matching this query.",
                history=self.memory.get_history(),
                screen_context=screen_ctx,
                system_instruction=system_instruction
            )
            
            self.memory.add_exchange(transcription, response)
            self.window.display_qa(mode_desc, transcription, response)
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            self.window.show_message("Error processing query. Please try again.")
    
    def monitor_sharing(self):
        """Background thread to detect screen sharing and transition stealth mode states."""
        while self.running:
            sharing_active = self.detector.is_screen_sharing_active()
            if sharing_active != self.is_sharing:
                self.is_sharing = sharing_active
                if self.is_sharing:
                    self.share_safe.activate_stealth_mode(self.window)
                else:
                    self.share_safe.deactivate_stealth_mode(self.window)
            time.sleep(2)  # Check every 2s
    
    def run(self):
        self.window.show()
        # Force mapping of tkinter window so HWND is fully initialized before thread runs
        try:
            self.window.root.update()
        except Exception as e:
            self.logger.error(f"Failed to update window: {e}")
            
        monitor_thread = threading.Thread(target=self.monitor_sharing, daemon=True)
        monitor_thread.start()
        
        try:
            self.window.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.cleanup()
    
    def toggle_autopilot(self, enabled):
        if enabled:
            if not self.autopilot_running:
                self.autopilot_running = True
                self.autopilot_stop_event.clear()
                threading.Thread(target=self.run_autopilot_loop, daemon=True).start()
                self.window.show_message("Auto-Pilot Mode enabled.")
        else:
            if self.autopilot_running:
                self.autopilot_running = False
                self.autopilot_stop_event.set()
                self.window.show_message("Auto-Pilot Mode disabled.")

    def run_autopilot_loop(self):
        while self.autopilot_running and not self.autopilot_stop_event.is_set():
            mode = self.window.mode_var.get()
            is_other = (mode != "listen_self")
            try:
                self.audio_listener.listen_continuous_vad(
                    callback=self.on_autopilot_speech_detected,
                    stop_event=self.autopilot_stop_event,
                    is_other=is_other
                )
            except Exception as e:
                self.logger.error(f"Error in autopilot loop: {e}")
                time.sleep(1.0)

    def on_autopilot_speech_detected(self, audio_data):
        try:
            self.window.show_message("Speech detected! Transcribing...")
            transcription = self.audio_processor.transcribe(audio_data)
            if not transcription or not transcription.strip():
                self.window.show_message("Speech detected, but transcription was empty.")
                return
                
            self.window.show_message("Generating AI response...")
            
            # Read styles and word limits dynamically from UI
            style = self.window.style_var.get()
            word_limit = self.window.words_var.get()
            
            system_instruction = (
                "You are Harvey, an expert real-time assistant for developers and presenters.\n"
                "Your primary task is to solve, answer, or explain the user's SPEECH QUERY directly.\n"
                "The 'Screen Context' contains text/code extracted from their display. Use it ONLY as supporting background if the user explicitly asks about what is on their screen.\n"
                "If the speech query is unrelated to the screen context (or if the screen context is an old error message and the user is speaking about a business/different topic), IGNORE the screen context entirely.\n"
                "Do not reference screen context errors or mention them unless the speech query is about them.\n"
                f"Answering Style: {style}\n"
                f"Word Limit: Max {word_limit} words. Be highly precise, direct, and concise."
            )
            
            mode = self.window.mode_var.get()
            speaker_desc = "Partner (Auto)" if mode != "listen_self" else "Self (Auto)"
            
            screen_ctx = self.memory.get_latest_context()
            response = self.ai_client.get_response(
                question=f"User Speech Query: {transcription}\nProvide the solution/answer matching this query.",
                history=self.memory.get_history(),
                screen_context=screen_ctx,
                system_instruction=system_instruction
            )
            
            self.memory.add_exchange(transcription, response)
            self.window.display_qa(speaker_desc, transcription, response)
        except Exception as e:
            self.logger.error(f"Error processing autopilot speech: {e}")

    def clear_conversation_memory(self):
        self.memory.history = []
        self.memory.contexts = []
        self.window.show_message("=== Conversation History & Screen Context Cleared ===")

    def cleanup(self):
        self.autopilot_running = False
        self.autopilot_stop_event.set()
        try:
            self.window.root.destroy()
        except Exception:
            pass
        try:
            if hasattr(self, 'hotkey_listener'):
                self.hotkey_listener.stop()
        except Exception:
            pass

if __name__ == "__main__":
    app = StealthQnAAssistant()
    app.run()