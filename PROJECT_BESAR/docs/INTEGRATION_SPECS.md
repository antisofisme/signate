# Integration Specifications

> **Date**: 2025-12-07
> **Status**: Draft
> **Region**: Indonesia (primary), Southeast Asia (expansion)

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       INTEGRATION ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  PAYMENT INTEGRATIONS                                           │   │
│  │  - Payment Gateway (Midtrans, Xendit)                           │   │
│  │  - Bank Transfer (Virtual Account)                              │   │
│  │  - E-Wallet (GoPay, OVO, DANA)                                  │   │
│  │  - Credit Card (Visa, Mastercard)                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  TAX INTEGRATIONS                                               │   │
│  │  - e-Faktur (Electronic Invoice)                                │   │
│  │  - e-Bupot (Withholding Tax)                                    │   │
│  │  - Tax Reporting                                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  EXTERNAL SERVICES                                              │   │
│  │  - Email (SMTP, SendGrid)                                       │   │
│  │  - SMS (Twilio, local provider)                                 │   │
│  │  - Storage (Cloudflare R2)                                      │   │
│  │  - Search (Meilisearch)                                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Payment Gateway Integration

### 1.1 Supported Gateways

| Gateway | Priority | Use Case |
|---------|----------|----------|
| **Midtrans** | Primary | Full payment stack (card, VA, e-wallet) |
| **Xendit** | Secondary | Alternative gateway, disbursement |
| **Manual** | Fallback | Bank transfer verification |

### 1.2 Payment Methods

| Method | Gateway | Settlement | Notes |
|--------|---------|------------|-------|
| Credit Card | Midtrans | T+2 | Visa, Mastercard, JCB |
| Virtual Account | Midtrans | Real-time | BCA, Mandiri, BNI, BRI, Permata |
| GoPay | Midtrans | Real-time | QR code |
| QRIS | Midtrans | Real-time | Universal QR |
| OVO | Xendit | Real-time | - |
| DANA | Xendit | Real-time | - |
| Bank Transfer | Manual | Manual verification | Fallback |

### 1.3 Midtrans Integration

#### 1.3.1 Configuration

```python
# Environment variables
MIDTRANS_SERVER_KEY=SB-Mid-server-xxx
MIDTRANS_CLIENT_KEY=SB-Mid-client-xxx
MIDTRANS_MERCHANT_ID=G123456789
MIDTRANS_IS_PRODUCTION=false
MIDTRANS_NOTIFICATION_URL=https://api.domain.com/webhooks/midtrans
```

#### 1.3.2 Payment Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MIDTRANS PAYMENT FLOW                                │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐
│ Create   │───►│ Get Snap │───►│ User     │───►│ Webhook  │───►│ Update │
│ Invoice  │    │ Token    │    │ Pays     │    │ Received │    │ Status │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐
│ Invoice  │   │ Call     │   │ Redirect │   │ Verify   │   │ Mark   │
│ created  │   │ Snap API │   │ to Snap  │   │ signature│   │ invoice│
│ status:  │   │ get token│   │ page     │   │ update   │   │ as paid│
│ sent     │   │          │   │          │   │ payment  │   │        │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘
```

#### 1.3.3 Snap Token Request

```python
# Create payment request
class MidtransService:
    def __init__(self):
        self.client = midtransclient.Snap(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY,
            client_key=settings.MIDTRANS_CLIENT_KEY
        )

    async def create_transaction(self, invoice: Invoice) -> dict:
        """Create Midtrans Snap transaction"""

        param = {
            "transaction_details": {
                "order_id": invoice.invoice_number,
                "gross_amount": int(invoice.total_amount)
            },
            "customer_details": {
                "first_name": invoice.tenant.name,
                "email": invoice.tenant.billing_email,
                "phone": invoice.tenant.phone
            },
            "item_details": [
                {
                    "id": item.id,
                    "name": item.description[:50],
                    "price": int(item.unit_price),
                    "quantity": int(item.quantity)
                }
                for item in invoice.items
            ],
            "enabled_payments": [
                "credit_card", "bca_va", "bni_va", "bri_va",
                "mandiri_bill", "gopay", "qris"
            ],
            "callbacks": {
                "finish": f"https://platform.domain.com/payments/{invoice.id}/finish"
            },
            "expiry": {
                "unit": "days",
                "duration": 3
            }
        }

        transaction = self.client.create_transaction(param)
        return {
            "token": transaction["token"],
            "redirect_url": transaction["redirect_url"]
        }
