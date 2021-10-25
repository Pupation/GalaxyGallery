
class ErrorException(Exception):
    def __init__(self, message,ret_code=400, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
        self.ret_code = ret_code
    
    def __repr__(self):
        return self.message

class GeneralException(Exception):
    def __init__(self, message, retcode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
        self.retcode = retcode