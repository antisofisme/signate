# Firebird Bridge Agent

Local service yang berjalan di server hotel untuk sync data Firebird PMS ke cloud backend.

## Arsitektur

```
┌─────────────────────────────────────────────────┐
│           CLOUD (Backend Python)                │
│   API Endpoint: /api/v1/pms/sync/*              │
└─────────────────────────────────────────────────┘
                    ↑
                    │ HTTPS POST
                    │
┌───────────────────┴─────────────────────────────┐
│         LOCAL HOTEL NETWORK                     │
│                                                 │
│  ┌─────────────────────────────────────┐       │
│  │   Firebird Bridge Agent (Python)    │       │
│  │   - Query Firebird every 5 min      │       │
│  │   - Extract guest data              │       │
│  │   - POST to cloud API               │       │
│  └─────────────────────────────────────┘       │
│                    ↓                             │
│  ┌─────────────────────────────────────┐       │
│  │   Firebird Database (PMS System)    │       │
│  │   - GUESTS, ROOMS tables            │       │
│  └─────────────────────────────────────┘       │
└─────────────────────────────────────────────────┘
```

## Fitur

- **Web UI**: Interface web untuk konfigurasi dan monitoring (port 5000)
- **Auto Sync**: Sync otomatis setiap N menit (default: 5 menit)
- **Guest Check-ins**: Kirim data tamu yang baru check-in
- **Room Status**: Kirim status ketersediaan kamar
- **Connection Testing**: Test koneksi Firebird dan Cloud API
- **Table Explorer**: List semua tabel di database Firebird
- **Retry Logic**: Auto retry jika gagal connect ke cloud
- **Logging**: Log lengkap untuk troubleshooting
- **Systemd Service**: Jalan otomatis saat server restart

## Instalasi

### 1. Requirements

- Python 3.8+
- Firebird database (PMS system)
- Network connectivity ke cloud backend

### 2. Install

```bash
cd firebird-bridge-agent
chmod +x install.sh
sudo ./install.sh
```

### 3. Web UI (Recommended)

Cara termudah untuk setup adalah menggunakan Web UI:

```bash
# Install dependencies
cd /opt/firebird-bridge-agent
pip3 install -r requirements.txt

# Start Web UI
python3 web_ui.py
```

Akses di browser: **http://localhost:5000**

**Features Web UI**:
- ✅ Configure Cloud API settings (URL, Organization ID, API Key)
- ✅ Configure Firebird Database (Host, Port, Path, User, Password)
- ✅ Test connections before saving
- ✅ List all tables in Firebird database
- ✅ Trigger manual sync
- ✅ Monitor sync status in real-time

**Database Credentials Default**:
- User: `SYSDBA`
- Password: `masterkey`

### 3. Manual Configuration (Alternative)

Atau edit file `/etc/firebird-bridge/config.yaml` secara manual:

```yaml
cloud:
  api_url: "http://192.168.5.12:8001/api/v1"
  organization_id: 1  # ID organisasi di cloud
  api_key: "your-api-key"  # Dapatkan dari web admin

firebird:
  host: "localhost"
  port: 3050
  database_path: "/path/to/your/hotel.fdb"
  username: "SYSDBA"
  password: "masterkey"
```

**PENTING**: Sesuaikan nama tabel dan kolom di `firebird_reader.py` dengan schema Firebird PMS Anda!

### 4. Start Service

```bash
# Start agent
sudo systemctl start firebird-bridge

# Check status
sudo systemctl status firebird-bridge

# View logs
sudo journalctl -u firebird-bridge -f
```

## Customization

### Sesuaikan Query Firebird

Edit file `/opt/firebird-bridge/firebird_reader.py`:

```python
# Method: get_recent_checkins()
query = """
    SELECT
        YOUR_GUEST_ID_COLUMN,
        YOUR_GUEST_NAME_COLUMN,
        YOUR_ROOM_NO_COLUMN,
        YOUR_CHECKIN_DATE_COLUMN,
        YOUR_CHECKOUT_DATE_COLUMN
    FROM YOUR_GUESTS_TABLE
    WHERE YOUR_CHECKIN_DATE_COLUMN >= ?
    AND YOUR_STATUS_COLUMN = 'CHECKED_IN'
"""
```

### Ubah Interval Sync

Edit `/etc/firebird-bridge/config.yaml`:

```yaml
sync:
  interval_minutes: 10  # Ubah ke 10 menit
```

Restart service:

```bash
sudo systemctl restart firebird-bridge
```

## Troubleshooting

### Error: Cannot connect to Firebird

```bash
# Check Firebird service
sudo systemctl status firebird

# Check database file exists
ls -la /path/to/hotel.fdb

# Test connection manually
python3
>>> import fdb
>>> conn = fdb.connect(host='localhost', database='/path/to/hotel.fdb', user='SYSDBA', password='masterkey')
>>> conn.close()
```

### Error: Cannot connect to cloud backend

```bash
# Test network connectivity
curl http://192.168.5.12:8001/api/v1/health

# Check API key valid
curl -H "X-API-Key: your-key" http://192.168.5.12:8001/api/v1/pms/sync/guests
```

### View Agent Logs

```bash
# Live log
sudo journalctl -u firebird-bridge -f

# Last 100 lines
sudo journalctl -u firebird-bridge -n 100

# Log file
sudo tail -f /var/log/firebird-bridge/agent.log
```

## Manual Testing

Test agent tanpa install sebagai service:

```bash
cd /mnt/g/khoirul/signate/firebird-bridge-agent
python3 agent.py
```

Press `Ctrl+C` untuk stop.

## Uninstall

```bash
# Stop service
sudo systemctl stop firebird-bridge
sudo systemctl disable firebird-bridge

# Remove files
sudo rm -rf /opt/firebird-bridge
sudo rm -rf /var/log/firebird-bridge
sudo rm -rf /etc/firebird-bridge
sudo rm /etc/systemd/system/firebird-bridge.service

# Reload systemd
sudo systemctl daemon-reload
```

## Security Notes

- Store API key securely in config file
- Use HTTPS in production (set `verify_ssl: true`)
- Restrict file permissions: `chmod 600 /etc/firebird-bridge/config.yaml`
- Consider VPN tunnel untuk network security
- Rotate API keys regularly

## Support

Untuk pertanyaan dan issue, hubungi tim development.
