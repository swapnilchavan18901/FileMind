from fastapi import APIRouter, Depends, HTTPException
from src.producer.producer import publish_document_job
from src.db import prisma
from src.deps.auth import get_current_user
from src.schemas.documentation import CreateUploadUrlRequest
from src.utils.s3 import generate_presigned_upload_url
import uuid
import os

router = APIRouter(tags=["documents"])


@router.post("/bots/{bot_id}/documents/upload-url")
async def create_upload_url(
    bot_id: str,
    payload: CreateUploadUrlRequest,
    user=Depends(get_current_user),
):
    # 1️⃣ Verify bot ownership
    # bot = await prisma.bot.find_unique(where={"id": bot_id})
    # if not bot or bot.userId != user.id:
    #     raise HTTPException(status_code=404, detail="Bot not found")

    # 2️⃣ Validate file (PDF only)
    print(f"payloadishere { payload }")
    if payload.fileSize > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    ext = os.path.splitext(payload.fileName)[1].lower()
    if ext != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if payload.fileType != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type")

    # 3️⃣ Create document record
    document_id = str(uuid.uuid4())
    s3_key = f"documents/{bot_id}/{document_id}.pdf"

    document = await prisma.document.create(
        data={
            "id": document_id,
            "botId": bot_id,
            "fileName": payload.fileName,
            "fileType": payload.fileType,
            "fileSize": payload.fileSize,
            "storageUrl": s3_key,
            "status": "queued",
        }
    )

    # 4️⃣ Generate presigned URL (NO Content-Type)
    upload_url = generate_presigned_upload_url(s3_key)
    
    return {
        "documentId": document.id,
        "uploadUrl": upload_url,
        "s3Key": s3_key,
    }


@router.post("/documents/{document_id}/complete")
async def complete_document_upload(
    document_id: str,
    user=Depends(get_current_user),
):
    print(f"userishere: {user.id}")
    # 1️⃣ Fetch document
    document = await prisma.document.find_unique(
        where={"id": document_id},
        include={"bot": True},
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2️⃣ Ownership check
    if document.bot.userId != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # 3️⃣ Prevent double enqueue
    if document.status in ("processing", "ready"):
        raise HTTPException(
            status_code=400,
            detail="Document already queued or processed",
        )

    # 4️⃣ Update status → queued
    await prisma.document.update(
        where={"id": document_id},
        data={"status": "queued"},
    )

    # 5️⃣ Push to queue (PRODUCER)
    await publish_document_job(document_id, document.bot.id, user.id)

    return {
        "success": True,
        "documentId": document_id,
        "status": "queued",
    }