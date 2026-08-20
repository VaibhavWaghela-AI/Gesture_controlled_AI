import pandas as pd
import os

CSV_FILE = 'imu_data.csv'

print(f"--- CHECKING {CSV_FILE} ---")

if not os.path.exists(CSV_FILE):
    print("❌ ERROR: File not found. You need to collect data first!")
    exit()

# 1. Read the file
try:
    df = pd.read_csv(CSV_FILE)
    print(f"Found {len(df)} rows.")
except Exception as e:
    print(f"❌ ERROR reading file: {e}")
    exit()

# 2. Check for the 'label' column
if 'label' not in df.columns:
    print("⚠️ HEADER MISSING! The file has data but no labels.")
    print("   Repairing file now...")
    
    # Reload the file assuming NO header (so we don't lose the first row of data)
    df = pd.read_csv(CSV_FILE, header=None)
    
    # Check if we have 7 columns (label + 6 sensors)
    if df.shape[1] == 7:
        # Assign the correct headers manually
        df.columns = ["label", "ax", "ay", "az", "gx", "gy", "gz"]
        
        # Save it back overwriting the old broken file
        df.to_csv(CSV_FILE, index=False)
        print("✅ SUCCESS: Headers added! File saved.")
        print("   You can now run the Training Script.")
    else:
        print(f"❌ CRITICAL ERROR: Your data has {df.shape[1]} columns, but we expected 7.")
        print("   The file might be corrupted. It is safest to delete it and re-collect.")
else:
    print("✅ The file already has headers. The error might be a typo in your code.")
    print(f"   Columns found: {list(df.columns)}")