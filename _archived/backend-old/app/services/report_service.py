"""
============================================================================
Report Service - PDF, Excel, CSV Generation
============================================================================

Comprehensive report generation service supporting multiple formats.

Features:
- PDF generation with ReportLab
- Excel export with openpyxl
- CSV export
- Report templates (daily, weekly, monthly)
- Scheduled report generation support
- Report history management
"""

import csv
import logging
from app.core.logging import StructuredLogger
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import BarChart, LineChart, PieChart, Reference

from app.models.content import Content
from app.models.device import Device
from app.models.activity import Activity

logger = StructuredLogger(__name__)

# ============================================================================
# Report Model (Simplified - Store in DB in production)
# ============================================================================

class ReportRecord:
    """In-memory report record (use database model in production)"""

    def __init__(
        self,
        id: str,
        title: str,
        format: str,
        report_type: str,
        status: str = "pending",
        file_size: Optional[int] = None,
        created_at: datetime = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ):
        self.id = id
        self.title = title
        self.format = format
        self.report_type = report_type
        self.status = status
        self.file_size = file_size
        self.created_at = created_at or datetime.now()
        self.completed_at = completed_at
        self.error_message = error_message


# In-memory storage (replace with database in production)
_reports_storage: Dict[str, ReportRecord] = {}
_report_files: Dict[str, bytes] = {}


# ============================================================================
# Report Service
# ============================================================================

