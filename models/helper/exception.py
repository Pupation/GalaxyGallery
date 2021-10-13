
class ErrorException(Exception):
    def __init__(self, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
    
    def __repr__(self):
        return self.message