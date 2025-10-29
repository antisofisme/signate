# Phase 4.4: Analytics & Reporting System Design

## Executive Summary

### Business Value
The Analytics & Reporting System will provide enterprise-grade insights into content performance, device health, and system efficiency for a Digital Signage platform managing 500+ devices. This system will enable:
- **Data-driven content optimization** - Understanding which content resonates with audiences
- **Proactive device management** - Detecting and preventing failures before they impact service
- **ROI measurement** - Quantifying the effectiveness of digital signage campaigns
- **Operational efficiency** - Identifying patterns and optimizing resource allocation

### Technical Approach
We'll implement a hybrid real-time and batch processing architecture using:
- **Event streaming** for real-time data collection (30-second heartbeats, playback events)
- **Time-series optimized storage** with PostgreSQL partitioning and TimescaleDB extension
- **Pre-aggregated materialized views** for dashboard performance
- **Background jobs** for report generation and alerting
- **Redis caching** for real-time metrics and WebSocket distribution

### Implementation Complexity
- **Moderate to High** - Requires careful database design, efficient data collection, and optimized query patterns
- **Timeline**: 6-8 weeks for full implementation
- **Team Requirements**: 1-2 backend developers, 1 frontend developer, 1 data engineer

## Data Collection Architecture

### Events to Track

#### 1. Device Events
```python
class DeviceEvent:
    device_id: int
    event_type: str  # "heartbeat", "boot", "shutdown", "error", "network_change"
    timestamp: datetime
    metadata: dict = {
        "ip_address": str,
        "firmware_version": str,
        "memory_usage": float,
        "cpu_usage": float,
        "storage_available": int,
        "network_speed": float,
        "screen_status": str,  # "on", "off", "standby"
        "temperature": float,  # Hardware temperature if available
        "location": dict  # GPS coordinates if available
    }
```

#### 2. Content Playback Events
```python
class PlaybackEvent:
    device_id: int
    content_id: int
    playlist_id: Optional[int]
    event_type: str  # "start", "progress", "complete", "error", "skip"
    timestamp: datetime
    metadata: dict = {
        "duration_watched": int,  # seconds
        "total_duration": int,  # seconds
        "buffer_events": int,
        "quality_switches": int,
        "average_bitrate": float,
        "completion_rate": float,  # 0.0 to 1.0
        "user_interaction": bool,  # Did user manually interact?
    }
```

#### 3. System Events
```python
class SystemEvent:
    event_type: str  # "api_call", "cache_hit", "error", "deployment"
    timestamp: datetime
    metadata: dict = {
        "endpoint": str,
        "method": str,
        "status_code": int,
        "response_time": float,
        "user_id": Optional[int],
        "error_message": Optional[str],
    }
```

### Collection Mechanism

#### Real-time Collection Pipeline
```python
# FastAPI WebSocket endpoint for device events
@app.websocket("/ws/analytics/{device_id}")
async def analytics_websocket(websocket: WebSocket, device_id: int):
    await manager.connect(device_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Validate and enrich event data
            event = validate_event(data)
            event['server_timestamp'] = datetime.utcnow()

            # Write to event queue
            await redis.xadd(f"events:{event['type']}", event)

            # Update real-time metrics
            await update_real_time_metrics(event)

            # Trigger alerts if needed
            await check_alert_conditions(event)
    except WebSocketDisconnect:
        manager.disconnect(device_id)
```

#### Batch Collection Workers
```python
# Background worker for processing event queue
async def process_analytics_queue():
    while True:
        # Read batch of events from Redis stream
        events = await redis.xread({"events:*": "$"}, count=100, block=1000)

        if events:
            # Batch insert to PostgreSQL
            async with db.begin() as conn:
                await conn.execute(
                    insert(analytics_events).values(events)
                )

            # Update aggregations
            await update_aggregations(events)
```

## Data Storage Design

### Database Schema

#### Core Tables

```sql
-- Time-series events table (partitioned by month)
CREATE TABLE analytics_events (
    id BIGSERIAL,
    event_id UUID DEFAULT gen_random_uuid(),
    device_id INTEGER,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    server_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE analytics_events_2025_01 PARTITION OF analytics_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Indexes for fast querying
CREATE INDEX idx_events_device_timestamp ON analytics_events (device_id, timestamp DESC);
CREATE INDEX idx_events_type_timestamp ON analytics_events (event_type, timestamp DESC);
CREATE INDEX idx_events_metadata_gin ON analytics_events USING gin(metadata);

-- Content analytics aggregation
CREATE TABLE content_analytics (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES content(id),
    date DATE NOT NULL,
    total_plays INTEGER DEFAULT 0,
    unique_devices INTEGER DEFAULT 0,
    total_watch_time INTEGER DEFAULT 0,  -- seconds
    avg_completion_rate DECIMAL(5,2) DEFAULT 0,
    skip_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    peak_concurrent_viewers INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(content_id, date)
);

-- Device analytics aggregation
CREATE TABLE device_analytics (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id),
    date DATE NOT NULL,
    uptime_seconds INTEGER DEFAULT 0,
    online_count INTEGER DEFAULT 0,
    offline_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_cpu_usage DECIMAL(5,2),
    avg_memory_usage DECIMAL(5,2),
    total_bandwidth_mb INTEGER DEFAULT 0,
    content_played INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(device_id, date)
);

-- Alert rules configuration
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- "threshold", "anomaly", "pattern"
    entity_type VARCHAR(50),  -- "device", "content", "system"
    condition JSONB NOT NULL,  -- Rule configuration
    actions JSONB NOT NULL,  -- What to do when triggered
    severity VARCHAR(20) DEFAULT 'warning',  -- "info", "warning", "critical"
    is_active BOOLEAN DEFAULT true,
    cooldown_minutes INTEGER DEFAULT 15,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alert history
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alert_rules(id),
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    entity_id INTEGER,
    entity_type VARCHAR(50),
    alert_data JSONB,
    notification_sent BOOLEAN DEFAULT false,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ
);

-- Report templates
CREATE TABLE report_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL,  -- "dashboard", "summary", "detailed"
    config JSONB NOT NULL,  -- Report configuration
    schedule_cron VARCHAR(50),  -- Cron expression for scheduled reports
    recipients JSONB,  -- Email addresses or webhook URLs
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generated reports
CREATE TABLE generated_reports (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES report_templates(id),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    status VARCHAR(20) DEFAULT 'pending',  -- "pending", "processing", "completed", "failed"
    error_message TEXT,
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMPTZ
);
```

