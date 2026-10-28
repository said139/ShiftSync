#!/usr/bin/env bash
ENV_FILE="C:/Users/saidm/Desktop/SHIFTSYNC/.env"
PSQL="/c/Program Files/PostgreSQL/17/bin/psql.exe"

printf "Enter PostgreSQL password for user 'postgres' (typing hidden): "
read -rs val
echo ""

export PGPASSWORD="$val"
if "$PSQL" -U postgres -h 127.0.0.1 -p 5432 -c "SELECT 1;" >/dev/null 2>&1; then
    echo "Connection to PostgreSQL succeeded!"
    # Create shiftsync_db if it doesn't exist
    "$PSQL" -U postgres -h 127.0.0.1 -p 5432 -tc "SELECT 1 FROM pg_database WHERE datname = 'shiftsync_db'" | grep -q 1 || \
        "$PSQL" -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE shiftsync_db;"
    grep -v "^POSTGRES_PASSWORD=" "$ENV_FILE" 2>/dev/null > "${ENV_FILE}.tmp" || true
    echo "POSTGRES_PASSWORD=$val" >> "${ENV_FILE}.tmp"
    mv "${ENV_FILE}.tmp" "$ENV_FILE"
    echo "Database 'shiftsync_db' is ready and credential saved to $ENV_FILE."
else
    echo "ERROR: PostgreSQL rejected that password for user 'postgres'. Please double-check your PostgreSQL password and try again."
    exit 1
fi
