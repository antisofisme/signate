# Data Integration & OCR Specifications

> **Specification #4**: OCR Integration, Image Processing, Data Extraction & Quality Rules
>
> **Last Updated**: 2025-12-13
> **Status**: ✅ Specification Approved
> **Related**: STD-16 (Smart Suggestions), STD-03 (Files), STD-19 (File Handling)

---

## Overview

This specification defines how OCR (Optical Character Recognition) integrates into the platform, image processing pipelines, data extraction and validation, and quality assurance rules.

**Use Cases**:
- Guest profile photo → Extract ID information (KTP, Passport)
- Receipt/invoice image → Extract line items, totals, tax
- Bank statement → Extract transactions for reconciliation
- Supplier invoice → Extract PO matching data

---

## 1. OCR Architecture

### 1.1 System Components

```
┌───────────────────────────────────────────────────────────┐
│                    User Application                        │
│  (Upload photo from PMS guest profile, POS receipt, etc)  │
└────────────────┬──────────────────────────────────────────┘
                 │
                 ↓
         ┌───────────────┐
         │ Image Upload  │
         │   & Validate  │
         └───────┬───────┘
                 │
                 ↓
      ┌──────────────────────┐
      │ Image Preprocessing  │
      │  • Resize            │
      │  • Normalize         │
      │  • Compress → WebP   │
      └──────────┬───────────┘
                 │
                 ↓
      ┌──────────────────────┐
      │  OCR Processing      │
      │  (Cloud or On-prem)  │
      │  • Tesseract (free)  │
      │  • Google Vision API │
      │  • AWS Textract      │
      │  • Azure Form Recog  │
      └──────────┬───────────┘
                 │
                 ↓
      ┌──────────────────────┐
      │ Data Extraction      │
      │  • Parse OCR output  │
      │  • Field mapping     │
      │  • Confidence score  │
      └──────────┬───────────┘
                 │
                 ↓
      ┌──────────────────────┐
      │ Data Validation      │
      │  • Format check      │
      │  • Regex match       │
      │  • Business rule     │
      └──────────┬───────────┘
                 │
                 ↓
    ┌────────────────────────────┐
    │ Present to User (STD-16)    │
    │ • High confidence: pre-fill │
    │ • Medium: show as hint      │
    │ • Low: flag for review      │
    └────────────┬────────────────┘
                 │
                 ↓
         ┌──────────────────┐
         │ User Confirm     │
         │ • Accept/Edit/   │
         │   Reject         │
         └────────┬─────────┘
                  │
                  ↓
         ┌──────────────────┐
         │ Save & Audit     │
         │ • Store image    │
         │ • Save data      │
         │ • Record changes │
         └──────────────────┘
```

### 1.2 OCR Provider Selection

```
Provider       | Cost    | Accuracy | Speed   | On-Prem | Best For
───────────────────────────────────────────────────────────────────
Tesseract      | Free    | 85-92%   | Medium  | ✅ Yes  | High volume, cost-sensitive
Google Vision  | Paid    | 96-98%   | Fast    | ❌ No   | High accuracy needed
AWS Textract   | Paid    | 95-97%   | Fast    | ❌ No   | AWS ecosystem
Azure Form Rec.| Paid    | 95-97%   | Fast    | ❌ No   | Structured forms
Cloudflare OCR | TBD     | TBD      | TBD     | TBD     | Potential alternative

RECOMMENDATION:
  Primary: Tesseract (free, on-prem capable)
  Fallback: Google Vision API (high accuracy, cost-controlled)
  Future: Hybrid approach (Tesseract for simple, Vision for complex)
```

---

## 2. Image Upload & Preprocessing

### 2.1 Upload Requirements

```
ACCEPTED FORMATS:
  • JPEG (.jpg, .jpeg) - most common for photos
  • PNG (.png) - for documents
  • TIFF (.tiff) - high-quality scans
  • PDF (.pdf) - for multi-page documents

REJECTED:
  • BMP, GIF, WebP (already processed)
  • SVG (vector, not suitable for OCR)

FILE SIZE LIMITS:
  Min: 100 KB (too small = low quality)
  Max: 10 MB (too large = slow processing)
  Ideal: 500 KB - 3 MB

RESOLUTION:
  Min: 150 DPI (too low = OCR accuracy drops)
  Ideal: 300 DPI (standard document)
  Max: 600 DPI (diminishing returns, larger file)

QUALITY CHECKS:
  Before OCR, validate:
    ✓ File format (mime type check)
    ✓ File size (100KB - 10MB)
    ✓ Image readable (not corrupted)
    ✓ Resolution adequate (>150 DPI)
    ✓ Not an ID document of restricted type (security)
```

