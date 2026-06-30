import psutil

class ScreenShareDetector:
    def __init__(self, config):
        self.config = config
        self.share_apps = config['stealth']['detect_apps']
    
    def is_screen_sharing_active(self):
        """Check for running screen sharing processes."""
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                name = proc.info['name'] or ''
                if any(app.lower() in name.lower() for app in self.share_apps):
                    # Additional check for sharing state if possible (e.g., window titles)
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False