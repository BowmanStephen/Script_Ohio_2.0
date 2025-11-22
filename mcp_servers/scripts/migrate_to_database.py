#!/usr/bin/env python3
"""
Database Migration Script for Script Ohio 2.0
==============================================

Migrates CSV data to SQLite and PostgreSQL databases for MCP server integration.
Handles schema creation, data import, and validation.

Usage:
    python migrate_to_database.py [--source ../starter_pack/data/] [--target sqlite|postgres] [--db-path data/databases/football_analysis.db]
"""

import os
import sys
import sqlite3
import pandas as pd
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class DatabaseMigrator:
    """Handles migration of CSV data to database formats"""

    def __init__(self, source_dir: str, target_db: str, db_path: str = None):
        self.source_dir = Path(source_dir)
        self.target_db = target_db
        self.db_path = Path(db_path) if db_path else Path("data/databases/football_analysis.db")
        self.setup_logging()

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"migration_{timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("DatabaseMigrator")

    def discover_csv_files(self) -> Dict[str, Path]:
        """Discover all CSV files in source directory"""
        csv_files = {}

        if not self.source_dir.exists():
            self.logger.error(f"Source directory does not exist: {self.source_dir}")
            return csv_files

        for csv_file in self.source_dir.rglob("*.csv"):
            # Create table name from filename
            table_name = csv_file.stem.lower().replace(" ", "_").replace("-", "_")
            csv_files[table_name] = csv_file
            self.logger.info(f"Found CSV file: {csv_file} -> {table_name}")

        return csv_files

    def create_sqlite_schema(self, csv_files: Dict[str, Path]) -> bool:
        """Create SQLite database schema from CSV files"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            self.logger.info(f"Creating SQLite database: {self.db_path}")

            for table_name, csv_file in csv_files.items():
                try:
                    # Read CSV to infer schema
                    df = pd.read_csv(csv_file, nrows=100)  # Read first 100 rows for schema inference

                    # Generate CREATE TABLE statement
                    columns = []
                    for col in df.columns:
                        # Simple type inference
                        sample_values = df[col].dropna().head(10)

                        if len(sample_values) == 0:
                            dtype = "TEXT"
                        elif pd.api.types.is_numeric_dtype(sample_values):
                            if df[col].dtype == 'int64':
                                dtype = "INTEGER"
                            else:
                                dtype = "REAL"
                        elif pd.api.types.is_datetime64_any_dtype(sample_values):
                            dtype = "TEXT"  # Store dates as text for simplicity
                        else:
                            dtype = "TEXT"

                        columns.append(f"{col.lower().replace(' ', '_').replace('-', '_')} {dtype}")

                    # Create table
                    create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        {', '.join(columns)}
                    )
                    """

                    cursor.execute(create_sql)
                    self.logger.info(f"Created table: {table_name}")

                except Exception as e:
                    self.logger.error(f"Error creating table {table_name}: {e}")
                    continue

            conn.commit()
            conn.close()
            self.logger.info("SQLite schema creation completed")
            return True

        except Exception as e:
            self.logger.error(f"Error creating SQLite schema: {e}")
            return False

    def migrate_to_sqlite(self, csv_files: Dict[str, Path]) -> bool:
        """Migrate CSV data to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)

            total_rows = 0

            for table_name, csv_file in csv_files.items():
                try:
                    self.logger.info(f"Migrating {csv_file.name} to table {table_name}")

                    # Read CSV in chunks to handle large files
                    chunk_size = 10000
                    chunks = pd.read_csv(csv_file, chunksize=chunk_size)

                    table_rows = 0

                    for chunk_num, chunk in enumerate(chunks):
                        # Clean column names
                        chunk.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in chunk.columns]

                        # Insert data
                        chunk.to_sql(table_name, conn, if_exists='append', index=False)
                        table_rows += len(chunk)

                        if chunk_num % 10 == 0:  # Log every 10 chunks
                            self.logger.info(f"  Processed chunk {chunk_num + 1}, rows so far: {table_rows}")

                    total_rows += table_rows
                    self.logger.info(f"✅ Migrated {table_rows} rows to {table_name}")

                except Exception as e:
                    self.logger.error(f"Error migrating {csv_file}: {e}")
                    continue

            conn.close()

            # Get database size
            db_size = self.db_path.stat().st_size / (1024 * 1024)  # MB
            self.logger.info(f"SQLite migration completed: {total_rows} total rows, database size: {db_size:.2f} MB")

            return True

        except Exception as e:
            self.logger.error(f"Error during SQLite migration: {e}")
            return False

    def validate_sqlite_data(self) -> bool:
        """Validate migrated SQLite data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            self.logger.info(f"Validating {len(tables)} tables in SQLite database")

            for table_tuple in tables:
                table_name = table_tuple[0]

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                # Get column count
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                self.logger.info(f"  {table_name}: {row_count} rows, {len(columns)} columns")

            conn.close()
            self.logger.info("SQLite data validation completed")
            return True

        except Exception as e:
            self.logger.error(f"Error validating SQLite data: {e}")
            return False

    def create_indexes(self) -> bool:
        """Create performance indexes for common queries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            self.logger.info("Creating database indexes...")

            # Common indexes for football data
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_games_season ON games(season)",
                "CREATE INDEX IF NOT EXISTS idx_games_week ON games(week)",
                "CREATE INDEX IF NOT EXISTS idx_games_home_team ON games(home_team)",
                "CREATE INDEX IF NOT EXISTS idx_games_away_team ON games(away_team)",
                "CREATE INDEX IF NOT EXISTS idx_teams_conference ON teams(conference)",
                "CREATE INDEX IF NOT EXISTS idx_plays_game_id ON plays(game_id)",
                "CREATE INDEX IF NOT EXISTS idx_plays_team ON plays(offense)",
            ]

            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    self.logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except sqlite3.Error as e:
                    self.logger.warning(f"Index creation failed: {e}")

            conn.commit()
            conn.close()
            self.logger.info("Index creation completed")
            return True

        except Exception as e:
            self.logger.error(f"Error creating indexes: {e}")
            return False

    def run_migration(self) -> bool:
        """Run complete migration process"""
        self.logger.info(f"Starting migration to {self.target_db.upper()}")

        # Discover CSV files
        csv_files = self.discover_csv_files()
        if not csv_files:
            self.logger.error("No CSV files found for migration")
            return False

        self.logger.info(f"Found {len(csv_files)} CSV files to migrate")

        if self.target_db.lower() == 'sqlite':
            # Create schema
            if not self.create_sqlite_schema(csv_files):
                return False

            # Migrate data
            if not self.migrate_to_sqlite(csv_files):
                return False

            # Create indexes
            if not self.create_indexes():
                return False

            # Validate data
            if not self.validate_sqlite_data():
                return False

            self.logger.info("✅ SQLite migration completed successfully")
            return True

        else:
            self.logger.error(f"Target database '{self.target_db}' not yet implemented")
            return False

def main():
    parser = argparse.ArgumentParser(description="Migrate CSV data to database")
    parser.add_argument("--source", default="../starter_pack/data/",
                       help="Source directory containing CSV files")
    parser.add_argument("--target", choices=["sqlite", "postgres"], default="sqlite",
                       help="Target database type")
    parser.add_argument("--db-path", default="data/databases/football_analysis.db",
                       help="Database file path for SQLite")

    args = parser.parse_args()

    # Create migrator
    migrator = DatabaseMigrator(args.source, args.target, args.db_path)

    # Run migration
    if migrator.run_migration():
        print(f"\n🎉 Migration to {args.target.upper()} completed successfully!")
        print(f"Database location: {migrator.db_path}")
    else:
        print(f"\n❌ Migration to {args.target.upper()} failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()