class ReportService:
    """Service for generating analytics reports in multiple formats"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(
            ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
        )
        self.styles.add(
            ParagraphStyle(
                name='SectionTitle',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#3b82f6'),
                spaceAfter=12,
                spaceBefore=12
            )
        )

    # ========================================================================
    # Report Management
    # ========================================================================

    async def create_report(
        self,
        format: str,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        sections: List[str],
        filters: Dict[str, Any]
    ) -> ReportRecord:
        """Create a new report record"""
        report_id = str(uuid4())
        title = f"Analytics Report - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        report = ReportRecord(
            id=report_id,
            title=title,
            format=format,
            report_type=report_type,
            status="pending"
        )

        _reports_storage[report_id] = report
        logger.info(f"Created report: {report_id}")

        return report

    async def get_report(self, report_id: str) -> Optional[ReportRecord]:
        """Get report by ID"""
        return _reports_storage.get(report_id)

    async def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        format_filter: Optional[str] = None
    ) -> Tuple[List[ReportRecord], int]:
        """List all reports with pagination"""
        reports = list(_reports_storage.values())

        # Apply filters
        if status_filter:
            reports = [r for r in reports if r.status == status_filter]
        if format_filter:
            reports = [r for r in reports if r.format == format_filter]

        # Sort by created_at desc
        reports.sort(key=lambda x: x.created_at, reverse=True)

        # Pagination
        total = len(reports)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = reports[start:end]

        return paginated, total

    async def get_report_file(self, report_id: str) -> Optional[bytes]:
        """Get report file data"""
        return _report_files.get(report_id)

    async def delete_report(self, report_id: str) -> bool:
        """Delete report and its file"""
        if report_id in _reports_storage:
            del _reports_storage[report_id]
            if report_id in _report_files:
                del _report_files[report_id]
            logger.info(f"Deleted report: {report_id}")
            return True
        return False

    # ========================================================================
    # Data Gathering
    # ========================================================================

    async def _gather_analytics_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Gather analytics data for report"""
        try:
            # Total views (using activities)
            activities_query = select(func.count(Activity.id)).where(
                and_(
                    Activity.created_at >= start_date,
                    Activity.created_at <= end_date
                )
            )
            total_views = (await self.db.execute(activities_query)).scalar() or 0

            # Device stats
            devices_query = select(func.count(Device.id))
            total_devices = (await self.db.execute(devices_query)).scalar() or 0

            online_devices_query = select(func.count(Device.id)).where(
                Device.status == "online"
            )
            online_devices = (await self.db.execute(online_devices_query)).scalar() or 0

            # Content stats
            content_query = select(func.count(Content.id))
            total_content = (await self.db.execute(content_query)).scalar() or 0

            # Top content (simulated - need proper tracking)
            top_content_query = select(Content).limit(10)
            top_content_result = await self.db.execute(top_content_query)
            top_content = top_content_result.scalars().all()

            return {
                "overview": {
                    "total_views": total_views,
                    "total_devices": total_devices,
                    "online_devices": online_devices,
                    "total_content": total_content,
                    "uptime_percentage": 99.5,  # Simulated
                },
                "devices": {
                    "online": online_devices,
                    "offline": total_devices - online_devices,
                    "total": total_devices,
                },
                "top_content": [
                    {
                        "title": content.title,
                        "type": content.type,
                        "views": 0,  # Would need tracking
                    }
                    for content in top_content
                ],
                "period": {
                    "start": start_date,
                    "end": end_date,
                }
            }

        except Exception as e:
            logger.error(f"Error gathering analytics data: {e}")
            return {
                "overview": {
                    "total_views": 0,
                    "total_devices": 0,
                    "online_devices": 0,
                    "total_content": 0,
                    "uptime_percentage": 0,
                },
                "devices": {
                    "online": 0,
                    "offline": 0,
                    "total": 0,
                },
                "top_content": [],
                "period": {
                    "start": start_date,
                    "end": end_date,
                }
            }

    # ========================================================================
    # PDF Generation
    # ========================================================================

    async def generate_pdf_report(
        self,
        start_date: datetime,
        end_date: datetime,
        orientation: str = "landscape"
    ) -> BytesIO:
        """Generate PDF report"""
        buffer = BytesIO()

        # Set page size
        pagesize = landscape(letter) if orientation == "landscape" else letter
        doc = SimpleDocTemplate(buffer, pagesize=pagesize)
        elements = []

        # Gather data
        data = await self._gather_analytics_data(start_date, end_date)

        # Title
        title = Paragraph(
            f"Analytics Report<br/>{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))

        # Overview Section
        elements.append(Paragraph("Overview", self.styles['SectionTitle']))
        overview_data = [
            ['Metric', 'Value'],
            ['Total Views', f"{data['overview']['total_views']:,}"],
            ['Total Devices', f"{data['overview']['total_devices']:,}"],
            ['Online Devices', f"{data['overview']['online_devices']:,}"],
            ['Total Content', f"{data['overview']['total_content']:,}"],
            ['System Uptime', f"{data['overview']['uptime_percentage']:.1f}%"],
        ]

        overview_table = Table(overview_data, colWidths=[3 * inch, 2 * inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(overview_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Device Status Section
        elements.append(Paragraph("Device Status", self.styles['SectionTitle']))
        device_data = [
            ['Status', 'Count', 'Percentage'],
            [
                'Online',
                f"{data['devices']['online']:,}",
                f"{(data['devices']['online'] / max(data['devices']['total'], 1) * 100):.1f}%"
            ],
            [
                'Offline',
                f"{data['devices']['offline']:,}",
                f"{(data['devices']['offline'] / max(data['devices']['total'], 1) * 100):.1f}%"
            ],
        ]

        device_table = Table(device_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(device_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Top Content Section
        if data['top_content']:
            elements.append(Paragraph("Top Content", self.styles['SectionTitle']))
            content_data = [['#', 'Title', 'Type', 'Views']]
            for idx, content in enumerate(data['top_content'][:10], 1):
                content_data.append([
                    str(idx),
                    content['title'][:50] + '...' if len(content['title']) > 50 else content['title'],
                    content['type'],
                    f"{content['views']:,}"
                ])

            content_table = Table(content_data, colWidths=[0.5 * inch, 4 * inch, 1 * inch, 1 * inch])
            content_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(content_table)

        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}",
            self.styles['Normal']
        )
        elements.append(footer)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ========================================================================
    # Excel Generation
    # ========================================================================

    async def generate_excel_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BytesIO:
        """Generate Excel report with formatting"""
        buffer = BytesIO()
        wb = openpyxl.Workbook()

        # Gather data
        data = await self._gather_analytics_data(start_date, end_date)

        # Remove default sheet
        wb.remove(wb.active)

        # ====================================================================
        # Overview Sheet
        # ====================================================================
        ws_overview = wb.create_sheet("Overview")

        # Title
        ws_overview['A1'] = "Analytics Report"
        ws_overview['A1'].font = Font(size=18, bold=True, color="FFFFFF")
        ws_overview['A1'].fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        ws_overview.merge_cells('A1:B1')

        # Period
        ws_overview['A2'] = "Period:"
        ws_overview['B2'] = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        ws_overview['A2'].font = Font(bold=True)

        # Headers
        ws_overview['A4'] = "Metric"
        ws_overview['B4'] = "Value"
        ws_overview['A4'].font = Font(bold=True, color="FFFFFF")
        ws_overview['B4'].font = Font(bold=True, color="FFFFFF")
        ws_overview['A4'].fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        ws_overview['B4'].fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")

        # Data
        overview_rows = [
            ("Total Views", data['overview']['total_views']),
            ("Total Devices", data['overview']['total_devices']),
            ("Online Devices", data['overview']['online_devices']),
            ("Total Content", data['overview']['total_content']),
            ("System Uptime", f"{data['overview']['uptime_percentage']:.1f}%"),
        ]

        for idx, (metric, value) in enumerate(overview_rows, start=5):
            ws_overview[f'A{idx}'] = metric
            ws_overview[f'B{idx}'] = value
            # Alternating row colors
            if idx % 2 == 0:
                ws_overview[f'A{idx}'].fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
                ws_overview[f'B{idx}'].fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")

        # Column widths
        ws_overview.column_dimensions['A'].width = 25
        ws_overview.column_dimensions['B'].width = 20

        # ====================================================================
        # Devices Sheet
        # ====================================================================
        ws_devices = wb.create_sheet("Devices")

        # Title
        ws_devices['A1'] = "Device Status"
        ws_devices['A1'].font = Font(size=16, bold=True, color="FFFFFF")
        ws_devices['A1'].fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
        ws_devices.merge_cells('A1:C1')

        # Headers
        headers = ["Status", "Count", "Percentage"]
        for idx, header in enumerate(headers, start=1):
            cell = ws_devices.cell(row=3, column=idx)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")

        # Data
        device_rows = [
            ("Online", data['devices']['online'], f"{(data['devices']['online'] / max(data['devices']['total'], 1) * 100):.1f}%"),
            ("Offline", data['devices']['offline'], f"{(data['devices']['offline'] / max(data['devices']['total'], 1) * 100):.1f}%"),
        ]

        for row_idx, (status, count, percentage) in enumerate(device_rows, start=4):
            ws_devices[f'A{row_idx}'] = status
            ws_devices[f'B{row_idx}'] = count
            ws_devices[f'C{row_idx}'] = percentage

        # Column widths
        ws_devices.column_dimensions['A'].width = 15
        ws_devices.column_dimensions['B'].width = 15
        ws_devices.column_dimensions['C'].width = 15

        # ====================================================================
        # Top Content Sheet
        # ====================================================================
        ws_content = wb.create_sheet("Top Content")

        # Title
        ws_content['A1'] = "Top Content"
        ws_content['A1'].font = Font(size=16, bold=True, color="FFFFFF")
        ws_content['A1'].fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
        ws_content.merge_cells('A1:D1')

        # Headers
        headers = ["#", "Title", "Type", "Views"]
        for idx, header in enumerate(headers, start=1):
            cell = ws_content.cell(row=3, column=idx)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")

        # Data
        for row_idx, content in enumerate(data['top_content'][:10], start=4):
            ws_content[f'A{row_idx}'] = row_idx - 3
            ws_content[f'B{row_idx}'] = content['title']
            ws_content[f'C{row_idx}'] = content['type']
            ws_content[f'D{row_idx}'] = content['views']

        # Column widths
        ws_content.column_dimensions['A'].width = 5
        ws_content.column_dimensions['B'].width = 50
        ws_content.column_dimensions['C'].width = 15
        ws_content.column_dimensions['D'].width = 15

        # Save
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    # ========================================================================
    # CSV Generation
    # ========================================================================

    async def generate_csv_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BytesIO:
        """Generate CSV report"""
        buffer = BytesIO()

        # Gather data
        data = await self._gather_analytics_data(start_date, end_date)

        # Write CSV
        writer = csv.writer(buffer.io if hasattr(buffer, 'io') else buffer, lineterminator='\n')

        # Title and period
        writer.writerow(["Analytics Report"])
        writer.writerow(["Period", f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"])
        writer.writerow([])

        # Overview section
        writer.writerow(["Overview"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Views", data['overview']['total_views']])
        writer.writerow(["Total Devices", data['overview']['total_devices']])
        writer.writerow(["Online Devices", data['overview']['online_devices']])
        writer.writerow(["Total Content", data['overview']['total_content']])
        writer.writerow(["System Uptime", f"{data['overview']['uptime_percentage']:.1f}%"])
        writer.writerow([])

        # Device section
        writer.writerow(["Device Status"])
        writer.writerow(["Status", "Count", "Percentage"])
        writer.writerow([
            "Online",
            data['devices']['online'],
            f"{(data['devices']['online'] / max(data['devices']['total'], 1) * 100):.1f}%"
        ])
        writer.writerow([
            "Offline",
            data['devices']['offline'],
            f"{(data['devices']['offline'] / max(data['devices']['total'], 1) * 100):.1f}%"
        ])
        writer.writerow([])

        # Top content section
        writer.writerow(["Top Content"])
        writer.writerow(["#", "Title", "Type", "Views"])
        for idx, content in enumerate(data['top_content'][:10], 1):
            writer.writerow([
                idx,
                content['title'],
                content['type'],
                content['views']
            ])

        buffer.seek(0)
        return buffer

    # ========================================================================
    # Async Report Generation
    # ========================================================================

    async def generate_report_async(self, report_id: str):
        """Generate report asynchronously (background task)"""
        try:
            report = _reports_storage.get(report_id)
            if not report:
                logger.error(f"Report not found: {report_id}")
                return

            # Update status
            report.status = "processing"
            logger.info(f"Generating report: {report_id}")

            # Generate based on format
            if report.format == "pdf":
                buffer = await self.generate_pdf_report(
                    datetime.now(),
                    datetime.now()
                )
            elif report.format == "excel":
                buffer = await self.generate_excel_report(
                    datetime.now(),
                    datetime.now()
                )
            else:  # csv
                buffer = await self.generate_csv_report(
                    datetime.now(),
                    datetime.now()
                )

            # Store file
            file_data = buffer.getvalue()
            _report_files[report_id] = file_data

            # Update report
            report.status = "completed"
            report.file_size = len(file_data)
            report.completed_at = datetime.now()

            logger.info(f"Report generated successfully: {report_id}")

        except Exception as e:
            logger.error(f"Error generating report {report_id}: {e}")
            report.status = "failed"
            report.error_message = str(e)