### Materialized Views for Performance

```sql
-- Real-time dashboard view (refreshed every 5 minutes)
CREATE MATERIALIZED VIEW mv_dashboard_stats AS
SELECT
    -- Device stats
    COUNT(DISTINCT d.id) as total_devices,
    COUNT(DISTINCT CASE WHEN d.last_seen > NOW() - INTERVAL '5 minutes' THEN d.id END) as online_devices,
    COUNT(DISTINCT CASE WHEN d.status = 'maintenance' THEN d.id END) as maintenance_devices,

    -- Content stats
    COUNT(DISTINCT c.id) as total_content,
    SUM(c.file_size_mb) as total_storage_mb,
    COUNT(DISTINCT CASE WHEN c.content_type = 'video' THEN c.id END) as video_count,
    COUNT(DISTINCT CASE WHEN c.content_type = 'image' THEN c.id END) as image_count,

    -- Playback stats (last 24h)
    (SELECT COUNT(*) FROM analytics_events
     WHERE event_type = 'playback_start'
     AND timestamp > NOW() - INTERVAL '24 hours') as plays_24h,

    -- System health
    (SELECT AVG(response_time) FROM analytics_events
     WHERE event_type = 'api_call'
     AND timestamp > NOW() - INTERVAL '1 hour') as avg_api_response_ms,

    NOW() as last_updated
FROM devices d
CROSS JOIN content c;

CREATE INDEX idx_mv_dashboard_stats_updated ON mv_dashboard_stats(last_updated);

-- Top content view (refreshed hourly)
CREATE MATERIALIZED VIEW mv_top_content AS
SELECT
    c.id,
    c.name,
    c.content_type,
    c.duration_seconds,
    COUNT(DISTINCT ae.device_id) as unique_viewers,
    COUNT(*) as total_plays,
    AVG((ae.metadata->>'completion_rate')::float) as avg_completion,
    SUM((ae.metadata->>'duration_watched')::int) as total_watch_seconds
FROM content c
LEFT JOIN analytics_events ae ON ae.metadata->>'content_id' = c.id::text
    AND ae.event_type = 'playback_complete'
    AND ae.timestamp > NOW() - INTERVAL '7 days'
GROUP BY c.id, c.name, c.content_type, c.duration_seconds
ORDER BY total_plays DESC;
```

### Partitioning Strategy

```sql
-- Automatic partition creation function
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_name text;
    start_date date;
    end_date date;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE);
    end_date := start_date + interval '1 month';
    partition_name := 'analytics_events_' || to_char(start_date, 'YYYY_MM');

    -- Check if partition exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF analytics_events FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly partition creation
CREATE EXTENSION IF NOT EXISTS pg_cron;
SELECT cron.schedule('create-partitions', '0 0 1 * *', 'SELECT create_monthly_partition()');
```

### Retention Policy

```sql
-- Drop old partitions after 12 months
CREATE OR REPLACE FUNCTION drop_old_partitions()
RETURNS void AS $$
DECLARE
    partition record;
BEGIN
    FOR partition IN
        SELECT tablename
        FROM pg_tables
        WHERE tablename LIKE 'analytics_events_%'
        AND tablename < 'analytics_events_' || to_char(CURRENT_DATE - INTERVAL '12 months', 'YYYY_MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I', partition.tablename);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly cleanup
SELECT cron.schedule('cleanup-partitions', '0 1 1 * *', 'SELECT drop_old_partitions()');
```

## Analytics Queries

### Pre-aggregation Strategy

```python
# Aggregation service that runs every 5 minutes
class AggregationService:
    async def aggregate_content_stats(self, date: datetime.date):
        """Pre-aggregate content statistics for faster querying"""
        query = """
            INSERT INTO content_analytics (
                content_id, date, total_plays, unique_devices,
                total_watch_time, avg_completion_rate, skip_count, error_count
            )
            SELECT
                (metadata->>'content_id')::int as content_id,
                DATE(timestamp) as date,
                COUNT(*) FILTER (WHERE event_type = 'playback_start') as total_plays,
                COUNT(DISTINCT device_id) as unique_devices,
                SUM((metadata->>'duration_watched')::int) as total_watch_time,
                AVG((metadata->>'completion_rate')::float) as avg_completion_rate,
                COUNT(*) FILTER (WHERE event_type = 'playback_skip') as skip_count,
                COUNT(*) FILTER (WHERE event_type = 'playback_error') as error_count
            FROM analytics_events
            WHERE DATE(timestamp) = $1
                AND event_category = 'playback'
            GROUP BY content_id, date
            ON CONFLICT (content_id, date)
            DO UPDATE SET
                total_plays = EXCLUDED.total_plays,
                unique_devices = EXCLUDED.unique_devices,
                total_watch_time = EXCLUDED.total_watch_time,
                avg_completion_rate = EXCLUDED.avg_completion_rate,
                skip_count = EXCLUDED.skip_count,
                error_count = EXCLUDED.error_count,
                updated_at = NOW()
        """
        await db.execute(query, date)

    async def aggregate_device_stats(self, date: datetime.date):
        """Pre-aggregate device statistics"""
        query = """
            INSERT INTO device_analytics (
                device_id, date, uptime_seconds, online_count,
                offline_count, error_count, avg_cpu_usage,
                avg_memory_usage, total_bandwidth_mb, content_played
            )
            SELECT
                device_id,
                DATE(timestamp) as date,
                COUNT(*) * 30 as uptime_seconds,  -- Heartbeat every 30s
                COUNT(*) FILTER (WHERE event_type = 'heartbeat') as online_count,
                COUNT(*) FILTER (WHERE event_type = 'disconnect') as offline_count,
                COUNT(*) FILTER (WHERE event_type = 'error') as error_count,
                AVG((metadata->>'cpu_usage')::float) as avg_cpu_usage,
                AVG((metadata->>'memory_usage')::float) as avg_memory_usage,
                SUM((metadata->>'bandwidth_kb')::int) / 1024 as total_bandwidth_mb,
                COUNT(DISTINCT metadata->>'content_id') as content_played
            FROM analytics_events
            WHERE DATE(timestamp) = $1
                AND device_id IS NOT NULL
            GROUP BY device_id, date
            ON CONFLICT (device_id, date)
            DO UPDATE SET
                uptime_seconds = EXCLUDED.uptime_seconds,
                online_count = EXCLUDED.online_count,
                offline_count = EXCLUDED.offline_count,
                error_count = EXCLUDED.error_count,
                avg_cpu_usage = EXCLUDED.avg_cpu_usage,
                avg_memory_usage = EXCLUDED.avg_memory_usage,
                total_bandwidth_mb = EXCLUDED.total_bandwidth_mb,
                content_played = EXCLUDED.content_played,
                updated_at = NOW()
        """
        await db.execute(query, date)
```