```

#### 1.3.4 Webhook Handler

```python
@router.post("/webhooks/midtrans")
async def handle_midtrans_webhook(
    request: Request,
    payment_service: PaymentService = Depends()
):
    """Handle Midtrans payment notification"""

    # Get raw body for signature verification
    body = await request.body()
    notification = json.loads(body)

    # Verify signature
    order_id = notification["order_id"]
    status_code = notification["status_code"]
    gross_amount = notification["gross_amount"]
    server_key = settings.MIDTRANS_SERVER_KEY

    signature_key = hashlib.sha512(
        f"{order_id}{status_code}{gross_amount}{server_key}".encode()
    ).hexdigest()

    if signature_key != notification.get("signature_key"):
        raise HTTPException(401, "Invalid signature")

    # Process based on transaction status
    transaction_status = notification["transaction_status"]
    fraud_status = notification.get("fraud_status", "accept")

    if transaction_status == "capture":
        if fraud_status == "accept":
            await payment_service.mark_as_paid(order_id, notification)
    elif transaction_status == "settlement":
        await payment_service.mark_as_paid(order_id, notification)
    elif transaction_status in ["cancel", "deny", "expire"]:
        await payment_service.mark_as_failed(order_id, notification)
    elif transaction_status == "pending":
        await payment_service.update_pending(order_id, notification)

    return {"status": "ok"}
```

### 1.4 Xendit Integration

#### 1.4.1 Configuration

```python
XENDIT_SECRET_KEY=xnd_development_xxx
XENDIT_PUBLIC_KEY=xnd_public_development_xxx
XENDIT_CALLBACK_TOKEN=xxx
XENDIT_WEBHOOK_URL=https://api.domain.com/webhooks/xendit
```

#### 1.4.2 Virtual Account

```python
class XenditService:
    def __init__(self):
        xendit.api_key = settings.XENDIT_SECRET_KEY

    async def create_va(self, invoice: Invoice, bank_code: str) -> dict:
        """Create Xendit Virtual Account"""

        from xendit import VirtualAccount

        va = VirtualAccount.create(
            external_id=invoice.invoice_number,
            bank_code=bank_code,  # BCA, BNI, BRI, MANDIRI, PERMATA
            name=invoice.tenant.name[:20],
            expected_amount=int(invoice.total_amount),
            expiration_date=(datetime.now() + timedelta(days=3)).isoformat(),
            is_closed=True,
            is_single_use=True
        )

        return {
            "va_number": va["account_number"],
            "bank_code": va["bank_code"],
            "expected_amount": va["expected_amount"],
            "expiration_date": va["expiration_date"]
        }
```

### 1.5 Payment Database Schema

```sql
-- Payment transactions table
CREATE TABLE payment_transactions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Reference
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    payment_id INTEGER REFERENCES payments(id),

    -- Gateway info
    gateway VARCHAR(20) NOT NULL,  -- 'midtrans', 'xendit', 'manual'
    gateway_transaction_id VARCHAR(100),
    gateway_order_id VARCHAR(100),

    -- Amount
    amount DECIMAL(18,4) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',

    -- Status
    status VARCHAR(20) NOT NULL,  -- 'pending', 'success', 'failed', 'expired'
    status_message TEXT,

    -- Payment method
    payment_method VARCHAR(50),  -- 'credit_card', 'bca_va', 'gopay', etc.
    payment_channel VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE,
    expired_at TIMESTAMP WITH TIME ZONE,

    -- Raw data
    gateway_response JSONB,
    webhook_payload JSONB
);

