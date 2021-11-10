from typing import Union, Callable, Coroutine
from functools import partial
from datetime import datetime, timedelta

from . import publish_with_delay

class DelayedTask:
    """This is a helper class that helps schedule delayed tasks with the
    help of rabbitmq delayed delivery extension.

    Usage: 
    ```python
        # register function
        @delay.reg
        [async] def delayed_function(*args, **kwargs):
            # Check if the tasked has been cancelled
            if cancelled:
                return
            # Do something
            pass

        # schedule task
        await delayed_function(delay: Union[timedelta, datetime], *args, **kwargs)
    ```
    
    Example:

    ```python
        async def test(m: str = 'hello world!'):
            print(datetime.now())
            await _test(timedelta(seconds=5), 'hello!', test='1')
            await _test_a(timedelta(seconds=6),'hello!', test='1')

        from utils.connection.mq import delay

        @delay.reg
        def _test(*args, **kwargs):
            print(datetime.now())
            print(args, kwargs)

        @delay.reg
        async def _test_a(*args, **kwargs):
            print(datetime.now())
            print(args, kwargs)
    ```
    """
    registed_func = dict()
    def __init__(self):
        pass

    async def spawn(self, _func_key: str, delay: Union[timedelta, datetime], *args, **kwargs):
        payload = {
            'func': _func_key,
            'args': args,
            'kwargs': kwargs
        }
        await publish_with_delay(payload, delay)

    def reg(self, func: Callable):
        self.registed_func[func.__module__ + func.__name__] = func
        return partial(self.spawn, func.__module__ + func.__name__)
    
    async def execute(self, message: dict):
        func = self.registed_func[message['func']]
        ret = func(*message['args'], **message['kwargs'])
        if isinstance(ret, Coroutine):
            await ret

delay = DelayedTask()