### Query Patterns

```python
# High-performance query examples
class AnalyticsQueries:
    @staticmethod
    async def get_content_performance(content_id: int, days: int = 30):
        """Get content performance metrics"""
        query = """
            SELECT
                date,
                total_plays,
                unique_devices,
                total_watch_time,
                avg_completion_rate,
                skip_count,
                error_count
            FROM content_analytics
            WHERE content_id = $1
                AND date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY date DESC
        """
        return await db.fetch_all(query % days, content_id)

    @staticmethod
    async def get_device_uptime(device_id: int, period: str = '24h'):
        """Calculate device uptime percentage"""
        query = """
            WITH heartbeats AS (
                SELECT
                    timestamp,
                    LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp
                FROM analytics_events
                WHERE device_id = $1
                    AND event_type = 'heartbeat'
                    AND timestamp > NOW() - INTERVAL $2
            )
            SELECT
                COUNT(*) * 30 as expected_seconds,
                SUM(
                    CASE
                        WHEN EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) <= 45
                        THEN 30
                        ELSE 0
                    END
                ) as actual_seconds
            FROM heartbeats
        """
        result = await db.fetch_one(query, device_id, period)
        return (result['actual_seconds'] / result['expected_seconds']) * 100 if result else 0

    @staticmethod
    async def get_peak_viewing_hours():
        """Identify peak content viewing hours"""
        query = """
            SELECT
                EXTRACT(HOUR FROM timestamp) as hour,
                COUNT(*) as play_count,
                COUNT(DISTINCT device_id) as unique_devices
            FROM analytics_events
            WHERE event_type = 'playback_start'
                AND timestamp > NOW() - INTERVAL '7 days'
            GROUP BY hour
            ORDER BY play_count DESC
        """
        return await db.fetch_all(query)
```

## Dashboard Design

### Real-time Dashboard Widgets

```typescript
// Dashboard component structure
interface DashboardWidget {
    id: string;
    type: 'metric' | 'chart' | 'map' | 'table' | 'timeline';
    title: string;
    refreshInterval: number;  // seconds
    dataSource: string;  // API endpoint
    config: WidgetConfig;
}

interface WidgetConfig {
    // Metric widget
    metric?: {
        value: number;
        change: number;
        changeType: 'increase' | 'decrease';
        format: 'number' | 'percentage' | 'currency' | 'duration';
    };

    // Chart widget
    chart?: {
        type: 'line' | 'bar' | 'pie' | 'area' | 'heatmap';
        xAxis: string;
        yAxis: string;
        series: ChartSeries[];
    };

    // Map widget
    map?: {
        center: [number, number];
        zoom: number;
        markers: MapMarker[];
    };
}

// Example dashboard configuration
const dashboardConfig: DashboardWidget[] = [
    {
        id: 'online-devices',
        type: 'metric',
        title: 'Online Devices',
        refreshInterval: 30,
        dataSource: '/api/analytics/devices/online',
        config: {
            metric: {
                value: 485,
                change: 5.2,
                changeType: 'increase',
                format: 'number'
            }
        }
    },
    {
        id: 'content-plays-chart',
        type: 'chart',
        title: 'Content Plays (24h)',
        refreshInterval: 300,
        dataSource: '/api/analytics/content/plays',
        config: {
            chart: {
                type: 'area',
                xAxis: 'time',
                yAxis: 'plays',
                series: [{
                    name: 'Video',
                    data: []
                }, {
                    name: 'Image',
                    data: []
                }]
            }
        }
    },
    {
        id: 'device-map',
        type: 'map',
        title: 'Device Locations',
        refreshInterval: 60,
        dataSource: '/api/analytics/devices/map',
        config: {
            map: {
                center: [40.7128, -74.0060],
                zoom: 10,
                markers: []
            }
        }
    }
];
```

### Real-time Updates

```typescript
// WebSocket connection for real-time updates
class DashboardWebSocket {
    private ws: WebSocket;
    private subscribers: Map<string, Function[]> = new Map();

    connect() {
        this.ws = new WebSocket('ws://192.168.5.12:8001/ws/analytics/dashboard');

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.notifySubscribers(data.widget_id, data.payload);
        };

        // Reconnect on disconnect
        this.ws.onclose = () => {
            setTimeout(() => this.connect(), 5000);
        };
    }

    subscribe(widgetId: string, callback: Function) {
        if (!this.subscribers.has(widgetId)) {
            this.subscribers.set(widgetId, []);
        }
        this.subscribers.get(widgetId)!.push(callback);
    }

    private notifySubscribers(widgetId: string, data: any) {
        const callbacks = this.subscribers.get(widgetId) || [];
        callbacks.forEach(cb => cb(data));
    }
}
```

## Reporting Engine

### Report Templates

