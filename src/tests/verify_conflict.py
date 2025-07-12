import os
import sys
import pandas as pd
from datetime import datetime
sys.path.append(os.getcwd())  # ensure src is importable
from src.modules import database as db

# Prepare sample DataFrame with intentional internal duplicate and new unique row
sample_data = [
    {
        'file_path': 'test_script',
        'date': '2024-07-01',
        'hour': 1.0,
        'plate': 'P1',
        'well_name': 'A1',
        'x': 1,
        'y': 1,
        'assay': 'A',
        'theo_dose': 0,
        'real_dose': 0,
        'value': 0,
        'is_neg_control': 0
    },
    {
        'file_path': 'test_script',
        'date': '2024-07-01',
        'hour': 1.0,
        'plate': 'P1',
        'well_name': 'A1',
        'x': 1,
        'y': 1,
        'assay': 'A',
        'theo_dose': 0,
        'real_dose': 0,
        'value': 0,
        'is_neg_control': 0
    },  # duplicate primary key row
    {
        'file_path': 'test_script',
        'date': '2024-07-01',
        'hour': 2.0,
        'plate': 'P1',
        'well_name': 'A2',
        'x': 1,
        'y': 2,
        'assay': 'A',
        'theo_dose': 0,
        'real_dose': 0,
        'value': 0,
        'is_neg_control': 0
    },
]

df = pd.DataFrame(sample_data)

unique_df, dup_df = db.detect_internal_duplicates(df)
print(f"Detected internal duplicates: {len(dup_df)} row(s)")

non_conflicts_before, conflicts_before = db.find_conflicts(unique_df)
print(f"Conflicts with DB before insert: {len(conflicts_before)}")

# Insert non-conflicting unique rows
if not non_conflicts_before.empty:
    db.insert_records(non_conflicts_before)

# Verify insertion
non_conflicts_after, conflicts_after = db.find_conflicts(unique_df)
print(f"Conflicts with DB after insert: {len(conflicts_after)} (should equal number of inserted rows)")

# Clean up inserted test data for repeatability
if not conflicts_after.empty:
    db.replace_records(pd.DataFrame())  # no-op, placeholder for potential cleanup logic

print("Verification script completed successfully.")