CREATE INDEX idx_payment_trans_invoice ON payment_transactions(invoice_id);
CREATE INDEX idx_payment_trans_gateway ON payment_transactions(gateway, gateway_order_id);
```

---

## Part 2: Tax Integration (Indonesia)

### 2.1 Tax Requirements

| Tax Type | Rate | Applies To |
|----------|------|------------|
| PPN (VAT) | 11% | Subscription fees, services |
| PPh 23 | 2% | Service payments (if applicable) |
| PPh 4(2) | 10% | Rental income (property module) |

### 2.2 e-Faktur Integration

#### 2.2.1 Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    e-FAKTUR FLOW                                        │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐
│ Invoice  │───►│ Generate │───►│ Submit   │───►│ Get      │───►│ Store  │
│ Created  │    │ e-Faktur │    │ to DJP   │    │ Approval │    │ PDF    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐
│ Invoice  │   │ - NPWP   │   │ API call │   │ - Status │   │ PDF    │
│ with tax │   │ - Items  │   │ to DJP   │   │ - Nomor  │   │ signed │
│ amount   │   │ - Tax    │   │ e-Faktur │   │   Faktur │   │ by DJP │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘
```

#### 2.2.2 e-Faktur Data Structure

```python
class EFakturData(BaseModel):
    """e-Faktur submission data"""

    # Header
    nomor_faktur: str  # From NSFP allocation
    tanggal_faktur: date
    masa_pajak: int  # Month (1-12)
    tahun_pajak: int  # Year

    # Seller (PKP)
    npwp_penjual: str
    nama_penjual: str
    alamat_penjual: str

    # Buyer
    npwp_pembeli: str
    nama_pembeli: str
    alamat_pembeli: str

    # Transaction
    jenis_faktur: int  # 1 = Normal, 2 = Replacement, 3 = Cancelled
    kode_transaksi: str  # 01 = Domestic, 04 = Export, etc.

    # Items
    items: List[EFakturItem]

    # Totals
    dpp: Decimal  # Tax base (before tax)
    ppn: Decimal  # VAT amount
    total: Decimal

class EFakturItem(BaseModel):
    nama_barang: str
    harga_satuan: Decimal
    jumlah_barang: Decimal
    harga_total: Decimal
    diskon: Decimal = Decimal("0")
    dpp: Decimal
    ppn: Decimal
    tarif_ppn: Decimal = Decimal("11")  # 11%
```

#### 2.2.3 e-Faktur Service

```python
class EFakturService:
    """e-Faktur integration service"""

    def __init__(self):
        self.api_url = settings.EFAKTUR_API_URL
        self.username = settings.EFAKTUR_USERNAME
        self.password = settings.EFAKTUR_PASSWORD

    async def generate_efaktur(self, invoice: Invoice) -> EFakturResult:
        """Generate e-Faktur from invoice"""

        # 1. Get NSFP (Nomor Seri Faktur Pajak)
        nsfp = await self._get_next_nsfp(invoice.tenant_id)

        # 2. Prepare data
        efaktur_data = EFakturData(
            nomor_faktur=nsfp,
            tanggal_faktur=invoice.invoice_date,
            masa_pajak=invoice.invoice_date.month,
            tahun_pajak=invoice.invoice_date.year,
            npwp_penjual=settings.COMPANY_NPWP,
            nama_penjual=settings.COMPANY_NAME,
            alamat_penjual=settings.COMPANY_ADDRESS,
            npwp_pembeli=invoice.tenant.tax_id,
            nama_pembeli=invoice.tenant.legal_name,
            alamat_pembeli=invoice.tenant.address,
            jenis_faktur=1,
            kode_transaksi="01",
            items=[
                EFakturItem(
                    nama_barang=item.description,
                    harga_satuan=item.unit_price,
                    jumlah_barang=item.quantity,
                    harga_total=item.amount,
                    dpp=item.amount,
                    ppn=item.amount * Decimal("0.11")
                )
                for item in invoice.items
            ],
            dpp=invoice.subtotal,
            ppn=invoice.tax_amount,
            total=invoice.total_amount
        )

        # 3. Submit to DJP
        result = await self._submit_to_djp(efaktur_data)

        # 4. Store result
        await self._store_efaktur(invoice.id, result)

        return result

    async def _submit_to_djp(self, data: EFakturData) -> EFakturResult:
        """Submit e-Faktur to DJP API"""
        # Implementation depends on DJP API version
        pass

    async def download_pdf(self, invoice_id: int) -> bytes:
        """Download e-Faktur PDF"""
        pass
```