```python
from enum import Enum
from typing import List, Dict, Any
from datetime import datetime, date
import asyncio
from jinja2 import Template

class ReportType(Enum):
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_PERFORMANCE = "weekly_performance"
    MONTHLY_EXECUTIVE = "monthly_executive"
    CUSTOM = "custom"

class ReportGenerator:
    def __init__(self, db, storage, email_service):
        self.db = db
        self.storage = storage
        self.email_service = email_service
        self.templates = self._load_templates()

    async def generate_report(
        self,
        report_type: ReportType,
        date_from: date,
        date_to: date,
        filters: Dict[str, Any] = None
    ) -> str:
        """Generate a report based on template"""

        # Collect data based on report type
        data = await self._collect_report_data(report_type, date_from, date_to, filters)

        # Apply template
        template = self.templates[report_type]
        html_content = template.render(
            data=data,
            date_from=date_from,
            date_to=date_to,
            generated_at=datetime.now()
        )

        # Convert to PDF
        pdf_path = await self._generate_pdf(html_content, report_type, date_from)

        # Store report
        report_id = await self._store_report(
            report_type, date_from, date_to, pdf_path
        )

        return report_id

    async def _collect_report_data(
        self,
        report_type: ReportType,
        date_from: date,
        date_to: date,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect all data needed for the report"""

        data = {}

        if report_type == ReportType.DAILY_SUMMARY:
            data['device_stats'] = await self._get_device_summary(date_from)
            data['content_stats'] = await self._get_content_summary(date_from)
            data['alerts'] = await self._get_alerts(date_from)
            data['top_content'] = await self._get_top_content(date_from, limit=10)

        elif report_type == ReportType.WEEKLY_PERFORMANCE:
            data['device_uptime'] = await self._get_device_uptime_report(date_from, date_to)
            data['content_performance'] = await self._get_content_performance(date_from, date_to)
            data['network_stats'] = await self._get_network_stats(date_from, date_to)
            data['error_analysis'] = await self._get_error_analysis(date_from, date_to)

        elif report_type == ReportType.MONTHLY_EXECUTIVE:
            data['kpi_metrics'] = await self._get_kpi_metrics(date_from, date_to)
            data['trend_analysis'] = await self._get_trend_analysis(date_from, date_to)
            data['roi_calculation'] = await self._get_roi_metrics(date_from, date_to)
            data['recommendations'] = await self._generate_recommendations(data)

        return data

    async def _get_device_summary(self, date: date) -> Dict:
        """Get device summary for a specific date"""
        query = """
            SELECT
                COUNT(DISTINCT device_id) as total_active,
                AVG(uptime_seconds) / 86400 * 100 as avg_uptime_pct,
                SUM(error_count) as total_errors,
                AVG(avg_cpu_usage) as avg_cpu,
                AVG(avg_memory_usage) as avg_memory
            FROM device_analytics
            WHERE date = $1
        """
        return await self.db.fetch_one(query, date)

    async def schedule_report(
        self,
        template_id: int,
        cron_expression: str,
        recipients: List[str]
    ):
        """Schedule a recurring report"""
        # Implementation would use APScheduler or similar
        pass
```

### Export Formats

```python
class ReportExporter:
    @staticmethod
    async def export_csv(data: List[Dict], filename: str) -> str:
        """Export data to CSV"""
        import csv
        import io

        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        return await storage.save(filename, output.getvalue())

    @staticmethod
    async def export_excel(data: Dict[str, List[Dict]], filename: str) -> str:
        """Export data to Excel with multiple sheets"""
        import pandas as pd
        import io

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, sheet_data in data.items():
                df = pd.DataFrame(sheet_data)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Add formatting
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#D7E4BD',
                    'border': 1
                })
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

        return await storage.save(filename, output.getvalue())

    @staticmethod
    async def export_pdf(html_content: str, filename: str) -> str:
        """Convert HTML report to PDF"""
        from weasyprint import HTML
        import io

        pdf_bytes = HTML(string=html_content).write_pdf()
        return await storage.save(filename, pdf_bytes)
```

## Alerting System

### Alert Rules Engine

```python
class AlertRule:
    def __init__(self, rule_config: Dict):
        self.id = rule_config['id']
        self.name = rule_config['name']
        self.rule_type = rule_config['rule_type']
        self.condition = rule_config['condition']
        self.actions = rule_config['actions']
        self.severity = rule_config['severity']
        self.cooldown_minutes = rule_config['cooldown_minutes']
        self.last_triggered = None

    async def evaluate(self, data: Dict) -> bool:
        """Evaluate if alert condition is met"""
        if self.rule_type == 'threshold':
            return self._evaluate_threshold(data)
        elif self.rule_type == 'anomaly':
            return await self._evaluate_anomaly(data)
        elif self.rule_type == 'pattern':
            return await self._evaluate_pattern(data)
        return False

    def _evaluate_threshold(self, data: Dict) -> bool:
        """Evaluate threshold-based rules"""
        metric = data.get(self.condition['metric'])
        operator = self.condition['operator']
        threshold = self.condition['threshold']

        if operator == 'gt':
            return metric > threshold
        elif operator == 'lt':
            return metric < threshold
        elif operator == 'eq':
            return metric == threshold
        elif operator == 'gte':
            return metric >= threshold
        elif operator == 'lte':
            return metric <= threshold
        return False

    async def _evaluate_anomaly(self, data: Dict) -> bool:
        """Evaluate anomaly detection rules using statistical methods"""
        # Implementation would use isolation forest, LSTM, or similar
        pass

    async def trigger_actions(self, alert_data: Dict):
        """Execute actions when alert is triggered"""
        for action in self.actions:
            if action['type'] == 'email':
                await self._send_email_alert(action, alert_data)
            elif action['type'] == 'webhook':
                await self._send_webhook(action, alert_data)
            elif action['type'] == 'sms':
                await self._send_sms(action, alert_data)
            elif action['type'] == 'dashboard':
                await self._update_dashboard(action, alert_data)

class AlertManager:
    def __init__(self, db, redis, notification_service):
        self.db = db
        self.redis = redis
        self.notification_service = notification_service
        self.rules = []
        self.load_rules()

    async def load_rules(self):
        """Load alert rules from database"""
        query = "SELECT * FROM alert_rules WHERE is_active = true"
        rules_data = await self.db.fetch_all(query)
        self.rules = [AlertRule(rule) for rule in rules_data]

    async def check_alerts(self):
        """Main alert checking loop"""
        while True:
            try:
                # Get current metrics
                metrics = await self._collect_current_metrics()

                # Evaluate each rule
                for rule in self.rules:
                    if await rule.evaluate(metrics):
                        if self._should_trigger(rule):
                            await self._trigger_alert(rule, metrics)

                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Alert checking error: {e}")
                await asyncio.sleep(60)

    def _should_trigger(self, rule: AlertRule) -> bool:
        """Check if alert should be triggered (respecting cooldown)"""
        if not rule.last_triggered:
            return True

        time_since_last = datetime.now() - rule.last_triggered
        return time_since_last.total_seconds() > rule.cooldown_minutes * 60

    async def _trigger_alert(self, rule: AlertRule, metrics: Dict):
        """Trigger an alert and record it"""
        alert_data = {
            'rule_id': rule.id,
            'rule_name': rule.name,
            'severity': rule.severity,
            'metrics': metrics,
            'triggered_at': datetime.now()
        }

        # Record in database
        query = """
            INSERT INTO alert_history
            (rule_id, triggered_at, alert_data, notification_sent)
            VALUES ($1, $2, $3, $4)
        """
        await self.db.execute(
            query,
            rule.id,
            alert_data['triggered_at'],
            json.dumps(metrics),
            True
        )

        # Execute actions
        await rule.trigger_actions(alert_data)

        # Update last triggered time
        rule.last_triggered = datetime.now()
```

