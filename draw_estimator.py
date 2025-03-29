import csv
from datetime import datetime
import os # To check if files exist

# --- Configuration ---
UPPERCLASS_FILENAME = 'UpperclassTimeOrder2025 (1).csv'
# Use a relative path or ensure the script is in the same directory as the CSV
# Alternatively, provide the full path, e.g., '/path/to/your/file/UpperclassTimeOrder2025 (1).csv'

RES_COLLEGE_TOP_N = 50 # Number of top drawers in res college likely to take a spot there

# --- Helper Functions ---

def load_draw_data(filepath):
    """Loads data from a draw time CSV file."""
    data = []
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return None
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as infile: # utf-8-sig handles BOM
            reader = csv.DictReader(infile)
            for row in reader:
                try:
                    # Attempt to parse the Draw Time
                    row['Draw Time Obj'] = datetime.strptime(row['Draw Time'], '%m/%d/%y %I:%M %p')
                    data.append(row)
                except ValueError as e:
                    print(f"Warning: Could not parse date in row: {row}. Error: {e}. Skipping row.")
                except KeyError as e:
                    print(f"Warning: Missing expected column '{e}' in file {filepath}. Check CSV header. Skipping row {row}")
                    continue # Skip rows with missing keys if critical like 'Draw Time'
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None

    # Sort by Draw Time Object just in case the file isn't perfectly sorted
    data.sort(key=lambda x: x.get('Draw Time Obj', datetime.max)) # Handle potential missing Draw Time Obj
    return data

def find_user_position(data, first_name, last_name):
    """Finds the user's dictionary and index in the data list."""
    first_name_lower = first_name.lower()
    last_name_lower = last_name.lower()
    for index, person in enumerate(data):
        # Compare case-insensitively
        if (person.get('First Name', '').lower() == first_name_lower and
            person.get('Last Name', '').lower() == last_name_lower):
            return person, index
    return None, -1 # User not found

def get_residential_college_early_drawers(top_n):
    """Gets PUIDs of top N drawers from multiple residential college files."""
    early_drawer_puids = set()
    print("\nEnter paths to Residential College CSV files.")
    print("Press Enter without typing a path when you are done adding files.")

    while True:
        filepath = input("Path to Residential College CSV (or press Enter to finish): ").strip()
        if not filepath:
            break

        print(f"Processing {filepath}...")
        college_data = load_draw_data(filepath)

        if college_data:
            count = 0
            for person in college_data:
                if count < top_n:
                    puid = person.get('PUID')
                    if puid:
                        early_drawer_puids.add(puid)
                        count += 1
                    else:
                         print(f"Warning: Row in {filepath} missing PUID: {person}. Skipping for early drawer check.")
                else:
                    break # Stop after processing top_n
            print(f"Added PUIDs for the top {count} drawers from {filepath}.")
        else:
            print(f"Skipping file {filepath} due to loading errors.")

    return early_drawer_puids

# --- Main Program Logic ---

print("--- Upperclassmen Housing Draw Estimator ---")

# 1. Load Upperclassmen Data
print(f"Loading upperclassmen data from {UPPERCLASS_FILENAME}...")
upperclass_data = load_draw_data(UPPERCLASS_FILENAME)

if not upperclass_data:
    print("Could not load upperclassmen data. Exiting.")
    exit()

print(f"Loaded {len(upperclass_data)} entries from upperclassmen list.")

# 2. Get User Input
user_first_name = input("Enter your First Name: ").strip()
user_last_name = input("Enter your Last Name: ").strip()

# 3. Find User in Upperclassmen List
user_info, user_index = find_user_position(upperclass_data, user_first_name, user_last_name)

if user_index == -1:
    print(f"\nUser '{user_first_name} {user_last_name}' not found in the upperclassmen list.")
    exit()

print(f"\nFound user: {user_info['First Name']} {user_info['Last Name']}")
print(f"  Draw Time: {user_info['Draw Time']}")
print(f"  Position in Upperclassmen Draw: {user_index + 1} out of {len(upperclass_data)}")

# 4. Identify People Ahead of the User (Initially)
people_ahead_initial = upperclass_data[:user_index]
initial_count = len(people_ahead_initial)
print(f"\nInitially, there are {initial_count} people scheduled to draw before you.")

if initial_count == 0:
    print("You have the first draw time! No filtering needed.")
    exit()

# 5. Get Residential College Early Drawers
print(f"\nNow, let's identify students likely to take spots in their Residential Colleges (Top {RES_COLLEGE_TOP_N}).")
early_res_college_puids = get_residential_college_early_drawers(RES_COLLEGE_TOP_N)
print(f"\nIdentified {len(early_res_college_puids)} unique PUIDs from the top {RES_COLLEGE_TOP_N} of provided residential college lists.")

# 6. Filter the "Ahead" List
people_ahead_filtered = []
removed_count = 0
print("\nFiltering the list of people ahead of you...")

for person in people_ahead_initial:
    puid = person.get('PUID')
    if not puid:
        print(f"Warning: Person ahead of you has no PUID: {person.get('First Name')} {person.get('Last Name')}. Cannot filter.")
        people_ahead_filtered.append(person) # Keep them if PUID is missing? Or discard? Keeping for now.
    elif puid not in early_res_college_puids:
        people_ahead_filtered.append(person)
    else:
        # This person is ahead *and* is an early drawer in a residential college
        # print(f"  - Removing {person.get('First Name')} {person.get('Last Name')} (PUID: {puid}) - likely taking Res College spot.")
        removed_count += 1

final_count = len(people_ahead_filtered)

# 7. Display Final Results
print("\n--- Final Estimate ---")
print(f"User: {user_info['First Name']} {user_info['Last Name']}")
print(f"Your Upperclassmen Draw Position: {user_index + 1}")
print(f"Initial number of people drawing before you: {initial_count}")
print(f"Number of those people likely taking a Residential College spot (Top {RES_COLLEGE_TOP_N}): {removed_count}")
print(f"Estimated number of people ACTUALLY drawing for Upperclassmen housing before you: {final_count}")

# Optional: Print the names of those still ahead
# print("\nPeople estimated to draw before you for Upperclassmen Housing:")
# if final_count > 0:
#     for i, person in enumerate(people_ahead_filtered):
#         print(f"  {i+1}. {person.get('First Name')} {person.get('Last Name')} (PUID: {person.get('PUID')}, Time: {person.get('Draw Time')})")
# else:
#      print("  (None)")