### 2.3 Tax Calculation

```python
class TaxCalculator:
    """Tax calculation service"""

    PPN_RATE = Decimal("0.11")  # 11% as of 2024
    PPH23_RATE = Decimal("0.02")  # 2% for services

    def calculate_invoice_tax(self, items: List[InvoiceItem]) -> TaxResult:
        """Calculate tax for invoice items"""

        subtotal = sum(item.amount for item in items)
        ppn = (subtotal * self.PPN_RATE).quantize(Decimal("1"))

        return TaxResult(
            subtotal=subtotal,
            tax_rate=self.PPN_RATE * 100,
            tax_amount=ppn,
            total=subtotal + ppn
        )

    def calculate_withholding_tax(
        self,
        amount: Decimal,
        tax_type: str
    ) -> Decimal:
        """Calculate withholding tax"""

        rates = {
            "pph23_service": Decimal("0.02"),  # 2%
            "pph23_royalty": Decimal("0.15"),  # 15%
            "pph4_2_rental": Decimal("0.10"),  # 10%
        }

        rate = rates.get(tax_type, Decimal("0"))
        return (amount * rate).quantize(Decimal("1"))
```

### 2.4 Tax Database Schema

```sql
-- NSFP (Nomor Seri Faktur Pajak) allocation
CREATE TABLE tax_nsfp_allocations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    prefix VARCHAR(10) NOT NULL,  -- e.g., '010.000-24'
    start_number INTEGER NOT NULL,
    end_number INTEGER NOT NULL,
    current_number INTEGER NOT NULL,
    allocated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    exhausted_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- e-Faktur records
CREATE TABLE tax_efaktur (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),

    -- Faktur info
    nomor_faktur VARCHAR(20) NOT NULL UNIQUE,
    tanggal_faktur DATE NOT NULL,
    masa_pajak INTEGER NOT NULL,
    tahun_pajak INTEGER NOT NULL,

    -- Status
    status VARCHAR(20) NOT NULL,  -- 'draft', 'submitted', 'approved', 'rejected'
    djp_response JSONB,

    -- Amounts
    dpp DECIMAL(18,4) NOT NULL,
    ppn DECIMAL(18,4) NOT NULL,
    total DECIMAL(18,4) NOT NULL,

    -- PDF
    pdf_url VARCHAR(500),
    pdf_generated_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_efaktur_invoice ON tax_efaktur(invoice_id);
CREATE INDEX idx_efaktur_tenant ON tax_efaktur(tenant_id, tahun_pajak, masa_pajak);
```

---

## Part 3: Email Integration

### 3.1 Email Provider

| Provider | Use Case | Priority |
|----------|----------|----------|
| SendGrid | Transactional emails | Primary |
| SMTP | Fallback | Secondary |
| Mailgun | Alternative | Future |

### 3.2 Email Types

| Type | Template | Trigger |
|------|----------|---------|
| Welcome | `welcome.html` | User registration |
| Email Verification | `verify_email.html` | Registration, email change |
| Password Reset | `password_reset.html` | Forgot password |
| Invoice | `invoice.html` | Invoice generated |
| Payment Confirmation | `payment_confirmed.html` | Payment received |
| Trial Expiring | `trial_expiring.html` | 3 days before trial ends |
| Subscription Expiring | `subscription_expiring.html` | 7 days before expiry |

