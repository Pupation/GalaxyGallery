from fastapi.responses import PlainTextResponse


from .benc import BencResponse

def ErrorResponse(content, status_code=400):
    headers = {'content-type': 'text/plain; charset=utf-8',
                'Pragma': 'no-cache'
            }
    return BencResponse(content={'failure reason': content}, status_code=status_code)