---
description: Create file upload feature for PROJECT_BESAR
---

# Flow C5: Create File Upload Feature

## Pre-requisites
- [ ] File types allowed defined
- [ ] Max size defined
- [ ] Storage location defined

## Step 1: Create Storage Service
Location: `modules/{module}/backend/app/services/storage/{entity}_storage.py`

```python
from app.core.storage import StorageService

class {Entity}Storage:
    def __init__(self, storage: StorageService):
        self.storage = storage
        self.bucket = '{entities}'

    async def upload(self, file: UploadFile, tenant_id: UUID) -> str:
        # Validate
        self._validate_file(file)

        # Generate key
        key = f"{tenant_id}/{uuid4()}/{file.filename}"

        # Upload to R2
        await self.storage.upload(self.bucket, key, file.file)

        return key

    async def get_presigned_url(self, key: str) -> str:
        return await self.storage.presigned_url(self.bucket, key, expires=3600)
```

## Step 2: Create API Endpoint
```python
@router.post("/upload")
async def upload_file(
    file: UploadFile,
    storage: {Entity}Storage = Depends(),
    tenant_id: UUID = Depends(get_tenant_id)
):
    key = await storage.upload(file, tenant_id)
    url = await storage.get_presigned_url(key)
    return {"key": key, "url": url}
```

## Step 3: Create Frontend Upload
```typescript
const { upload, progress, isUploading } = useFileUpload();

<FileUpload
  accept=".pdf,.jpg,.png"
  maxSize={10 * 1024 * 1024} // 10MB
  onUpload={async (file) => {
    const result = await upload(file);
    return result.url;
  }}
/>

{isUploading && <ProgressBar value={progress} />}
```

## Step 4: Drag & Drop Support
```typescript
<Dropzone
  onDrop={handleDrop}
  accept={{ 'image/*': ['.png', '.jpg'], 'application/pdf': ['.pdf'] }}
>
  {({ getRootProps, getInputProps, isDragActive }) => (
    <div {...getRootProps()} className={cn('dropzone', isDragActive && 'active')}>
      <input {...getInputProps()} />
      <p>Drag files here or click to browse</p>
    </div>
  )}
</Dropzone>
```

## Checklist Before Complete
- [ ] File validation (type, size)
- [ ] Secure upload to R2
- [ ] Presigned URLs for access
- [ ] Progress indicator
- [ ] Error handling
- [ ] Virus scanning (if required)
