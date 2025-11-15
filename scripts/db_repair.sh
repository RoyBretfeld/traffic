#!/bin/bash

# SQLite Datenbank-Reparatur-Skript
# Stellt eine potenziell korrupte SQLite-Datenbank wieder her.

DB_FILE="./app.db"
BACKUP_FILE="./app.db.bak"
DUMP_FILE="./dump.sql"
NEW_DB_FILE="./app_repaired.db"

echo "Starting SQLite database repair process for ${DB_FILE}"

if [ ! -f "${DB_FILE}" ]; then
  echo "Error: Database file ${DB_FILE} not found!"
  exit 1
fi

# 1. Datenbank sichern
echo "1. Creating backup of ${DB_FILE} to ${BACKUP_FILE}"
cp "${DB_FILE}" "${BACKUP_FILE}"
if [ $? -ne 0 ]; then
  echo "Error: Failed to create backup. Aborting."
  exit 1
fi

# 2. SQL-Dump erstellen
echo "2. Creating SQL dump from ${DB_FILE} to ${DUMP_FILE}"
sqlite3 "${DB_FILE}" ".mode insert" ".output ${DUMP_FILE}" ".dump" ".exit"
if [ $? -ne 0 ]; then
  echo "Error: Failed to create SQL dump. The database might be severely corrupted. Trying to create dump from backup."
  sqlite3 "${BACKUP_FILE}" ".mode insert" ".output ${DUMP_FILE}" ".dump" ".exit"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to create SQL dump from backup. Aborting."
    exit 1
  fi
fi

# 3. Neue Datenbank aus Dump erstellen
echo "3. Creating new database from dump to ${NEW_DB_FILE}"
sqlite3 "${NEW_DB_FILE}" ".read ${DUMP_FILE}" ".exit"
if [ $? -ne 0 ]; then
  echo "Error: Failed to create new database from dump. Aborting."
  exit 1
fi

# 4. Alte Datenbank umbenennen und neue Datenbank einsetzen
echo "4. Replacing original database with repaired one."
mv "${DB_FILE}" "${DB_FILE}.corrupted_$(date +%Y%m%d_%H%M%S)"
mv "${NEW_DB_FILE}" "${DB_FILE}"

# 5. Aufräumen
echo "5. Cleaning up temporary dump file."
rm "${DUMP_FILE}"

echo "Database repair process completed. Original database backed up to ${BACKUP_FILE}"
echo "You can remove the .corrupted_... file manually if the new database works fine."

exit 0
