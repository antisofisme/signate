#!/usr/bin/env python3
"""
Firebird Bridge Agent - Web UI
Simple web interface for configuration and monitoring
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import yaml
import os
import sys
from pathlib import Path
import fdb
import requests
from datetime import datetime
import threading
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebird_reader import FirebirdReader
from cloud_sync import CloudSyncClient

app = Flask(__name__)
app.secret_key = 'firebird-bridge-secret-key-change-in-production'

# Global agent state
agent_state = {
    'running': False,
    'last_sync': None,
    'last_error': None,
    'sync_count': 0,
    'guest_count': 0,
    'room_count': 0
}

CONFIG_FILE = 'config.yaml'


def load_config():
    """Load configuration from YAML file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    return get_default_config()


def save_config(config):
    """Save configuration to YAML file"""
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def get_default_config():
    """Get default configuration"""
    return {
        'cloud': {
            'api_url': 'http://192.168.5.12:8001/api/v1',
            'organization_id': 1,
            'api_key': '',
            'verify_ssl': False
        },
        'firebird': {
            'host': 'localhost',
            'port': 3050,
            'database_path': '/path/to/hotel.fdb',
            'username': 'SYSDBA',
            'password': 'masterkey',
            'charset': 'UTF8'
        },
        'tables': {
            'guest_table': {
                'enabled': False,
                'table_name': '',
                'columns': {
                    'guest_name': '',
                    'room_number': '',
                    'checkin_date': '',
                    'checkout_date': '',
                    'email': '',
                    'phone': '',
                    'country': '',
                    'reservation_no': ''
                },
                'where_clause': ''
            },
            'room_table': {
                'enabled': False,
                'table_name': '',
                'columns': {
                    'room_number': '',
                    'room_type': '',
                    'status': '',
                    'floor': '',
                    'bed_type': '',
                    'max_occupancy': ''
                },
                'where_clause': ''
            }
        },
        'sync': {
            'interval_minutes': 5,
            'batch_size': 100,
            'retry_attempts': 3,
            'retry_delay_seconds': 10
        },
        'logging': {
            'level': 'INFO',
            'file': '/var/log/firebird-bridge/agent.log',
            'max_size_mb': 50,
            'backup_count': 5
        }
    }


# =============================================================================
# ROUTES
# =============================================================================


@app.route('/')
def index():
    """Dashboard page"""
    config = load_config()
    return render_template('index.html', config=config, state=agent_state)


@app.route('/settings')
def settings():
    """Settings page"""
    config = load_config()
    return render_template('settings.html', config=config)


@app.route('/tables')
def tables():
    """Table mapping page"""
    config = load_config()
    return render_template('tables.html', config=config)


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config = load_config()
    # Hide sensitive data
    if 'api_key' in config.get('cloud', {}):
        config['cloud']['api_key'] = '***' + config['cloud']['api_key'][-4:] if config['cloud']['api_key'] else ''
    if 'password' in config.get('firebird', {}):
        config['firebird']['password'] = '***' + config['firebird']['password'][-2:] if config['firebird']['password'] else ''
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        data = request.json
        config = load_config()

        # Update cloud settings
        if 'cloud' in data:
            config['cloud'].update(data['cloud'])

        # Update firebird settings
        if 'firebird' in data:
            config['firebird'].update(data['firebird'])

        # Update sync settings
        if 'sync' in data:
            config['sync'].update(data['sync'])

        save_config(config)
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/test-firebird', methods=['POST'])
def test_firebird():
    """Test Firebird database connection"""
    try:
        data = request.json

        conn = fdb.connect(
            host=data.get('host', 'localhost'),
            port=int(data.get('port', 3050)),
            database=data['database_path'],
            user=data['username'],
            password=data['password'],
            charset=data.get('charset', 'UTF8')
        )

        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
        table_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Connection successful! Found {table_count} tables.',
            'table_count': table_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Connection failed: {str(e)}'
        }), 400


@app.route('/api/test-cloud', methods=['POST'])
def test_cloud():
    """Test cloud API connection"""
    try:
        data = request.json

        url = f"{data['api_url']}/health"
        headers = {
            'X-API-Key': data['api_key'],
            'X-Organization-ID': str(data['organization_id'])
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            verify=data.get('verify_ssl', False)
        )

        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Cloud connection successful!',
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Cloud returned status {response.status_code}'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Connection failed: {str(e)}'
        }), 400