### Alert Examples

```python
# Predefined alert rules
DEFAULT_ALERT_RULES = [
    {
        'name': 'Device Offline',
        'rule_type': 'threshold',
        'entity_type': 'device',
        'condition': {
            'metric': 'minutes_since_heartbeat',
            'operator': 'gt',
            'threshold': 5
        },
        'actions': [{
            'type': 'email',
            'recipients': ['ops@company.com'],
            'template': 'device_offline'
        }],
        'severity': 'warning',
        'cooldown_minutes': 15
    },
    {
        'name': 'High Error Rate',
        'rule_type': 'threshold',
        'entity_type': 'system',
        'condition': {
            'metric': 'error_rate_per_minute',
            'operator': 'gt',
            'threshold': 10
        },
        'actions': [{
            'type': 'webhook',
            'url': 'https://hooks.slack.com/services/xxx',
            'method': 'POST'
        }],
        'severity': 'critical',
        'cooldown_minutes': 30
    },
    {
        'name': 'Storage Almost Full',
        'rule_type': 'threshold',
        'entity_type': 'system',
        'condition': {
            'metric': 'storage_usage_percent',
            'operator': 'gt',
            'threshold': 90
        },
        'actions': [{
            'type': 'email',
            'recipients': ['admin@company.com'],
            'template': 'storage_warning'
        }],
        'severity': 'warning',
        'cooldown_minutes': 360
    },
    {
        'name': 'Content Playback Failure',
        'rule_type': 'threshold',
        'entity_type': 'content',
        'condition': {
            'metric': 'failure_rate',
            'operator': 'gt',
            'threshold': 0.1  # 10% failure rate
        },
        'actions': [{
            'type': 'dashboard',
            'highlight': true
        }, {
            'type': 'email',
            'recipients': ['content@company.com'],
            'template': 'content_failure'
        }],
        'severity': 'warning',
        'cooldown_minutes': 60
    }
]
```

## API Specifications

### Analytics Endpoints

```python
from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import datetime, date, timedelta
from typing import Optional, List

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Content Analytics
@router.get("/content/{content_id}")
async def get_content_analytics(
    content_id: int,
    date_from: Optional[date] = Query(default=date.today() - timedelta(days=30)),
    date_to: Optional[date] = Query(default=date.today()),
    granularity: str = Query(default="daily", regex="^(hourly|daily|weekly|monthly)$")
):
    """
    Get analytics for specific content

    Returns:
    - Total plays
    - Unique viewers
    - Average completion rate
    - Geographic distribution
    - Time-series data based on granularity
    """
    # Implementation here
    return {
        "content_id": content_id,
        "date_range": {
            "from": date_from,
            "to": date_to
        },
        "metrics": {
            "total_plays": 1234,
            "unique_viewers": 456,
            "total_watch_time_hours": 789.5,
            "avg_completion_rate": 0.85,
            "skip_rate": 0.05
        },
        "time_series": [],
        "geographic_distribution": [],
        "device_breakdown": {
            "webos_tv": 300,
            "browser": 100,
            "monitor": 56
        }
    }

# Device Analytics
@router.get("/devices/{device_id}")
async def get_device_analytics(
    device_id: int,
    date_from: Optional[date] = Query(default=date.today() - timedelta(days=7)),
    date_to: Optional[date] = Query(default=date.today())
):
    """
    Get analytics for specific device

    Returns:
    - Uptime percentage
    - Content played
    - Error logs
    - Performance metrics
    """
    return {
        "device_id": device_id,
        "date_range": {
            "from": date_from,
            "to": date_to
        },
        "metrics": {
            "uptime_percentage": 99.5,
            "total_content_played": 234,
            "unique_content_played": 45,
            "error_count": 3,
            "avg_cpu_usage": 45.2,
            "avg_memory_usage": 62.1,
            "total_bandwidth_gb": 12.5
        },
        "uptime_chart": [],
        "performance_timeline": [],
        "error_logs": []
    }

# Dashboard Data
@router.get("/dashboard")
async def get_dashboard_data():
    """
    Get real-time dashboard data

    Returns aggregated metrics for dashboard display
    """
    return {
        "system_stats": {
            "total_devices": 500,
            "online_devices": 485,
            "total_content": 1234,
            "active_playlists": 45
        },
        "real_time_metrics": {
            "current_viewers": 423,
            "content_playing_now": 38,
            "bandwidth_usage_mbps": 234.5,
            "api_response_ms": 45
        },
        "alerts": {
            "critical": 0,
            "warning": 2,
            "info": 5
        },
        "trends": {
            "device_growth": "+5.2%",
            "content_views": "+12.3%",
            "uptime": "99.9%"
        },
        "top_content": [],
        "recent_activities": []
    }

# Generate Report
@router.post("/reports/generate")
async def generate_report(
    report_type: str,
    date_from: date,
    date_to: date,
    format: str = Query(default="pdf", regex="^(pdf|excel|csv)$"),
    filters: Optional[dict] = None,
    email_to: Optional[List[str]] = None
):
    """
    Generate an analytics report

    Args:
    - report_type: Type of report (daily_summary, weekly_performance, etc.)
    - date_from: Start date
    - date_to: End date
    - format: Output format
    - filters: Optional filters
    - email_to: Optional email addresses for delivery

    Returns report ID for download
    """
    # Queue report generation
    report_id = await queue_report_generation(
        report_type, date_from, date_to, format, filters, email_to
    )

    return {
        "report_id": report_id,
        "status": "generating",
        "estimated_time_seconds": 30,
        "download_url": f"/api/analytics/reports/{report_id}/download"
    }

# Download Report
@router.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """
    Download a generated report
    """
    # Implementation would fetch from storage
    pass

# Real-time metrics WebSocket
@router.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metrics streaming
    """
    await websocket.accept()
    try:
        while True:
            # Send metrics every second
            metrics = await get_real_time_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
```