### 2.2 Preprocessing Pipeline

```python
def preprocess_image(file_path: str, target_format: str = 'webp') -> dict:
    """
    Preprocess image for OCR and storage.

    Steps:
    1. Load image
    2. Normalize orientation (detect & correct rotation)
    3. Deskew (if document is tilted)
    4. Enhance contrast (improve text visibility)
    5. Remove noise
    6. Resize to standard DPI (300 DPI)
    7. Compress to WebP
    """

    image = Image.open(file_path)

    # 1. Detect & Fix Rotation
    image = fix_rotation(image)

    # 2. Deskew
    image = deskew(image)

    # 3. Contrast Enhancement
    image = enhance_contrast(image)

    # 4. Noise Reduction
    image = denoise(image)

    # 5. Resize to 300 DPI
    # Current DPI: read from image metadata
    # Target DPI: 300
    current_dpi = image.info.get('dpi', (96, 96))
    if current_dpi[0] != 300:
        scale_factor = 300 / current_dpi[0]
        new_size = (
            int(image.width * scale_factor),
            int(image.height * scale_factor)
        )
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # 6. Compress to WebP
    webp_path = f"{file_path}.webp"
    image.save(webp_path, 'WEBP', quality=85)  # 85% quality = good balance

    # Return metadata
    return {
        'original_format': image.format,
        'original_size_kb': os.path.getsize(file_path) / 1024,
        'webp_size_kb': os.path.getsize(webp_path) / 1024,
        'compression_ratio': os.path.getsize(file_path) / os.path.getsize(webp_path),
        'dimensions': (image.width, image.height),
        'dpi': 300,
        'preprocessing_time_ms': elapsed_time,
        'webp_path': webp_path
    }

# Result: Image optimized, compressed, ready for OCR
```

---

## 3. OCR Processing & Data Extraction

### 3.1 OCR Execution

```python
def extract_text_with_ocr(image_path: str, ocr_provider: str = 'tesseract') -> dict:
    """
    Extract text from image using OCR.

    Returns:
      raw_text: Full OCR output
      structured_data: Field-extracted data
      confidence_scores: Per-field confidence
      processing_details: Time, provider, version
    """

    if ocr_provider == 'tesseract':
        ocr_result = pytesseract.image_to_data(
            image_path,
            output_type=pytesseract.Output.DICT,
            lang='ind+eng'  # Indonesian + English
        )
        raw_text = pytesseract.image_to_string(image_path)

    elif ocr_provider == 'google_vision':
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()

        with open(image_path, 'rb') as f:
            image = vision.Image(content=f.read())

        response = client.document_text_detection(image=image)
        raw_text = response.full_text_annotation.text

    return {
        'raw_text': raw_text,
        'processing_time_ms': elapsed_time,
        'provider': ocr_provider,
        'language': 'ind+eng'
    }
```

### 3.2 Field Extraction from OCR Output

```python
def extract_fields(raw_text: str, document_type: str) -> dict:
    """
    Extract structured fields from OCR text.

    Document types:
      - 'ktp': Indonesian ID Card
      - 'passport': Passport
      - 'invoice': Commercial invoice
      - 'receipt': POS receipt
      - 'bank_statement': Bank statement
    """

    if document_type == 'ktp':
        return extract_ktp_fields(raw_text)
    elif document_type == 'passport':
        return extract_passport_fields(raw_text)
    # ... etc

def extract_ktp_fields(raw_text: str) -> dict:
    """Extract KTP (Indonesian ID card) fields."""

    patterns = {
        'no_identitas': r'NO\.\s*IDENTITAS\s*:\s*(\d{16})',
        'nama': r'NAMA\s*:\s*([A-Z\s]+)',
        'tempat_lahir': r'TEMPAT\s*LAHIR\s*:\s*([A-Z\s]+)',
        'tanggal_lahir': r'TANGGAL\s*LAHIR\s*:\s*(\d{1,2}\s*[A-Z]+\s*\d{4})',
        'jenis_kelamin': r'JENIS\s*KELAMIN\s*:\s*(LAKI-LAKI|PEREMPUAN)',
        'alamat': r'ALAMAT\s*:\s*(.+?)(?=RT|$)',
        'agama': r'AGAMA\s*:\s*(ISLAM|KRISTEN|HINDU|BUDHA|LAIN)',
        'pekerjaan': r'PEKERJAAN\s*:\s*([A-Z\s]+)',
        'berlaku_hingga': r'BERLAKU\s*HINGGA\s*:\s*(\d{1,2}\s*[A-Z]+\s*\d{4})'
    }

    extracted = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            extracted[field] = {
                'value': match.group(1).strip(),
                'confidence': 0.9  # Based on pattern match
            }
        else:
            extracted[field] = {
                'value': None,
                'confidence': 0.0
            }

    return extracted
```

