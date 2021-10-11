from fastapi.responses import PlainTextResponse
import bencodepy


def BencResponse(content, status_code=200):
    headers = {'content-type': 'text/plain; charset=utf-8',
                'Pragma': 'no-cache'
            }
    content = bencodepy.encode(content)
    return PlainTextResponse(content=content, status_code=status_code, headers=headers)