## Frontend Implementation

### Component Structure

```typescript
// src/components/analytics/
// ├── Dashboard/
// │   ├── DashboardContainer.tsx
// │   ├── MetricCard.tsx
// │   ├── ChartWidget.tsx
// │   ├── DeviceMap.tsx
// │   └── AlertsPanel.tsx
// ├── Reports/
// │   ├── ReportGenerator.tsx
// │   ├── ReportList.tsx
// │   ├── ReportScheduler.tsx
// │   └── ReportViewer.tsx
// ├── ContentAnalytics/
// │   ├── ContentPerformance.tsx
// │   ├── ContentComparison.tsx
// │   └── ContentTrends.tsx
// ├── DeviceAnalytics/
// │   ├── DeviceUptime.tsx
// │   ├── DevicePerformance.tsx
// │   └── DeviceAlerts.tsx
// └── shared/
//     ├── ChartComponents.tsx
//     ├── DateRangePicker.tsx
//     └── ExportButtons.tsx

// Example: Real-time dashboard component
import React, { useEffect, useState } from 'react';
import { Line, Bar, Pie } from 'recharts';
import { useWebSocket } from '../hooks/useWebSocket';

interface DashboardProps {
    refreshInterval?: number;
}

export const AnalyticsDashboard: React.FC<DashboardProps> = ({
    refreshInterval = 30000
}) => {
    const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
    const { data: realtimeData } = useWebSocket('/ws/analytics/metrics');

    useEffect(() => {
        fetchDashboardData();
        const interval = setInterval(fetchDashboardData, refreshInterval);
        return () => clearInterval(interval);
    }, [refreshInterval]);

    useEffect(() => {
        if (realtimeData) {
            updateMetrics(realtimeData);
        }
    }, [realtimeData]);

    const fetchDashboardData = async () => {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();
        setMetrics(data);
    };

    const updateMetrics = (newData: any) => {
        setMetrics(prev => ({
            ...prev,
            real_time_metrics: newData
        }));
    };

    if (!metrics) return <LoadingSpinner />;

    return (
        <div className="analytics-dashboard">
            {/* Metric Cards Row */}
            <div className="grid grid-cols-4 gap-4 mb-6">
                <MetricCard
                    title="Online Devices"
                    value={metrics.system_stats.online_devices}
                    total={metrics.system_stats.total_devices}
                    trend={metrics.trends.device_growth}
                    color="green"
                />
                <MetricCard
                    title="Content Views Today"
                    value={metrics.real_time_metrics.current_viewers}
                    trend={metrics.trends.content_views}
                    color="blue"
                />
                <MetricCard
                    title="System Uptime"
                    value={metrics.trends.uptime}
                    format="percentage"
                    color="purple"
                />
                <MetricCard
                    title="Active Alerts"
                    value={metrics.alerts.warning + metrics.alerts.critical}
                    severity={metrics.alerts.critical > 0 ? 'critical' : 'warning'}
                    color="orange"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-2 gap-6 mb-6">
                <ChartWidget
                    title="Content Plays (24h)"
                    type="area"
                    data={metrics.content_plays_timeline}
                />
                <ChartWidget
                    title="Device Status Distribution"
                    type="pie"
                    data={metrics.device_status_breakdown}
                />
            </div>

            {/* Device Map and Activity Feed */}
            <div className="grid grid-cols-3 gap-6">
                <div className="col-span-2">
                    <DeviceMap devices={metrics.device_locations} />
                </div>
                <div className="col-span-1">
                    <ActivityFeed activities={metrics.recent_activities} />
                </div>
            </div>
        </div>
    );
};
```

### Chart Library Integration

```typescript
// Using Recharts for data visualization
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar,
    PieChart, Pie, Cell, ResponsiveContainer,
    CartesianGrid, XAxis, YAxis, Tooltip, Legend
} from 'recharts';

interface ChartWidgetProps {
    title: string;
    type: 'line' | 'area' | 'bar' | 'pie';
    data: any[];
    height?: number;
}

export const ChartWidget: React.FC<ChartWidgetProps> = ({
    title,
    type,
    data,
    height = 300
}) => {
    const renderChart = () => {
        switch (type) {
            case 'line':
                return (
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#8884d8"
                            activeDot={{ r: 8 }}
                        />
                    </LineChart>
                );

            case 'area':
                return (
                    <AreaChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <Tooltip />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke="#8884d8"
                            fill="#8884d8"
                        />
                    </AreaChart>
                );

            case 'pie':
                const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];
                return (
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={renderCustomizedLabel}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`}
                                      fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                    </PieChart>
                );

            default:
                return null;
        }
    };

    return (
        <div className="chart-widget">
            <h3 className="text-lg font-semibold mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={height}>
                {renderChart()}
            </ResponsiveContainer>
        </div>
    );
};
```

## Performance Benchmarks

### Expected Load Calculations

```yaml
Load Metrics:
  Devices: 500 active devices
  Heartbeat Interval: 30 seconds

  Events per Hour:
    - Heartbeats: 500 × 120 = 60,000 events
    - Playback Events: ~500 × 10 = 5,000 events (assuming 10 content changes/hour)
    - System Events: ~1,000 events
    Total: ~66,000 events/hour

  Storage Growth:
    - Raw Events: ~100 bytes/event × 66,000 × 24 = ~160 MB/day
    - Aggregated Data: ~20 MB/day
    - Total: ~180 MB/day = ~5.4 GB/month

  Query Performance Targets:
    - Dashboard Load: < 500ms
    - Real-time Metrics: < 100ms
    - Report Generation: < 30 seconds
    - Chart Rendering: < 200ms
