from pydantic import BaseModel, validator
from typing import Optional, Any
from bson import ObjectId
from datetime import datetime

import re

from main import config
MASKED_WORD = [re.compile(word) for word in config.site.preference.word_filter]

class Message(BaseModel):
    _id: ObjectId
    sender_uid: Optional[int]
    receiver_uid: Optional[int]
    content: Optional[str]
    send_time: Optional[datetime]
    quote: Any

    @validator('content')
    def validate_message(cls, message):
        for mask in MASKED_WORD:
            message = re.sub(mask, message, '*')
        return message

class MessageHandler: 
    def __init__(self, **kwargs):
        self.message = Message(**kwargs)