### 3.3 Field Confidence Scoring

```python
def calculate_field_confidence(field_name: str, extracted_value: str,
                               ocr_confidence: float, validation_result: bool) -> float:
    """
    Calculate confidence for extracted field.

    Factors:
      1. OCR confidence (from OCR engine)
      2. Pattern match (regex pattern match quality)
      3. Validation result (format validation pass/fail)
      4. Fuzzy match (if comparing to known values)
    """

    score = 0

    # Factor 1: OCR confidence (weight: 40%)
    ocr_score = ocr_confidence * 0.4
    score += ocr_score

    # Factor 2: Pattern match (weight: 30%)
    pattern_match_quality = calculate_pattern_match_quality(field_name, extracted_value)
    score += pattern_match_quality * 0.3

    # Factor 3: Validation (weight: 20%)
    validation_score = 1.0 if validation_result else 0.5
    score += validation_score * 0.2

    # Factor 4: Format check (weight: 10%)
    format_correct = check_format(field_name, extracted_value)
    score += (1.0 if format_correct else 0.3) * 0.1

    final_confidence = min(score, 1.0)  # Cap at 100%
    return int(final_confidence * 100)

# Example results:
# no_identitas: "123456789012345" → 98% confidence
# nama: "KHOIRUL USER" → 92% confidence (slight OCR blur on last name)
# alamat: "Jl. Merdeka No. 123" → 85% confidence (partial text extracted)
```

---

## 4. Data Validation & Quality Rules

### 4.1 Validation Rules by Field Type

```python
VALIDATION_RULES = {
    'id_number': {
        'format': r'^\d{16}$',  # KTP: 16 digits
        'min_length': 16,
        'max_length': 16,
        'check_digit': validate_ktp_checksum  # KTP has checksum
    },

    'passport': {
        'format': r'^[A-Z0-9]{6,10}$',
        'min_length': 6,
        'max_length': 10
    },

    'phone': {
        'format': r'^(\+62|62|0)[0-9]{9,12}$',
        'normalize': lambda x: x.replace(' ', '').replace('-', ''),
        'valid_prefixes': ['62812', '62813', '62811', '62821', '0812', '0813']
    },

    'email': {
        'format': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'lowercase': True
    },

    'date': {
        'format': r'^\d{1,2}[/-]\d{1,2}[/-]\d{4}$',
        'parse': ['dd/mm/yyyy', 'mm/dd/yyyy', 'dd-mm-yyyy'],
        'min_date': '1900-01-01',
        'max_date': 'today'
    },

    'address': {
        'min_length': 5,
        'max_length': 200
    }
}

def validate_field(field_name: str, value: str) -> dict:
    """Validate extracted field against rules."""

    rules = VALIDATION_RULES.get(field_name)
    if not rules:
        return {'valid': True, 'errors': []}

    errors = []

    # Check format
    if 'format' in rules:
        if not re.match(rules['format'], value):
            errors.append(f"Invalid format. Expected: {rules['format']}")

    # Check length
    if 'min_length' in rules and len(value) < rules['min_length']:
        errors.append(f"Too short. Minimum: {rules['min_length']}")

    if 'max_length' in rules and len(value) > rules['max_length']:
        errors.append(f"Too long. Maximum: {rules['max_length']}")

    # Check digit validation (e.g., KTP checksum)
    if 'check_digit' in rules:
        if not rules['check_digit'](value):
            errors.append("Invalid check digit")

    # Normalize if needed
    if 'normalize' in rules:
        value = rules['normalize'](value)

    # Lowercase if needed
    if rules.get('lowercase', False):
        value = value.lower()

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'normalized_value': value
    }
```

---

## 5. Suggestion Presentation (STD-16 Integration)

### 5.1 OCR Suggestion UI Structure