```

### Optimization Strategies

```python
# 1. Caching Strategy
class CacheManager:
    def __init__(self, redis):
        self.redis = redis
        self.ttl = {
            'dashboard': 30,  # 30 seconds
            'content_stats': 300,  # 5 minutes
            'device_stats': 60,  # 1 minute
            'reports': 3600  # 1 hour
        }

    async def get_or_compute(self, key: str, compute_fn, ttl_override=None):
        """Get from cache or compute if missing"""
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        result = await compute_fn()
        ttl = ttl_override or self.ttl.get(key.split(':')[0], 60)
        await self.redis.setex(key, ttl, json.dumps(result))
        return result

# 2. Query Optimization
class OptimizedQueries:
    @staticmethod
    def create_indexes():
        """Create optimized indexes for analytics queries"""
        return [
            "CREATE INDEX CONCURRENTLY idx_events_device_time ON analytics_events(device_id, timestamp DESC)",
            "CREATE INDEX CONCURRENTLY idx_events_content_time ON analytics_events((metadata->>'content_id')::int, timestamp DESC)",
            "CREATE INDEX CONCURRENTLY idx_events_type_time ON analytics_events(event_type, timestamp DESC)",
            "CREATE INDEX CONCURRENTLY idx_content_analytics_date ON content_analytics(date DESC)",
            "CREATE INDEX CONCURRENTLY idx_device_analytics_date ON device_analytics(date DESC)",
        ]

    @staticmethod
    async def parallel_query_execution(queries: List[str]):
        """Execute multiple queries in parallel"""
        tasks = [db.fetch_all(query) for query in queries]
        results = await asyncio.gather(*tasks)
        return results

# 3. Data Aggregation Pipeline
class AggregationPipeline:
    def __init__(self):
        self.batch_size = 1000
        self.workers = 4

    async def process_events(self):
        """Process events in batches with multiple workers"""
        queue = asyncio.Queue()

        # Start workers
        workers = [
            asyncio.create_task(self.worker(queue))
            for _ in range(self.workers)
        ]

        # Feed queue
        async for batch in self.get_event_batches():
            await queue.put(batch)

        # Signal completion
        for _ in range(self.workers):
            await queue.put(None)

        # Wait for workers
        await asyncio.gather(*workers)

    async def worker(self, queue):
        """Worker to process event batches"""
        while True:
            batch = await queue.get()
            if batch is None:
                break
            await self.process_batch(batch)
```

## Implementation Roadmap

### Phase 4.4.1: Data Collection Infrastructure (Week 1-2)

```yaml
Tasks:
  - Set up event streaming with Redis Streams
  - Implement WebSocket endpoints for device events
  - Create event validation and enrichment pipeline
  - Set up database partitioning
  - Implement basic event storage

Deliverables:
  - Event collection API endpoints
  - Database schema with partitions
  - Basic event processing workers
```

### Phase 4.4.2: Basic Analytics & Aggregation (Week 3-4)

```yaml
Tasks:
  - Implement aggregation workers
  - Create materialized views
  - Build content analytics endpoints
  - Build device analytics endpoints
  - Implement caching layer

Deliverables:
  - Analytics API endpoints
  - Pre-aggregated data tables
  - Cache management system
```

### Phase 4.4.3: Real-time Dashboard (Week 5)

```yaml
Tasks:
  - Create dashboard React components
  - Implement WebSocket for real-time updates
  - Integrate chart libraries
  - Build dashboard widgets
  - Implement auto-refresh mechanism

Deliverables:
  - Live analytics dashboard
  - Real-time metric updates
  - Interactive charts and visualizations
```

### Phase 4.4.4: Reporting Engine (Week 6)

```yaml
Tasks:
  - Create report templates
  - Implement report generation service
  - Build report scheduler
  - Add export functionality (PDF, Excel, CSV)
  - Implement email delivery

Deliverables:
  - Report generation API
  - Scheduled reports
  - Multiple export formats
```

### Phase 4.4.5: Alerting System (Week 7-8)

```yaml
Tasks:
  - Build alert rule engine
  - Implement alert evaluation loop
  - Create notification channels
  - Build alert management UI
  - Add alert history and acknowledgment

Deliverables:
  - Alert configuration API
  - Real-time alert processing
  - Multi-channel notifications
  - Alert management dashboard
```

## Code Examples

### Event Tracking Implementation

```python
# viewer/js/analytics.js
class AnalyticsTracker {
    constructor(deviceId) {
        this.deviceId = deviceId;
        this.ws = null;
        this.eventQueue = [];
        this.reconnectAttempts = 0;
        this.connectWebSocket();
    }

    connectWebSocket() {
        this.ws = new WebSocket(`ws://192.168.5.12:8001/ws/analytics/${this.deviceId}`);

        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            this.flushQueue();
        };

        this.ws.onclose = () => {
            setTimeout(() => {
                this.reconnectAttempts++;
                this.connectWebSocket();
            }, Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000));
        };
    }

    track(eventType, metadata = {}) {
        const event = {
            device_id: this.deviceId,
            event_type: eventType,
            timestamp: new Date().toISOString(),
            metadata: {
                ...metadata,
                user_agent: navigator.userAgent,
                screen_resolution: `${screen.width}x${screen.height}`,
                viewport: `${window.innerWidth}x${window.innerHeight}`
            }
        };

        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(event));
        } else {
            this.eventQueue.push(event);
        }
    }

    trackPlayback(contentId, action, additionalData = {}) {
        this.track(`playback_${action}`, {
            content_id: contentId,
            ...additionalData
        });
    }

    trackHeartbeat() {
        this.track('heartbeat', {
            memory_usage: performance.memory ?
                (performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize) * 100 : null,
            page_visible: !document.hidden,
            connection_type: navigator.connection ? navigator.connection.effectiveType : null
        });
    }

    flushQueue() {
        while (this.eventQueue.length > 0 && this.ws.readyState === WebSocket.OPEN) {
            const event = this.eventQueue.shift();
            this.ws.send(JSON.stringify(event));
        }
    }
}

