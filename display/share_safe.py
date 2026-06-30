class ShareSafeManager:
    def __init__(self, config):
        self.config = config
    
    def activate_stealth_mode(self, window):
        """Move window to a safe position during screen sharing."""
        if self.config['display']['stealth_mode']:
            window.move_to_safe_position()
    
    def deactivate_stealth_mode(self, window):
        """Restore window to default position when not screen sharing."""
        window.reset_position()