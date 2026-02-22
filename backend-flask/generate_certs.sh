#!/bin/bash
# Generate self-signed SSL certificates for development/testing
# For production, use certificates from a trusted CA (e.g., Let's Encrypt)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$SCRIPT_DIR/certs"

# Create certs directory if not exists
mkdir -p "$CERTS_DIR"

# Certificate settings
COUNTRY="CN"
STATE="Beijing"
CITY="Beijing"
ORG="Sensor Server"
OU="IT"
DOMAIN="localhost"
DAYS=365

echo "Generating self-signed SSL certificate..."
echo "Certificate will be valid for $DAYS days"
echo ""

# Generate private key and certificate
openssl req -x509 -nodes -days $DAYS -newkey rsa:2048 \
    -keyout "$CERTS_DIR/server.key" \
    -out "$CERTS_DIR/server.crt" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1"

# Set proper permissions
chmod 600 "$CERTS_DIR/server.key"
chmod 644 "$CERTS_DIR/server.crt"

echo ""
echo "SSL certificates generated successfully!"
echo "  Certificate: $CERTS_DIR/server.crt"
echo "  Private Key: $CERTS_DIR/server.key"
echo ""
echo "To enable HTTPS, set the following environment variables:"
echo "  export SSL_ENABLED=true"
echo "  export SSL_CERT_FILE=certs/server.crt"
echo "  export SSL_KEY_FILE=certs/server.key"
echo "  export SSL_PORT=443"
echo ""
echo "Or add to .env file:"
echo "  SSL_ENABLED=true"
echo "  SSL_CERT_FILE=certs/server.crt"
echo "  SSL_KEY_FILE=certs/server.key"
echo "  SSL_PORT=443"
