from pydantic import BaseModel, StringConstraints
from datetime import datetime
from typing import Optional, Dict, Annotated

class LogShema(BaseModel):
    timestamp: datetime
    level: Annotated[str, StringConstraints(pattern=r"^(DEBUG|INFO|WARNING|ERROR)$")]
    service: Annotated[str, StringConstraints(min_length=1)]
    message: Annotated[str, StringConstraints(min_length=1)]
    metadata: Optional[Dict] = None

class UserRegister(BaseModel):
    username: Annotated[str, StringConstraints(min_length=4)]
    password: Annotated[str, StringConstraints(min_length=6)]

class UserLogin(BaseModel):
    username: Annotated[str, StringConstraints(min_length=4)]
    password: Annotated[str, StringConstraints(min_length=6)]