### 3.3 Email Service

```python
class EmailService:
    """Email sending service"""

    def __init__(self):
        self.sendgrid = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.templates_path = Path("templates/email")

    async def send_email(
        self,
        to: str,
        subject: str,
        template: str,
        context: dict
    ) -> bool:
        """Send templated email"""

        # Render template
        template_path = self.templates_path / f"{template}.html"
        html_content = self._render_template(template_path, context)

        # Create message
        message = Mail(
            from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
            to_emails=to,
            subject=subject,
            html_content=html_content
        )

        # Send
        try:
            response = self.sendgrid.send(message)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            # Queue for retry
            await self._queue_for_retry(to, subject, template, context)
            return False

    async def send_invoice_email(self, invoice: Invoice):
        """Send invoice email with PDF attachment"""

        # Generate PDF
        pdf_bytes = await self.pdf_service.generate_invoice_pdf(invoice)

        # Create email with attachment
        message = Mail(
            from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
            to_emails=invoice.tenant.billing_email,
            subject=f"Invoice {invoice.invoice_number}",
            html_content=self._render_template(
                "invoice.html",
                {"invoice": invoice}
            )
        )

        # Add PDF attachment
        attachment = Attachment(
            FileContent(base64.b64encode(pdf_bytes).decode()),
            FileName(f"{invoice.invoice_number}.pdf"),
            FileType("application/pdf"),
            Disposition("attachment")
        )
        message.attachment = attachment

        return await self._send(message)
```

### 3.4 Email Queue

```python
# Celery task for async email
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def send_email_task(self, to: str, subject: str, template: str, context: dict):
    """Async email sending task"""
    try:
        email_service = EmailService()
        asyncio.run(email_service.send_email(to, subject, template, context))
    except Exception as e:
        logger.error(f"Email task failed: {e}")
        raise self.retry(exc=e)
```

---

## Part 4: SMS Integration

### 4.1 SMS Provider

| Provider | Use Case | Region |
|----------|----------|--------|
| Twilio | International | Global |
| Infobip | Local | Indonesia |
| Wavecell | Alternative | SEA |

### 4.2 SMS Types

| Type | Template | Trigger |
|------|----------|---------|
| OTP | `Your code: {code}` | Login MFA, verification |
| Payment Reminder | `Invoice {no} due...` | 3 days before due |
| Payment Received | `Payment Rp {amount}...` | Payment confirmed |

### 4.3 SMS Service

```python
class SMSService:
    """SMS sending service"""

    def __init__(self):
        self.twilio = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS message"""

        # Normalize phone number
        phone = self._normalize_phone(to)

        try:
            result = self.twilio.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
            return result.status in ["queued", "sent", "delivered"]
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    async def send_otp(self, phone: str, code: str):
        """Send OTP code"""
        message = f"Your verification code is: {code}. Valid for 5 minutes."
        return await self.send_sms(phone, message)

    def _normalize_phone(self, phone: str) -> str:
        """Normalize to E.164 format"""
        # Remove non-digits
        digits = re.sub(r'\D', '', phone)

        # Handle Indonesian numbers
        if digits.startswith('0'):
            digits = '62' + digits[1:]
        elif not digits.startswith('62'):
            digits = '62' + digits

        return '+' + digits
```

---

## Part 5: File Storage Integration

### 5.1 Storage Provider

| Provider | Use Case | Cost |
|----------|----------|------|
| Cloudflare R2 | Primary storage | Free egress |
| AWS S3 | Alternative | Standard |
| MinIO | Self-hosted | Development |

### 5.2 Storage Structure