```typescript
interface OCRSuggestion {
  // Extracted data with confidence
  fields: {
    [field_name]: {
      value: string | null;
      confidence: number;  // 0-100%
      validation_status: 'valid' | 'invalid' | 'warning';
      validation_errors?: string[];
      ocr_alternatives?: string[];  // If OCR uncertain
    };
  };

  // Summary
  summary: {
    total_fields: number;
    high_confidence_fields: number;  // >= 90%
    medium_confidence_fields: number;  // 70-89%
    low_confidence_fields: number;  // < 70%
    validation_pass_rate: number;  // % of fields passing validation
  };

  // Processing metadata
  metadata: {
    document_type: 'ktp' | 'passport' | 'invoice' | 'receipt';
    ocr_provider: string;
    ocr_confidence: number;
    processing_time_ms: number;
    image_file_path: string;
    extracted_at: timestamp;
  };

  // User action
  user_action?: {
    status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'MODIFIED';
    accepted_at?: timestamp;
    modifications?: Map<field, new_value>;
  };
}
```

### 5.2 UI Presentation

```
┌────────────────────────────────────────────────────┐
│ Document Type: Indonesian ID Card (KTP)           │
│ OCR Provider: Tesseract (87% confidence)          │
├────────────────────────────────────────────────────┤
│                                                    │
│ ⏱️  Processing took 2.3 seconds                    │
│                                                    │
│ Summary: 8/10 fields extracted (80% complete)     │
│ • High confidence (8): ████░░░░░░ 80%            │
│ • Medium confidence (2): ░░░░░░░░░░ 0%            │
│ • Low confidence (0): ░░░░░░░░░░ 0%              │
│                                                    │
│ ─────────────────────────────────────────────────  │
│                                                    │
│ NO IDENTITAS                                       │
│ ┌─────────────────────────────────────┐           │
│ │ 1234567890123456        ✓ 98%       │  ← Input │
│ └─────────────────────────────────────┘           │
│ Validation: PASS (valid checksum)                 │
│                                                    │
│ NAMA                                               │
│ ┌─────────────────────────────────────┐           │
│ │ KHOIRUL USER           ⚠️  85%      │           │
│ └─────────────────────────────────────┘           │
│ Note: "USER" may be misread, check if correct    │
│                                                    │
│ TEMPAT LAHIR                                       │
│ ┌─────────────────────────────────────┐           │
│ │ JAKARTA                ✓ 92%        │           │
│ └─────────────────────────────────────┘           │
│                                                    │
│ TANGGAL LAHIR                                      │
│ ┌─────────────────────────────────────┐           │
│ │ 15 MEI 1990            ✓ 95%        │           │
│ └─────────────────────────────────────┘           │
│ Parsed as: 1990-05-15 (format valid)              │
│                                                    │
│ ... (more fields) ...                             │
│                                                    │
│ BERLAKU HINGGA                                     │
│ ┌─────────────────────────────────────┐           │
│ │ [MISSING - not visible in image] ❌ │ ← Flag   │
│ └─────────────────────────────────────┘           │
│ Action: Please enter manually or re-upload       │
│                                                    │
│ ─────────────────────────────────────────────────  │
│                                                    │
│ Original Image Quality: Good                      │
│ Resolution: 300 DPI                               │
│ File: scan_ktp_12345.webp (145 KB)               │
│                                                    │
│ [CONFIRM & SAVE] [EDIT MANUALLY] [RETRY OCR]    │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 6. Error Handling & Quality Assurance

### 6.1 Common OCR Errors

```
ERROR TYPE              | Example                | Mitigation
─────────────────────────────────────────────────────────────
Rotation/Skew          | Image rotated 45°      | Auto-rotate, deskew
Character confusion    | 0 vs O, l vs 1, S vs 5 | Confidence scoring
Partial text           | Bottom of doc cut off   | Flag as missing
Blurry/Low quality     | Out of focus photo      | Reject, ask re-upload
Language mix           | ID + English text       | Multi-language OCR
Formatting issues      | Table structure lost    | Pattern matching
Handwritten text       | Manual signatures       | Low confidence, flag

MITIGATION STRATEGY:
  1. Preprocessing improves quality (deskew, denoise, enhance)
  2. Confidence scoring flags uncertain fields
  3. Validation rules catch format errors
  4. User review catches context errors
  5. Fallback: Manual entry if OCR fails
```

### 6.2 Quality Assurance Thresholds

```python
QA_THRESHOLDS = {
    'min_document_confidence': 0.75,  # If avg OCR < 75%, ask user to re-upload
    'min_field_confidence': 0.7,      # Field with <70% → flag for review
    'min_validation_pass_rate': 0.8,  # If <80% fields valid → review before save
    'min_image_size_kb': 100,
    'max_image_size_kb': 10000,
}

