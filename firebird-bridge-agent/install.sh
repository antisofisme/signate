#!/bin/bash
# Firebird Bridge Agent Installation Script

echo "Installing Firebird Bridge Agent..."

# Create directory structure
mkdir -p /opt/firebird-bridge
mkdir -p /var/log/firebird-bridge
mkdir -p /etc/firebird-bridge

# Copy files
cp agent.py /opt/firebird-bridge/
cp firebird_reader.py /opt/firebird-bridge/
cp cloud_sync.py /opt/firebird-bridge/
cp models.py /opt/firebird-bridge/
cp requirements.txt /opt/firebird-bridge/
cp config.yaml /etc/firebird-bridge/config.yaml

# Install Python dependencies
cd /opt/firebird-bridge
pip3 install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/firebird-bridge.service <<EOF
[Unit]
Description=Firebird Bridge Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/firebird-bridge
ExecStart=/usr/bin/python3 /opt/firebird-bridge/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chmod +x /opt/firebird-bridge/agent.py
chmod 644 /etc/firebird-bridge/config.yaml

# Enable and start service
systemctl daemon-reload
systemctl enable firebird-bridge

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit config: /etc/firebird-bridge/config.yaml"
echo "2. Start service: systemctl start firebird-bridge"
echo "3. View logs: journalctl -u firebird-bridge -f"
echo ""