```
bucket/
├── tenants/
│   └── {tenant_id}/
│       ├── invoices/
│       │   └── {year}/
│       │       └── {invoice_id}.pdf
│       ├── efaktur/
│       │   └── {year}/
│       │       └── {faktur_number}.pdf
│       └── documents/
│           └── {document_id}/
│               └── {filename}
├── users/
│   └── {user_id}/
│       └── avatar/
│           └── {filename}
└── system/
    └── templates/
        └── {template_name}
```

### 5.3 Storage Service

```python
class StorageService:
    """File storage service using Cloudflare R2"""

    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY,
            aws_secret_access_key=settings.R2_SECRET_KEY,
            region_name='auto'
        )
        self.bucket = settings.R2_BUCKET

    async def upload_file(
        self,
        file: bytes,
        path: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Upload file to storage"""

        self.client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=file,
            ContentType=content_type
        )

        return f"{settings.R2_PUBLIC_URL}/{path}"

    async def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Get signed URL for private file"""

        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': path},
            ExpiresIn=expires_in
        )

    async def delete_file(self, path: str):
        """Delete file from storage"""

        self.client.delete_object(
            Bucket=self.bucket,
            Key=path
        )

    async def upload_invoice_pdf(self, invoice: Invoice, pdf: bytes) -> str:
        """Upload invoice PDF"""

        path = (
            f"tenants/{invoice.tenant_id}/invoices/"
            f"{invoice.invoice_date.year}/{invoice.invoice_number}.pdf"
        )
        return await self.upload_file(pdf, path, "application/pdf")
```

---

## Part 6: Notification Integration

### 6.1 Notification Channels

| Channel | Use Case | Priority |
|---------|----------|----------|
| In-App | All notifications | Primary |
| Email | Important events | Primary |
| SMS | Critical alerts | High priority only |
| Push | Mobile app | Future |
| Webhook | External systems | On-demand |

### 6.2 Notification Service

```python
class NotificationService:
    """Multi-channel notification service"""

    def __init__(
        self,
        email_service: EmailService,
        sms_service: SMSService
    ):
        self.email = email_service
        self.sms = sms_service

    async def notify(
        self,
        user_id: int,
        notification_type: str,
        data: dict,
        channels: List[str] = None
    ):
        """Send notification through specified channels"""

        # Get user preferences
        user = await self.user_repo.get(user_id)
        preferences = await self.get_preferences(user_id)

        # Determine channels
        if channels is None:
            channels = self._get_default_channels(notification_type, preferences)

        # Create in-app notification
        await self._create_in_app(user_id, notification_type, data)

        # Send to other channels
        for channel in channels:
            if channel == "email" and user.email:
                await self._send_email_notification(user, notification_type, data)
            elif channel == "sms" and user.phone:
                await self._send_sms_notification(user, notification_type, data)
            elif channel == "webhook":
                await self._send_webhook(user_id, notification_type, data)

    NOTIFICATION_TEMPLATES = {
        "invoice_generated": {
            "title": "New Invoice Generated",
            "email_template": "invoice_notification",
            "sms_template": "Invoice {invoice_number} for Rp {amount} has been generated. Due: {due_date}",
            "channels": ["in_app", "email"]
        },
        "payment_received": {
            "title": "Payment Received",
            "email_template": "payment_confirmation",
            "sms_template": "Payment of Rp {amount} received for invoice {invoice_number}. Thank you!",
            "channels": ["in_app", "email", "sms"]
        },
        "trial_expiring": {
            "title": "Trial Expiring Soon",
            "email_template": "trial_expiring",
            "channels": ["in_app", "email"]
        }
    }
```

---

## Part 7: Webhook Integration

### 7.1 Outgoing Webhooks

| Event | Payload | Use Case |
|-------|---------|----------|
| `tenant.created` | Tenant data | External CRM |
| `invoice.created` | Invoice data | Accounting system |
| `payment.received` | Payment data | ERP integration |
| `subscription.changed` | Subscription data | License management |

### 7.2 Webhook Configuration

