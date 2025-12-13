---
description: Create report/export feature for PROJECT_BESAR
---

# Flow C2: Create Report Feature

## Pre-requisites
- [ ] Report type defined (PDF/Excel/CSV)
- [ ] Data source identified
- [ ] Filters/parameters defined

## Step 1: Create Report Service
Location: `modules/{module}/backend/app/services/reports/{report}_report.py`

```python
from app.core.reports import ReportGenerator

class {Report}Report(ReportGenerator):
    async def generate(self, params: ReportParams) -> bytes:
        # Fetch data
        data = await self.fetch_data(params)

        # Generate report
        if params.format == 'pdf':
            return await self.generate_pdf(data)
        elif params.format == 'excel':
            return await self.generate_excel(data)
        else:
            return await self.generate_csv(data)
```

## Step 2: Create Background Job
```python
@celery_app.task
def generate_report_async(report_id: str, params: dict):
    report = {Report}Report()
    result = report.generate(ReportParams(**params))

    # Store result
    storage.upload(f"reports/{report_id}", result)

    # Notify user
    notify_report_ready(report_id)
```

## Step 3: Create API Endpoint
```python
@router.post("/reports/{report-type}")
async def generate_{report}(params: ReportParams):
    report_id = str(uuid4())
    generate_report_async.delay(report_id, params.dict())
    return {"report_id": report_id, "status": "processing"}

@router.get("/reports/{report_id}")
async def get_report_status(report_id: str):
    return {"status": get_status(report_id), "download_url": get_url(report_id)}
```

## Step 4: Create Frontend UI
```typescript
const { mutate, data } = useGenerateReport();

const handleGenerate = () => {
  mutate(params, {
    onSuccess: (data) => {
      toast.info('Report is being generated...');
      pollReportStatus(data.report_id);
    },
  });
};
```

## Checklist Before Complete
- [ ] Report generates correctly
- [ ] Async for large reports
- [ ] Download works
- [ ] Progress feedback
- [ ] Error handling
