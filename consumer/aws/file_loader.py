
import boto3
import tempfile
import asyncio
import os
from pypdf import PdfReader
from botocore.config import Config
from botocore.exceptions import ClientError
from consumer.consumer_env import env


class Document:
    """Simple Document class to replace langchain Document"""
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}

# Match the exact S3 configuration from src/utils/s3.py
s3 = boto3.client(
    "s3",
    region_name=env.AWS_REGION,
    aws_access_key_id=env.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
    endpoint_url=f"https://s3.{env.AWS_REGION}.amazonaws.com",
    config=Config(signature_version="s3v4"),
)
BUCKET = env.AWS_S3_BUCKET

print("=" * 60)
print("🔧 AWS S3 Consumer Configuration Loaded:")
print(f"   Region: {env.AWS_REGION}")
print(f"   Bucket: {BUCKET}")
print(f"   Endpoint: https://s3.{env.AWS_REGION}.amazonaws.com")
print(f"   Access Key ID: {env.AWS_ACCESS_KEY_ID[:10]}..." if env.AWS_ACCESS_KEY_ID else "   Access Key ID: NOT SET")
print("=" * 60)

def _load_pdf_from_s3_sync(key: str) -> tuple[list[Document], str]:
    """Synchronous helper for loading PDF from S3
    Returns: (documents, temp_file_path)
    """
    print(f"\n{'='*60}")
    print(f"🔍 S3 Download Request:")
    print(f"   Bucket: {BUCKET}")
    print(f"   Key: {key}")
    print(f"   Full URL: https://s3.{env.AWS_REGION}.amazonaws.com/{BUCKET}/{key}")
    print(f"{'='*60}\n")
    
    # First, try to verify bucket access and find the file
    try:
        print("🔎 Checking if file exists...")
        # Try to head_object to check if file exists
        s3.head_object(Bucket=BUCKET, Key=key)
        print(f"✅ File exists in S3!")
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        print(f"⚠️ head_object failed with error: {error_code}")
        
        # Try to list objects with this prefix
        try:
            print(f"\n🔎 Searching for files with prefix: {key}")
            response = s3.list_objects_v2(Bucket=BUCKET, Prefix=key, MaxKeys=1)
            
            if 'Contents' in response and len(response['Contents']) > 0:
                print(f"✅ Found file: {response['Contents'][0]['Key']}")
            else:
                print(f"❌ No files found with prefix: {key}")
                
                # Get parent directory to see what's there
                parent_prefix = "/".join(key.split("/")[:-1]) + "/"
                print(f"\n🔎 Checking parent directory: {parent_prefix}")
                parent_response = s3.list_objects_v2(Bucket=BUCKET, Prefix=parent_prefix, MaxKeys=10)
                
                if 'Contents' in parent_response:
                    print(f"📂 Files in parent directory:")
                    for obj in parent_response['Contents']:
                        print(f"   - {obj['Key']}")
                else:
                    print(f"❌ Parent directory is empty")
                    
                    # Try to list root of bucket
                    print(f"\n🔎 Sample files from bucket root:")
                    root_response = s3.list_objects_v2(Bucket=BUCKET, MaxKeys=10)
                    if 'Contents' in root_response:
                        for obj in root_response['Contents']:
                            print(f"   - {obj['Key']}")
                    else:
                        print(f"   (bucket is empty)")
                        
        except Exception as list_err:
            print(f"❌ Error listing bucket: {list_err}")
        
        raise e
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
        
        try:
            print(f"⬇️  Downloading to: {tmp_path}")
            s3.download_file(BUCKET, key, tmp_path)
            print(f"✅ Successfully downloaded!")
            
            print(f"📖 Loading PDF...")
            reader = PdfReader(tmp_path)
            
            # Extract text from each page and create Document objects
            docs = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                doc = Document(
                    page_content=text,
                    metadata={
                        "page": page_num + 1,  # 1-indexed page numbers
                        "source": key,
                        "total_pages": len(reader.pages)
                    }
                )
                docs.append(doc)
            
            # Count pages with content
            pages_with_content = sum(1 for doc in docs if doc.page_content and doc.page_content.strip())
            print(f"✅ PDF loaded: {len(docs)} pages ({pages_with_content} have text content)")
            
            # Return docs AND temp file path so it can be cleaned up later
            return docs, tmp_path
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            print(f"❌ Download failed: {e}")
            raise e

async def load_pdf_from_s3(key: str) -> tuple[list[Document], str]:
    """Async wrapper for loading PDF from S3 using thread pool
    Returns: (documents, temp_file_path)
    """
    return await asyncio.to_thread(_load_pdf_from_s3_sync, key)
