# Analytics Dashboard - Quick Start Guide

## 🚀 Getting Started

### Access the Dashboard

1. **Navigate to Analytics**:
   - Click "Analytics" in the sidebar navigation
   - Or visit: `http://localhost:3000/analytics`

2. **Dashboard Loads**:
   - Default date range: Last 30 days
   - Auto-refresh: Enabled (30 seconds)
   - All metrics displayed

---

## 📊 Dashboard Components

### 1. Overview Metrics (Top Row)

Four key performance indicators:

| Metric | Description | Color |
|--------|-------------|-------|
| **Total Views** | All content views in period | Blue |
| **Unique Viewers** | Distinct device views | Purple |
| **Avg Duration** | Average viewing time | Green |
| **Uptime** | System availability % | Green |

### 2. Detailed Widgets (Middle Row)

#### Active Devices Card
- **Online/Offline/Error/Pending** breakdown
- Progress bar showing online percentage
- Color-coded status indicators:
  - 🟢 Green = Online
  - ⚪ Gray = Offline
  - 🔴 Red = Error
  - 🟡 Yellow = Pending

#### Top Content Card
- **Top 10 performing content** (ranked #1-10)
- Shows: Title, Type, View count
- Click to see full title
- Real-time updates

#### System Health Card
- **CPU, Memory, Disk** usage bars
- **API response time** in milliseconds
- **Health status**: Healthy, Warning, Critical
- Color-coded alerts:
  - < 50% = Green (Healthy)
  - 50-80% = Yellow (Warning)
  - > 80% = Red (Critical)

### 3. Charts (Grid Layout)

#### Views Over Time (Area Chart)
- **Blue area**: Total views
- **Green area**: Unique viewers
- X-axis: Date/time
- Y-axis: View count
- Hover for exact values

#### Top Performing Content (Bar Chart)
- **Blue bars**: Total views
- **Green bars**: Unique viewers
- X-axis: Content titles (top 10)
- Y-axis: View count
- Angled labels for readability

#### Device Status Distribution (Pie Chart)
- **Segments**: Online, Offline, Error, Pending
- **Center**: Total device count
- **Percentages**: Shown on each segment
- Legend below chart

#### Error Rate Trends (Line Chart)
- **Red line**: Error count
- **Blue line**: Total requests
- X-axis: Time
- Y-axis: Count
- Identifies problem periods

### 4. Viewing Patterns (Full Width)

**Hourly Heatmap (Bar Chart)**:
- **Purple bars**: Views per hour
- X-axis: Hour (00:00 - 23:00)
- Y-axis: View count
- Identifies peak usage times

---

## 🎛️ Controls & Actions

### Date Range Selection

**Presets** (quick selection):
- **Last 24 Hours** - Today's data
- **Last 7 Days** - Past week
- **Last 30 Days** - Past month (default)
- **Last 90 Days** - Past quarter

**Custom Range**:
1. Click start date picker
2. Select start date
3. Click end date picker
4. Select end date
5. Dashboard updates automatically

### Auto-Refresh

**Enable/Disable**:
- ✅ Checked: Refreshes every 30 seconds
- ❌ Unchecked: Manual refresh only
- Toggle in top-right corner

**Manual Refresh**:
- Click "Refresh" button (🔄 icon)
- Shows spinning icon while loading
- Toast notification on completion

### Export Reports

Three export formats available:

#### 1. PDF Export
```
Click: "Export PDF" button
Format: Professional PDF report
Orientation: Landscape
Includes: All sections with tables and data
Filename: analytics_report_YYYYMMDD_HHMMSS.pdf
```

**PDF Contents**:
- Title and date range
- Overview metrics table
- Device status breakdown
- Top content list
- Formatted headers and footers
- Color-coded sections

#### 2. Excel Export
```
Click: "Export Excel" button
Format: .xlsx spreadsheet
Sheets: Overview, Devices, Top Content
Includes: Formatted tables with colors
Filename: analytics_report_YYYYMMDD_HHMMSS.xlsx
```

**Excel Structure**:
- **Sheet 1 (Overview)**: Key metrics
- **Sheet 2 (Devices)**: Device status
- **Sheet 3 (Top Content)**: Content ranking
- Styled headers and alternating rows

#### 3. CSV Export
```
Click: "Export CSV" button
Format: Plain text CSV
Sections: All data sections
Includes: Headers and data rows
Filename: analytics_report_YYYYMMDD_HHMMSS.csv
```

**CSV Structure**:
- Section headers
- Metric names and values
- Compatible with Excel/Google Sheets

---

## 💡 Usage Scenarios

### Scenario 1: Daily Performance Check

```
1. Navigate to Analytics
2. Select "Last 24 Hours"
3. Review overview metrics
4. Check device status
5. Identify top content
```

**Look for**:
- ✅ High online device percentage (> 90%)
- ✅ Low error count (< 10)
- ✅ Content being viewed
- ⚠️ Offline devices to investigate

### Scenario 2: Weekly Report Generation

```
1. Select "Last 7 Days"
2. Review all charts
3. Note trends and anomalies
4. Click "Export PDF"
5. Download and share report
```

**Include in report**:
- Total views and unique viewers
- Device uptime percentage
- Top performing content
- Error trends
- Peak viewing hours

### Scenario 3: Monthly Business Review

```
1. Select "Last 30 Days"
2. Analyze viewing patterns
3. Identify content performance
4. Export to Excel
5. Create presentation
```

**Key insights**:
- Content ROI (views per content)
- Device utilization rates
- System reliability metrics
- User engagement patterns

### Scenario 4: Troubleshooting Issues

```
1. Select custom date range (incident period)
2. Check error rate chart
3. Review device status
4. Identify affected content
5. Export CSV for detailed analysis
```

**Debug checklist**:
- When did errors spike?
- Which devices went offline?
- What content was affected?
- What were the error patterns?

---

## 🎨 Dashboard Features

### Real-Time Updates

**Auto-Refresh (30s)**:
- Enabled by default
- Polls API every 30 seconds
- Updates all widgets and charts
- Shows "Last updated" timestamp

**Manual Refresh**:
- Click refresh button anytime
- Immediately fetches latest data
- Shows loading state during fetch
- Toast notification on complete

### Loading States

**Initial Load**:
- Skeleton loaders on all cards
- Gray animated placeholders
- Maintains layout structure

**Refresh Load**:
- Spinning refresh icon
- Data remains visible
- Smooth transition to new data

**Export Load**:
- "Generating report..." toast
- Spinning icon in bottom-right
- Download starts automatically

### Empty States

**No Data Available**:
- Icon with message
- Suggests checking date range
- Encourages content creation

**No Devices**:
- "No devices registered" message
- Link to device registration

### Error Handling

**API Errors**:
- Toast notification with message
- Data remains from last successful fetch
- Retry button available

**Network Errors**:
- "Failed to load" message
- Manual refresh to retry
- Graceful degradation

---

## 🎯 Best Practices

### 1. Regular Monitoring

```
✅ Check dashboard daily
✅ Enable auto-refresh during active monitoring
✅ Set up weekly report exports
✅ Monitor device status frequently
```

### 2. Performance Optimization

```
✅ Use shorter date ranges for faster loads
✅ Disable auto-refresh when not actively monitoring
✅ Export reports for historical analysis
✅ Archive old reports regularly
```

### 3. Data Analysis

```
✅ Compare week-over-week trends
✅ Identify peak viewing hours
✅ Track content performance over time
✅ Monitor system health metrics
```

### 4. Report Sharing

```
✅ Export PDF for presentations
✅ Export Excel for deep analysis
✅ Export CSV for data integration
✅ Include context and insights
```

---

## 🔧 Troubleshooting

### Dashboard Not Loading

**Issue**: Analytics page shows loading spinner indefinitely

**Solutions**:
1. Check network connection
2. Verify API server is running (`http://192.168.5.12:8001`)
3. Check browser console for errors
4. Try manual refresh
5. Clear browser cache and reload

### Charts Not Rendering

**Issue**: Chart areas are blank or show errors

**Solutions**:
1. Ensure data is available for date range
2. Try different date range
3. Check browser console
4. Verify Recharts library loaded
5. Reload page

### Export Not Downloading

**Issue**: Click export button but no file downloads

**Solutions**:
1. Check browser download settings
2. Allow pop-ups for the site
3. Verify API endpoint responding
4. Check browser console for errors
5. Try different export format

### Incorrect Data

**Issue**: Metrics seem wrong or outdated

**Solutions**:
1. Check selected date range
2. Click manual refresh
3. Verify system time is correct
4. Check data in database directly
5. Review activity logs

---

## 📱 Mobile Usage

### Responsive Design

**Tablet (768px+)**:
- 2-column grid layout
- Full functionality
- Touch-friendly buttons
- Swipeable charts

**Mobile (< 768px)**:
- Single-column layout
- Stacked widgets
- Larger touch targets
- Simplified navigation

### Mobile Tips

```
✅ Use portrait orientation for better viewing
✅ Pinch to zoom on charts
✅ Swipe through date range presets
✅ Export reports for desktop analysis
```

---

## 🎓 Key Metrics Explained

### Total Views
- **Definition**: Total number of content plays
- **Formula**: Count of all play events
- **Use**: Measure overall engagement

### Unique Viewers
- **Definition**: Distinct devices that viewed content
- **Formula**: Count of unique device IDs
- **Use**: Measure audience reach

### Average Duration
- **Definition**: Mean time content is displayed
- **Formula**: Sum(duration) / Count(views)
- **Use**: Measure engagement depth

### System Uptime
- **Definition**: Percentage of time system was available
- **Formula**: (Uptime seconds / Total seconds) * 100
- **Use**: Measure reliability

### Online Percentage
- **Definition**: Percentage of devices currently online
- **Formula**: (Online devices / Total devices) * 100
- **Use**: Measure device health

---

## 🚀 Advanced Features (Coming Soon)

- [ ] Custom dashboard builder
- [ ] Saved report templates
- [ ] Scheduled email reports
- [ ] Real-time WebSocket updates
- [ ] Predictive analytics
- [ ] Anomaly detection
- [ ] Custom alerts and notifications
- [ ] Multi-user collaboration
- [ ] API access for integrations

---

## 📞 Support

**Issues or Questions?**
- Check backend API docs: `http://192.168.5.12:8001/docs`
- Review error logs in browser console
- Contact system administrator
- Create GitHub issue

---

**Version**: 1.0.0
**Last Updated**: October 28, 2025
**Status**: Production Ready