def check_ocr_quality(ocr_result: dict) -> dict:
    """Quality gate before presenting to user."""

    # Average confidence
    avg_confidence = sum(f['confidence'] for f in ocr_result['fields'].values()) / len(ocr_result['fields'])

    # Validation pass rate
    valid_count = sum(1 for f in ocr_result['fields'].values() if f['validation_status'] == 'valid')
    validation_pass_rate = valid_count / len(ocr_result['fields'])

    issues = []

    if avg_confidence < QA_THRESHOLDS['min_document_confidence']:
        issues.append(f"Low document quality ({avg_confidence:.0%}). Consider re-upload.")

    if validation_pass_rate < QA_THRESHOLDS['min_validation_pass_rate']:
        issues.append(f"Low validation pass rate ({validation_pass_rate:.0%}). Manual review recommended.")

    # Flag low-confidence fields
    low_confidence_fields = [
        f for f, data in ocr_result['fields'].items()
        if data['confidence'] < QA_THRESHOLDS['min_field_confidence']
    ]

    if low_confidence_fields:
        issues.append(f"Low confidence fields: {', '.join(low_confidence_fields)}")

    return {
        'quality_passed': len(issues) == 0,
        'avg_confidence': avg_confidence,
        'validation_pass_rate': validation_pass_rate,
        'issues': issues,
        'action': 'proceed' if len(issues) == 0 else 'review'
    }
```

---

## 7. Storage & Archival

### 7.1 Image Storage

```
Original Upload:
  - Path: /uploads/original/{tenant_id}/{document_type}/{uuid}.{ext}
  - Format: As uploaded (JPEG, PNG, etc)
  - Retention: 30 days (after processing)

Processed (WebP):
  - Path: /storage/processed/{tenant_id}/{document_type}/{uuid}.webp
  - Format: WebP (85% quality, optimized)
  - Retention: Depends on document type
  - Size: Typically 40-60% of original

Examples:
  - Guest ID photos: 7 years (per hotel regulation)
  - Receipts: 5 years (accounting requirement)
  - Bank statements: 7 years (tax compliance)
  - Invoice scans: 10 years (legal requirement)

Archival:
  - After retention period: Move to cold storage (AWS Glacier, etc)
  - Keep indexing for retrieval
  - Eventually delete if regulations allow
```

### 7.2 Extracted Data Storage

```
Extracted OCR Data:
  - Stored in main database (linked to entity)
  - No duplicate storage of raw text
  - Audit trail maintained (STD-16, BIZ-03)

Metadata:
  - ocr_processing_details table
  - Tracks: image_file, ocr_provider, confidence, fields extracted
  - Links: Guest profile ID, Invoice ID, etc

Query Example:
  SELECT
    extracted_data,
    ocr_confidence,
    validated_at,
    user_confirmed_by,
    user_confirmed_at
  FROM ocr_processing_details
  WHERE entity_type = 'guest_profile'
    AND entity_id = 'guest-123'
    AND extracted_at > DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## 8. Integration with Other Systems

### 8.1 Guest Profile Integration (PMS)

```
Flow:
  1. Guest uploads KTP photo
  2. System preprocesses, OCR extracts
  3. Suggestion presented (STD-16)
  4. Guest confirms/edits
  5. Data saved to guest profile

Result:
  guest_profile table populated:
    - first_name, last_name (from OCR)
    - id_type, id_number (from OCR)
    - date_of_birth (from OCR)
    - address, city (from OCR)
    - image_webp_path (processed image)
    - ocr_confidence (metadata)
    - created_at (audit)
```

### 8.2 Invoice/Receipt Integration (Accounting/POS)

```
Flow:
  1. User uploads receipt/invoice image
  2. System OCR extracts line items, total, date
  3. Suggestion presented
  4. User confirms/edits
  5. Create GL entries, AP invoice

Result:
  expense_claim or ap_invoice:
    - items[], amounts[], taxes[] (from OCR)
    - vendor_name (from OCR)
    - invoice_date, invoice_number (from OCR)
    - receipt_image_path (evidence)
    - gl_entry_id (linked for audit)
```

### 8.3 Bank Statement Integration (Reconciliation)

