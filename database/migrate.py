#!/usr/bin/env python3
"""
Database migration utility for code-to-doc project.
Handles applying and rolling back database migrations.
"""

import os
import sys
import psycopg2
from pathlib import Path
from typing import List, Tuple
import argparse
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'code_to_doc',
    'user': os.getenv('DB_USER', os.getenv('USER')),
    'password': os.getenv('DB_PASSWORD', '')
}

class MigrationManager:
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.migrations_dir = Path(__file__).parent.parent / 'migrations'

    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)

    def ensure_migration_table(self):
        """Ensure migration tracking table exists."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS applied_migrations (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(255) UNIQUE NOT NULL,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        checksum VARCHAR(64)
                    )
                """)
                conn.commit()

    def get_migration_files(self) -> List[Path]:
        """Get all migration files sorted by name."""
        if not self.migrations_dir.exists():
            return []

        files = [f for f in self.migrations_dir.glob('*.sql') if f.is_file()]
        return sorted(files)

    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT filename FROM applied_migrations ORDER BY filename")
                return [row[0] for row in cur.fetchall()]

    def calculate_checksum(self, filepath: Path) -> str:
        """Calculate MD5 checksum of migration file."""
        import hashlib
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def apply_migration(self, filepath: Path) -> bool:
        """Apply a single migration file."""
        filename = filepath.name
        checksum = self.calculate_checksum(filepath)

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Read and execute migration
                    with open(filepath, 'r') as f:
                        migration_sql = f.read()

                    # Skip if it's just a record file (contains no actual SQL)
                    if 'DROP SCHEMA public CASCADE' in migration_sql and 'already been applied' in migration_sql:
                        print(f"Skipping record-only migration: {filename}")
                        cur.execute("""
                            INSERT INTO applied_migrations (filename, checksum)
                            VALUES (%s, %s)
                            ON CONFLICT (filename) DO NOTHING
                        """, (filename, checksum))
                        conn.commit()
                        return True

                    # Execute migration SQL
                    cur.execute(migration_sql)

                    # Record migration as applied
                    cur.execute("""
                        INSERT INTO applied_migrations (filename, checksum)
                        VALUES (%s, %s)
                        ON CONFLICT (filename) DO UPDATE SET
                            applied_at = CURRENT_TIMESTAMP,
                            checksum = EXCLUDED.checksum
                    """, (filename, checksum))

                    conn.commit()
                    print(f"Applied migration: {filename}")
                    return True

        except Exception as e:
            print(f"Error applying migration {filename}: {e}")
            return False

    def migrate_up(self, target: str = None) -> bool:
        """Apply pending migrations up to target (or all if None)."""
        self.ensure_migration_table()

        migration_files = self.get_migration_files()
        applied_migrations = set(self.get_applied_migrations())

        pending = [f for f in migration_files if f.name not in applied_migrations]

        if target:
            # Apply only up to target migration
            target_found = False
            filtered_pending = []
            for f in pending:
                filtered_pending.append(f)
                if f.name == target:
                    target_found = True
                    break

            if not target_found:
                print(f"Target migration {target} not found in pending migrations")
                return False

            pending = filtered_pending

        if not pending:
            print("No pending migrations to apply")
            return True

        print(f"Applying {len(pending)} migration(s)...")
        success = True

        for migration_file in pending:
            if not self.apply_migration(migration_file):
                success = False
                break

        return success

    def status(self):
        """Show migration status."""
        self.ensure_migration_table()

        migration_files = self.get_migration_files()
        applied_migrations = self.get_applied_migrations()

        print("Migration Status:")
        print("================")

        if not migration_files:
            print("No migration files found")
            return

        for migration_file in migration_files:
            filename = migration_file.name
            status = "APPLIED" if filename in applied_migrations else "PENDING"
            print(f"{filename:<40} {status}")

        print(f"\nTotal migrations: {len(migration_files)}")
        print(f"Applied: {len(applied_migrations)}")
        print(f"Pending: {len(migration_files) - len(applied_migrations)}")

def main():
    parser = argparse.ArgumentParser(description='Database migration manager')
    parser.add_argument('command', choices=['up', 'status'],
                       help='Migration command to execute')
    parser.add_argument('--target', '-t',
                       help='Target migration file for up command')

    args = parser.parse_args()

    manager = MigrationManager(DB_CONFIG)

    try:
        if args.command == 'up':
            success = manager.migrate_up(args.target)
            sys.exit(0 if success else 1)
        elif args.command == 'status':
            manager.status()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()