from pydantic import BaseModel


class CreateUploadUrlRequest(BaseModel):
    fileName: str
    fileType: str
    fileSize: int