```
Flow:
  1. User uploads bank statement image/PDF
  2. System OCR extracts transactions
  3. Present suggestions for reconciliation (STD-16)
  4. User matches with GL entries
  5. Reconciliation complete (BIZ-03)

Result:
  reconciliation_entry:
    - bank_transactions[] (from OCR)
    - gl_matches[] (user confirmed)
    - reconciliation_status: COMPLETE
    - image_evidence_path (audit trail)
```

---

## 9. Performance & Scaling

### 9.1 Processing Optimization

```
Tesseract (on-prem):
  • CPU intensive
  • Cost: $0 (free software)
  • Speed: 2-10 seconds per image (depending on size)
  • Accuracy: 85-92%
  • Scale: Vertical (add CPU cores), horizontal (multiple servers)

Google Vision API:
  • Cloud-based, instant
  • Cost: $1.50 per 1000 images
  • Speed: <1 second per image
  • Accuracy: 96-98%
  • Scale: Unlimited (cloud)

HYBRID APPROACH:
  • Simple documents (ID cards, receipts): Tesseract
  • Complex documents (tables, forms): Google Vision
  • Load-based: High queue → Tesseract (local), quick → Google

Queue Implementation:
  1. Upload image
  2. Queue OCR job (Celery)
  3. Return immediately (async)
  4. Process in background
  5. Notify user when ready
  6. User reviews suggestions
```

### 9.2 Caching Strategy

```
Cache at multiple levels:

Level 1: Image Processing Cache
  Key: image_file_hash
  Value: processed WebP path
  TTL: Permanent (processed image reusable)

Level 2: OCR Result Cache
  Key: image_file_hash + ocr_provider
  Value: extracted fields + confidence
  TTL: Permanent (results stable)

Level 3: Validation Cache
  Key: field_value + field_type
  Value: validation_result
  TTL: 24 hours (rules may change)

Result: Reupload same image → instant result from cache
```

---

## 10. Security & Compliance

### 10.1 Sensitive Data Handling

```
PII/Sensitive Data:
  • ID numbers, passport numbers
  • Names, dates of birth
  • Addresses

Security Measures:
  • Encryption at rest (image storage)
  • Encryption in transit (HTTPS)
  • Access control (only authorized users)
  • Data masking in logs (don't log full ID numbers)
  • Audit trail (who accessed, when, why)

Compliance:
  • GDPR: User consent for data extraction
  • HIPAA: If medical documents involved
  • SOC 2: Secure processing, audit trail
  • Local regulations: Data retention laws
```

### 10.2 ID Document Processing

```
LIMITATIONS:
  ❌ Do NOT: Store ID numbers in plain text in logs
  ❌ Do NOT: Send OCR results via unencrypted email
  ❌ Do NOT: Cache sensitive fields in Redis without encryption
  ❌ Do NOT: Display full ID numbers in UI history

BEST PRACTICE:
  ✅ Do: Encrypt sensitive fields in database
  ✅ Do: Use proper HTTPS/TLS for transmission
  ✅ Do: Audit log all access to ID data
  ✅ Do: Mask ID in UI (show last 4 digits only)
  ✅ Do: Set retention period, auto-delete after
```

---

## 11. Implementation Checklist

- [ ] **OCR Provider Setup**: Tesseract or Google Vision integration
- [ ] **Image Preprocessing**: Rotation, deskew, denoise, compress to WebP
- [ ] **Field Extraction**: Regex patterns, field mapping per document type
- [ ] **Confidence Scoring**: Calculate per-field confidence (OCR + validation)
- [ ] **Validation Rules**: Format, length, checksum validation per field
- [ ] **UI Integration (STD-16)**: Present suggestions with confidence
- [ ] **User Confirmation**: Accept/edit/reject workflow
- [ ] **Audit Trail**: Track OCR results, user actions, modifications
- [ ] **Storage**: Image archival, metadata, retention policy
- [ ] **Error Handling**: Handle OCR failures, low quality, missing data
- [ ] **Security**: Encrypt sensitive data, audit access
- [ ] **Testing**: Test OCR accuracy, field extraction, validation

---

## 12. Key Takeaways

```
OCR + Image Processing = Smart Data Entry

✅ Faster: User doesn't type manually
✅ Safer: System validates extracted data
✅ Auditable: Full trail of extraction & user confirmation
✅ Scalable: Async processing, caching
✅ Flexible: Confidence-based suggestions (STD-16)

Pipeline:
  Upload → Preprocess → OCR → Extract → Validate → Suggest → Confirm → Save

Quality:
  • OCR confidence: 85-98% depending on provider
  • Field validation: Format, regex, business rules
  • User review: Final check before save
  • Audit trail: Full history visible
```

