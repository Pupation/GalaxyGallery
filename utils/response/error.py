from fastapi.responses import PlainTextResponse


def ErrorResponse(content, status_code=400):
    headers = {'content-type': 'text/plain; charset=utf-8',
                'Pragma': 'no-cache'
            }
    return PlainTextResponse(content=content, status_code=status_code, headers=headers)