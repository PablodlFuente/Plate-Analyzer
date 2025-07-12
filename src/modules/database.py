"""
Database module for the Plates Analyzer application.
HHandles all interactions with the SQLite database.
"""
import sqlite3
import logging
from datetime import datetime
import pandas as pd
import numpy as np  # Added to safely convert numpy scalars to Python types

DB_FILE = "data/plate_data.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Creates the plate_readings table if it doesn't exist."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plate_readings (
                    file_path TEXT,
                    date TEXT,
                    hour REAL,
                    plate TEXT,
                    well_name TEXT,
                    x INTEGER,
                    y INTEGER,
                    assay TEXT,
                    theo_dose REAL,
                    real_dose REAL,
                    value REAL,
                    is_neg_control INTEGER,
                    update_datetime TEXT,
                    PRIMARY KEY (date, hour, plate, x, y, assay)
                )
            """)
            conn.commit()
            logging.getLogger('plate_analyzer').info("Database table 'plate_readings' created.")
    except sqlite3.Error as e:
        logging.getLogger('plate_analyzer').error(f"Database error while creating table: {e}")
        raise

def _to_py(value):
    """Convert numpy scalar types to native Python scalars to avoid
    inserting BLOBs into SQLite or failing to match during queries."""
    if isinstance(value, (np.generic,)):
        return value.item()
    return value

def find_conflicts(data_df):
    """Find rows in the DataFrame that conflict with existing DB records.
    Returns tuple: (non_conflicts_df, incoming_conflicts_df, existing_conflicts_df).
    existing_conflicts_df rows correspond one-to-one with incoming_conflicts_df order.
    """
    if data_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    primary_keys = ['date', 'hour', 'plate', 'x', 'y', 'assay']
    conflicting_indices = []
    non_conflicting_indices = []
    existing_rows = []

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check for each row individually for maximum robustness
        for index, row in data_df.iterrows():
            query = "SELECT * FROM plate_readings WHERE date=? AND hour=? AND plate=? AND x=? AND y=? AND assay=?"
            # Ensure numeric params are native Python scalars (not numpy types)
            params = (
                row['date'],
                _to_py(row['hour']),
                row['plate'],
                _to_py(row['x']),
                _to_py(row['y']),
                row['assay']
            )
            logging.getLogger('plate_analyzer').debug(f"find_conflicts query params: {params}")
            cursor.execute(query, params)
            match = cursor.fetchone()
            if match:
                conflicting_indices.append(index)
                existing_rows.append(dict(match))
            else:
                non_conflicting_indices.append(index)

    incoming_conflicts = data_df.loc[conflicting_indices]
    non_conflicts = data_df.loc[non_conflicting_indices]
    existing_conflicts = pd.DataFrame(existing_rows) if existing_rows else pd.DataFrame()

    return non_conflicts, incoming_conflicts, existing_conflicts

def detect_internal_duplicates(data_df):
    """Return a DataFrame with duplicated primary keys within the incoming data."""
    primary_keys = ['date', 'hour', 'plate', 'x', 'y', 'assay']
    dup_mask = data_df.duplicated(subset=primary_keys, keep=False)
    duplicates_df = data_df[dup_mask].copy()
    unique_df = data_df[~dup_mask].copy()
    return unique_df, duplicates_df


def insert_records(data_df):
    """Insert rows using INSERT OR REPLACE (so user choice governs)."""
    if data_df.empty:
        return

        # Convert numpy scalar types to native Python types for SQLite compatibility
    data_df = data_df.map(_to_py)
    data_df['update_datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db_connection() as conn:
        cols = list(data_df.columns)
        placeholders = ', '.join(['?'] * len(cols))
        # Use INSERT, not INSERT OR REPLACE. Conflicts should be handled before this function is called.
        # Using INSERT will raise an IntegrityError if a conflict exists, which is safer than silent replacement.
        sql = f"INSERT INTO plate_readings ({', '.join(cols)}) VALUES ({placeholders})"
        cursor = conn.cursor()
        records = [tuple(row) for row in data_df.to_numpy()]
        cursor.executemany(sql, records)
        conn.commit()

def replace_records(data_df):
    """Inserts new records or replaces them if they already exist."""
    if data_df.empty:
        return
        # Convert numpy scalar types to native Python types for SQLite compatibility
    data_df = data_df.map(_to_py)
    data_df['update_datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db_connection() as conn:
        cols = ', '.join(data_df.columns)
        placeholders = ', '.join(['?'] * len(data_df.columns))
        sql = f'INSERT OR REPLACE INTO plate_readings ({cols}) VALUES ({placeholders})'
        cursor = conn.cursor()
        records = [tuple(row) for row in data_df.to_numpy()]
        cursor.executemany(sql, records)
        conn.commit()

def delete_all_records():
    """Delete ALL rows from plate_readings table. Use with extreme caution."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM plate_readings")
        conn.commit()
    logging.getLogger('plate_analyzer').warning("All records deleted from database by user action.")

# Ensure the table is created when the module is imported
create_table()
