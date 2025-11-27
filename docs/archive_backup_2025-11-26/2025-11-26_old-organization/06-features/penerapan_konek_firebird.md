  🔥 Stack & Teknologi yang Digunakan

  Library Utama:
  - fdb==2.0.4 - Pure Python driver untuk Firebird (bukan C-based)
  - FastAPI 0.104.1 - Framework web
  - Uvicorn 0.24.0 - ASGI server
  - Firebird 2.5.9 - Database server

  🏗️ Prinsip Arsitektur

  1️⃣ Connection Pool Pattern

  # Lokasi: api2/core/database.py

  class ConnectionPool:
      def __init__(self, db_name, config, max_connections=5):
          self.pool = Queue(maxsize=max_connections)
          self.active_connections = []

  Prinsip:
  - Menggunakan queue-based pooling dengan maksimal 5 koneksi per database
  - Thread-safe dengan menggunakan lock
  - Health check otomatis setiap 5 menit
  - Auto-replace koneksi yang mati

  2️⃣ Dua Mode Koneksi

  Server Mode (TCP/IP):
  dsn = f"{host}/{port}:{database_path}"
  # Contoh: "localhost/3050:/path/powerfo.gdb"

  Embedded Mode (Direct):
  dsn = database_path
  # Contoh: "/path/powerfo.gdb"

  3️⃣ Singleton Pattern

  class DatabaseConnector:
      _instance = None
      _lock = threading.Lock()

      @classmethod
      def get_connection(cls, db_name='powerfo'):
          # Returns context manager

  Keuntungan: Satu instance untuk semua koneksi, hemat resource

  4️⃣ Context Manager Pattern

  # Usage:
  with DatabaseConnector.get_connection('powerfo') as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM TABLE")
      results = cursor.fetchall()

  📁 Struktur File Penting

  api2/
  ├── core/
  │   ├── database.py                    # Connection pool & manager
  │   ├── database_optimization.py       # Performance monitoring
  │   └── config.py                      # Config loader
  ├── config.json                        # Database configuration
  ├── requirements.txt                   # fdb==2.0.4
  └── FDB_FIREBIRD_CONNECTION_GUIDE.md  # Setup guide

  🎯 Cara Kerja (Flow)

  1. Startup: Load config.json → Validasi → Buat connection pool
  2. Request: Get connection dari pool → Execute query → Return to pool
  3. Health Check: Setiap 5 menit cek SELECT 1 FROM RDB$DATABASE
  4. Monitoring: Track query time, detect slow queries (>1s)
  5. Error Handling: FAIL FAST (tidak ada fallback/mock data)

  💡 Fitur Utama

  ✅ Connection pooling otomatis✅ Health monitoring real-time✅ Performance metrics (24 jam retention)✅
  Multi-database support✅ Thread-safe operations✅ Slow query detection

  📝 Contoh Konfigurasi

  config.json:
  {
    "databases": {
      "powerfo": {
        "path": "/path/to/powerfo.gdb",
        "host": "localhost",
        "port": 3050,
        "user": "SYSDBA",
        "password": "masterkey",
        "charset": "UTF8",
        "connection_mode": "server"
      }
    }
  }