@app.route('/api/list-tables', methods=['POST'])
def list_tables():
    """List all tables in Firebird database"""
    try:
        data = request.json

        conn = fdb.connect(
            host=data.get('host', 'localhost'),
            port=int(data.get('port', 3050)),
            database=data['database_path'],
            user=data['username'],
            password=data['password'],
            charset=data.get('charset', 'UTF8')
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT RDB$RELATION_NAME
            FROM RDB$RELATIONS
            WHERE RDB$SYSTEM_FLAG = 0 AND RDB$VIEW_BLR IS NULL
            ORDER BY RDB$RELATION_NAME
        """)

        tables = [row[0].strip() for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        # Categorize tables
        guest_tables = [t for t in tables if any(keyword in t.upper() for keyword in ['GUEST', 'TAMU', 'RESERVATION', 'BOOKING'])]
        room_tables = [t for t in tables if any(keyword in t.upper() for keyword in ['ROOM', 'KAMAR', 'CHAMBER'])]

        return jsonify({
            'success': True,
            'tables': tables,
            'guest_tables': guest_tables,
            'room_tables': room_tables,
            'total': len(tables)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list tables: {str(e)}'
        }), 400


@app.route('/api/table-columns', methods=['POST'])
def get_table_columns():
    """Get columns for a specific table"""
    try:
        data = request.json
        table_name = data['table_name']

        from table_mapper import TableMapper

        mapper = TableMapper(data)
        mapper.connect()
        columns = mapper.get_table_columns(table_name)
        mapper.close()

        return jsonify({
            'success': True,
            'table_name': table_name,
            'columns': columns,
            'total': len(columns)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get columns: {str(e)}'
        }), 400


@app.route('/api/table-mapping', methods=['POST'])
def update_table_mapping():
    """Update table mapping configuration"""
    try:
        data = request.json
        config = load_config()

        # Update tables configuration
        if 'tables' in data:
            config['tables'] = data['tables']

        save_config(config)
        return jsonify({'success': True, 'message': 'Table mapping saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/state')
def get_state():
    """Get agent state"""
    return jsonify(agent_state)


@app.route('/api/sync-now', methods=['POST'])
def sync_now():
    """Trigger immediate sync"""
    try:
        config = load_config()

        # Test connections first
        firebird_reader = FirebirdReader(config['firebird'])
        cloud_client = CloudSyncClient(config['cloud'])

        if not cloud_client.test_connection():
            return jsonify({
                'success': False,
                'message': 'Cannot connect to cloud backend'
            }), 400

        # Sync guests
        guests = firebird_reader.get_recent_checkins(minutes=config['sync']['interval_minutes'])
        guest_count = len(guests)

        if guests:
            from models import GuestData
            guest_data = [GuestData.from_firebird(g, config['cloud']['organization_id']) for g in guests]
            cloud_client.sync_guests(guest_data)

        # Sync rooms
        rooms = firebird_reader.get_room_status()
        room_count = len(rooms)

        if rooms:
            from models import RoomStatus
            room_data = [RoomStatus.from_firebird(r, config['cloud']['organization_id']) for r in rooms]
            cloud_client.sync_rooms(room_data)

        firebird_reader.close()

        # Update state
        agent_state['last_sync'] = datetime.now().isoformat()
        agent_state['sync_count'] += 1
        agent_state['guest_count'] = guest_count
        agent_state['room_count'] = room_count
        agent_state['last_error'] = None

        return jsonify({
            'success': True,
            'message': f'Sync completed! Guests: {guest_count}, Rooms: {room_count}',
            'guest_count': guest_count,
            'room_count': room_count
        })
    except Exception as e:
        agent_state['last_error'] = str(e)
        return jsonify({
            'success': False,
            'message': f'Sync failed: {str(e)}'
        }), 500


# =============================================================================
# MAIN
# =============================================================================


if __name__ == '__main__':
    # Create default config if not exists
    if not os.path.exists(CONFIG_FILE):
        save_config(get_default_config())
        print(f"Created default configuration: {CONFIG_FILE}")

    print("=" * 80)
    print("Firebird Bridge Agent - Web UI")
    print("=" * 80)
    print("Starting web interface...")
    print("Access at: http://localhost:5000")
    print("=" * 80)

    app.run(host='0.0.0.0', port=5000, debug=True)