```sql
-- Webhook endpoints table
CREATE TABLE webhook_endpoints (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),

    -- Endpoint
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(100) NOT NULL,  -- For signature

    -- Events
    events JSONB NOT NULL,  -- ["invoice.created", "payment.received"]

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER REFERENCES users(id)
);

-- Webhook delivery log
CREATE TABLE webhook_deliveries (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    endpoint_id INTEGER NOT NULL REFERENCES webhook_endpoints(id),

    -- Event
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,

    -- Delivery
    status VARCHAR(20) NOT NULL,  -- 'pending', 'success', 'failed'
    response_code INTEGER,
    response_body TEXT,
    attempts INTEGER DEFAULT 0,

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE
);
```

### 7.3 Webhook Service

```python
class WebhookService:
    """Outgoing webhook service"""

    async def trigger(self, event_type: str, tenant_id: int, data: dict):
        """Trigger webhooks for event"""

        # Find matching endpoints
        endpoints = await self.endpoint_repo.find_by_event(tenant_id, event_type)

        for endpoint in endpoints:
            if not endpoint.is_active:
                continue

            # Create delivery record
            delivery = await self.delivery_repo.create({
                "endpoint_id": endpoint.id,
                "event_type": event_type,
                "payload": data
            })

            # Queue for async delivery
            await self.queue_delivery(delivery.id)

    async def deliver(self, delivery_id: int):
        """Deliver webhook"""

        delivery = await self.delivery_repo.get(delivery_id)
        endpoint = await self.endpoint_repo.get(delivery.endpoint_id)

        # Prepare payload
        payload = {
            "event": delivery.event_type,
            "timestamp": datetime.now().isoformat(),
            "data": delivery.payload
        }

        # Generate signature
        signature = hmac.new(
            endpoint.secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()

        # Send request
        try:
            response = await self.http_client.post(
                endpoint.url,
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Event": delivery.event_type
                },
                timeout=30
            )

            await self.delivery_repo.update(delivery_id, {
                "status": "success" if response.status_code < 300 else "failed",
                "response_code": response.status_code,
                "response_body": response.text[:1000],
                "delivered_at": datetime.now(),
                "attempts": delivery.attempts + 1
            })

        except Exception as e:
            await self._handle_failure(delivery_id, str(e))

    async def _handle_failure(self, delivery_id: int, error: str):
        """Handle delivery failure with exponential backoff"""

        delivery = await self.delivery_repo.get(delivery_id)
        attempts = delivery.attempts + 1

        if attempts >= 5:
            # Max retries reached
            await self.delivery_repo.update(delivery_id, {
                "status": "failed",
                "attempts": attempts,
                "response_body": error
            })
            return

        # Exponential backoff: 1min, 5min, 30min, 2h
        delays = [60, 300, 1800, 7200]
        next_retry = datetime.now() + timedelta(seconds=delays[attempts - 1])

        await self.delivery_repo.update(delivery_id, {
            "status": "pending",
            "attempts": attempts,
            "next_retry_at": next_retry
        })
```

---

## Part 8: Third-Party API Standards

### 8.1 API Client Pattern

```python
class BaseAPIClient:
    """Base class for third-party API clients"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"}
        )

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> dict:
        """Make API request with error handling"""

        try:
            response = await self.session.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"API error: {e.response.status_code} - {e.response.text}")
            raise ExternalAPIError(
                service=self.__class__.__name__,
                status_code=e.response.status_code,
                message=e.response.text
            )

        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise ExternalAPIError(
                service=self.__class__.__name__,
                status_code=0,
                message=str(e)
            )

    async def close(self):
        await self.session.aclose()
```

### 8.2 Circuit Breaker

```python
class CircuitBreaker:
    """Circuit breaker for external API calls"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker"""

        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failures = 0
        self.state = "closed"

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.failures >= self.failure_threshold:
            self.state = "open"

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
```

---

*Last Updated: 2025-12-07*