// Initialize tracker
const analytics = new AnalyticsTracker(DEVICE_ID);

// Track heartbeat every 30 seconds
setInterval(() => analytics.trackHeartbeat(), 30000);

// Track playback events
videoPlayer.on('play', () => analytics.trackPlayback(contentId, 'start'));
videoPlayer.on('pause', () => analytics.trackPlayback(contentId, 'pause'));
videoPlayer.on('ended', () => analytics.trackPlayback(contentId, 'complete', {
    completion_rate: 1.0,
    duration_watched: videoPlayer.duration
}));
videoPlayer.on('error', (e) => analytics.trackPlayback(contentId, 'error', {
    error_code: e.code,
    error_message: e.message
}));
```

### Aggregation Query Example

```sql
-- Hourly content performance aggregation
WITH hourly_stats AS (
    SELECT
        DATE_TRUNC('hour', timestamp) as hour,
        (metadata->>'content_id')::int as content_id,
        COUNT(*) FILTER (WHERE event_type = 'playback_start') as plays,
        COUNT(DISTINCT device_id) as unique_devices,
        AVG((metadata->>'completion_rate')::float) as avg_completion,
        SUM((metadata->>'duration_watched')::int) as total_watch_seconds,
        COUNT(*) FILTER (WHERE event_type = 'playback_error') as errors
    FROM analytics_events
    WHERE timestamp >= NOW() - INTERVAL '24 hours'
        AND event_category = 'playback'
    GROUP BY hour, content_id
),
ranked_content AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY hour ORDER BY plays DESC) as hourly_rank
    FROM hourly_stats
)
SELECT
    c.name as content_name,
    rc.hour,
    rc.plays,
    rc.unique_devices,
    ROUND(rc.avg_completion * 100, 2) as completion_percentage,
    rc.total_watch_seconds / 60 as total_watch_minutes,
    rc.errors,
    rc.hourly_rank
FROM ranked_content rc
JOIN content c ON c.id = rc.content_id
WHERE rc.hourly_rank <= 10
ORDER BY rc.hour DESC, rc.hourly_rank;
```

### Chart Component Example

```typescript
// Advanced chart with drill-down capability
import React, { useState, useMemo } from 'react';
import {
    ComposedChart, Bar, Line, Area, XAxis, YAxis,
    CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    Cell, PieChart, Pie, Sector
} from 'recharts';

interface ContentPerformanceChartProps {
    data: ContentAnalytics[];
    onDrillDown?: (contentId: number) => void;
}

export const ContentPerformanceChart: React.FC<ContentPerformanceChartProps> = ({
    data,
    onDrillDown
}) => {
    const [activeIndex, setActiveIndex] = useState<number | null>(null);

    const chartData = useMemo(() => {
        return data.map(item => ({
            ...item,
            completion_rate: item.avg_completion_rate * 100,
            efficiency: (item.total_plays / item.unique_devices).toFixed(2)
        }));
    }, [data]);

    const handleClick = (data: any, index: number) => {
        setActiveIndex(index);
        if (onDrillDown) {
            onDrillDown(data.content_id);
        }
    };

    const renderActiveShape = (props: any) => {
        const { cx, cy, innerRadius, outerRadius, startAngle, endAngle,
                fill, payload, value } = props;

        return (
            <g>
                <Sector
                    cx={cx}
                    cy={cy}
                    innerRadius={innerRadius}
                    outerRadius={outerRadius + 10}
                    startAngle={startAngle}
                    endAngle={endAngle}
                    fill={fill}
                />
                <text x={cx} y={cy} dy={-10} textAnchor="middle" fill={fill}>
                    {payload.name}
                </text>
                <text x={cx} y={cy} dy={10} textAnchor="middle" fill="#999">
                    {`${value} plays`}
                </text>
                <text x={cx} y={cy} dy={30} textAnchor="middle" fill="#999">
                    {`${payload.completion_rate.toFixed(1)}% completion`}
                </text>
            </g>
        );
    };

    return (
        <div className="content-performance-chart">
            <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Bar
                        yAxisId="left"
                        dataKey="total_plays"
                        fill="#8884d8"
                        onClick={handleClick}
                    >
                        {chartData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={index === activeIndex ? '#ffc658' : '#8884d8'}
                            />
                        ))}
                    </Bar>
                    <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="completion_rate"
                        stroke="#82ca9d"
                        strokeWidth={2}
                    />
                    <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="unique_devices"
                        fill="#ffc658"
                        stroke="#ffc658"
                        fillOpacity={0.3}
                    />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
};
```

## Security & Privacy Considerations

```yaml
Data Protection:
  - Anonymize PII in analytics events
  - Implement data retention policies
  - Encrypt sensitive metrics in transit and at rest
  - Audit trail for all data access

GDPR Compliance:
  - Right to be forgotten implementation
  - Data portability for analytics data
  - Consent management for tracking
  - Privacy-preserving aggregations

Access Control:
  - Role-based access to analytics
  - Department-level data isolation
  - API rate limiting
  - Query result size limits
```

## Monitoring & Maintenance

```yaml
System Monitoring:
  - Analytics pipeline health checks
  - Query performance monitoring
  - Storage growth tracking
  - Alert delivery success rates

Maintenance Tasks:
  - Daily: Check aggregation jobs
  - Weekly: Vacuum analyze tables
  - Monthly: Create new partitions, review indexes
  - Quarterly: Archive old data, review retention
```

## Success Metrics

```yaml
KPIs for Analytics System:
  - Dashboard load time: < 500ms (target: 95th percentile)
  - Report generation time: < 30s for standard reports
  - Data freshness: < 1 minute for real-time metrics
  - Alert delivery time: < 1 minute from trigger
  - System uptime: > 99.9%
  - Query performance: < 100ms for cached, < 1s for computed
```

---

This comprehensive design provides a robust, scalable analytics and reporting system that will grow with your Digital Signage platform from 500 to 1000+ devices while maintaining performance and providing valuable business insights.