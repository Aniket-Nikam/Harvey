import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import threading

class AssistantWindow:
    def __init__(self, config, share_safe):
        self.config = config
        self.share_safe = share_safe
        self.root = tk.Tk()
        self.root.title(config['display']['window_title'])
        self.root.geometry(f"{config['display']['size'][0]}x{config['display']['size'][1]}")
        self.root.attributes('-topmost', config['display']['always_on_top'])
        self.root.attributes('-alpha', config['display']['opacity'])
        self.root.configure(bg='#121212')
        
        self.trigger_callback = None
        self.hidden = False
        self.hwnd = None  # Set later if needed
        
        # Configure ttk style for clean widgets
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground="black", background="#1a1a1a", foreground="lime", arrowcolor="lime")
        
        # Settings frame at the top
        settings_frame = tk.Frame(self.root, bg='#1a1a1a', bd=1, relief=tk.FLAT)
        settings_frame.pack(fill=tk.X, padx=8, pady=6)
        
        # Row 1: Mode Selection
        mode_label = tk.Label(settings_frame, text="Mode:", bg='#1a1a1a', fg='#a0a0a0', font=('Consolas', 9, 'bold'))
        mode_label.grid(row=0, column=0, sticky='w', padx=5, pady=4)
        
        self.mode_var = tk.StringVar(value="screenshot")
        modes = [("Screen", "screenshot"), ("Listen Other", "listen_other"), ("Listen Self", "listen_self")]
        for idx, (text, val) in enumerate(modes):
            rb = tk.Radiobutton(settings_frame, text=text, variable=self.mode_var, value=val,
                                bg='#1a1a1a', fg='lime', selectcolor='#121212',
                                activebackground='#1a1a1a', activeforeground='lime',
                                font=('Consolas', 9))
            rb.grid(row=0, column=idx+1, sticky='w', padx=4, pady=4)
            
        # Row 2: Answer Style & Words
        style_label = tk.Label(settings_frame, text="Style:", bg='#1a1a1a', fg='#a0a0a0', font=('Consolas', 9, 'bold'))
        style_label.grid(row=1, column=0, sticky='w', padx=5, pady=4)
        
        self.style_var = tk.StringVar(value="Concise & Direct")
        styles_list = ["Concise & Direct", "Detailed Explanatory", "Code Only", "Bullet Points"]
        self.style_dropdown = ttk.Combobox(settings_frame, textvariable=self.style_var, values=styles_list,
                                           state="readonly", width=18, font=('Consolas', 9))
        self.style_dropdown.grid(row=1, column=1, columnspan=2, sticky='w', padx=4, pady=4)
        
        words_label = tk.Label(settings_frame, text="Words:", bg='#1a1a1a', fg='#a0a0a0', font=('Consolas', 9, 'bold'))
        words_label.grid(row=1, column=3, sticky='w', padx=5, pady=4)
        
        self.words_var = tk.IntVar(value=150)
        self.words_slider = tk.Scale(settings_frame, from_=50, to=500, orient=tk.HORIZONTAL, variable=self.words_var,
                                     bg='#1a1a1a', fg='white', troughcolor='#121212', activebackground='lime',
                                     highlightthickness=0, borderwidth=0, showvalue=True, resolution=25,
                                     font=('Consolas', 8), length=100)
        self.words_slider.grid(row=1, column=4, sticky='w', padx=4, pady=2)
        
        # Row 3: Listen Duration & Auto-Pilot & Clear Button
        duration_label = tk.Label(settings_frame, text="Time:", bg='#1a1a1a', fg='#a0a0a0', font=('Consolas', 9, 'bold'))
        duration_label.grid(row=2, column=0, sticky='w', padx=5, pady=4)
        
        self.duration_var = tk.IntVar(value=30)
        self.duration_slider = tk.Scale(settings_frame, from_=10, to=60, orient=tk.HORIZONTAL, variable=self.duration_var,
                                        bg='#1a1a1a', fg='white', troughcolor='#121212', activebackground='lime',
                                        highlightthickness=0, borderwidth=0, showvalue=True, resolution=5,
                                        font=('Consolas', 8), length=90)
        self.duration_slider.grid(row=2, column=1, sticky='w', padx=4, pady=2)
        
        self.autopilot_var = tk.BooleanVar(value=False)
        self.autopilot_callback = None
        self.clear_callback = None
        self.autopilot_cb = tk.Checkbutton(settings_frame, text="Auto-Pilot", variable=self.autopilot_var,
                                           command=self.on_autopilot_change,
                                           bg='#1a1a1a', fg='lime', selectcolor='#121212',
                                           activebackground='#1a1a1a', activeforeground='lime',
                                           font=('Consolas', 9, 'bold'))
        self.autopilot_cb.grid(row=2, column=2, columnspan=2, sticky='w', padx=5, pady=6)
        
        self.clear_btn = tk.Button(settings_frame, text="CLEAR", command=self.on_clear_click,
                                   bg='#3c1414', fg='white', activebackground='#ff3333', activeforeground='white',
                                   font=('Consolas', 9, 'bold'), relief=tk.FLAT, bd=0)
        self.clear_btn.grid(row=2, column=4, sticky='ew', padx=4, pady=6)
        
        # Row 4: Action Trigger Button (Stretched)
        self.trigger_btn = tk.Button(settings_frame, text="RUN ACTIVE (F5)", command=self.on_trigger_click,
                                     bg='lime', fg='black', activebackground='#bfff00', activeforeground='black',
                                     font=('Consolas', 9, 'bold'), relief=tk.FLAT, bd=0)
        self.trigger_btn.grid(row=3, column=0, columnspan=5, sticky='ew', padx=5, pady=6)
        
        # Text Output Area
        text_frame = tk.Frame(self.root, bg='#121212', bd=1, relief=tk.FLAT)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, bg='black', fg='lime',
                                                   font=('Consolas', 10), insertbackground='lime', bd=0)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for beautiful formatting
        self.text_area.tag_config("header", foreground="#39ff14", font=('Consolas', 10, 'bold')) # Neon green
        self.text_area.tag_config("query", foreground="#a0a0a0", font=('Consolas', 9, 'italic')) # Muted gray
        self.text_area.tag_config("answer", foreground="white", font=('Consolas', 10)) # Crisp white
        self.text_area.tag_config("divider", foreground="#444444") # Dark gray divider
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def on_trigger_click(self):
        if self.trigger_callback:
            self.trigger_callback(self.mode_var.get())
            
    def on_autopilot_change(self):
        if self.autopilot_callback:
            self.autopilot_callback(self.autopilot_var.get())

    def on_clear_click(self):
        if self.clear_callback:
            self.clear_callback()
    
    def on_close(self):
        self.root.quit()  # Quit the mainloop
        self.root.destroy()
    
    def get_hwnd(self):
        if not self.hwnd:
            hwnd = self.root.winfo_id()
            import ctypes
            try:
                # GA_ROOT = 2 (retrieve the actual outer Windows frame handle for Tkinter)
                self.hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)
            except Exception:
                self.hwnd = hwnd
        return self.hwnd
    
    def show(self):
        def _show():
            self.root.deiconify()
            self.hidden = False
            
            # Exclude window from screenshots and screen recording permanently
            if self.config['display'].get('stealth_mode', True):
                import logging
                logger = logging.getLogger(__name__)
                try:
                    self.root.update()  # Force map/create frame structures in OS immediately
                    hwnd = self.get_hwnd()
                    if hwnd:
                        import ctypes
                        # WDA_EXCLUDEFROMCAPTURE = 0x00000011 (completely hides window from screen capture/sharing)
                        success = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
                        if not success:
                            success = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000001)
                        logger.info(f"Stealth display affinity applied to HWND {hwnd}: success={success}")
                    else:
                        logger.error("Failed to apply display affinity: HWND not resolved.")
                except Exception as e:
                    logger.error(f"Failed to apply display affinity: {e}")
        self.root.after(0, _show)
    
    def hide(self):
        self.root.after(0, lambda: self.root.withdraw())
        self.hidden = True
    
    def toggle_visibility(self):
        if self.hidden:
            self.show()
        else:
            self.hide()
    
    def display_qa(self, speaker, query, answer):
        def _insert():
            import time
            timestamp = time.strftime('%H:%M:%S')
            self.text_area.insert(tk.END, f"\n=== [{timestamp}] Spoken by: {speaker} ===\n", "header")
            self.text_area.insert(tk.END, f"Query: \"{query}\"\n", "query")
            self.text_area.insert(tk.END, f"Answer:\n{answer}\n", "answer")
            self.text_area.insert(tk.END, "—" * 45 + "\n", "divider")
            self.text_area.see(tk.END)
        self.root.after(0, _insert)

    def display_response(self, response):
        def _insert():
            self.text_area.insert(tk.END, f"\nAI: {response}\n", "answer")
            self.text_area.see(tk.END)
        self.root.after(0, _insert)
    
    def show_message(self, msg):
        def _insert():
            self.text_area.insert(tk.END, f"\n{msg}\n")
            self.text_area.see(tk.END)
        self.root.after(0, _insert)
    
    def move_to_safe_position(self):
        def _move():
            # Move to bottom right or second monitor
            screen_w = self.root.winfo_screenwidth()
            self.root.geometry(f"+{screen_w - 450}+{self.root.winfo_screenheight() - 350}")
        self.root.after(0, _move)
    
    def reset_position(self):
        self.root.after(0, lambda: self.root.geometry("+100+100"))  # Default