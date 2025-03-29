import csv
from datetime import datetime
import os

# --- Configuration ---
UPPERCLASS_FILENAME = 'UpperclassTimeOrder2025 (1).csv'
AVAILABLE_ROOMS_FILENAME = 'AvailableRoomsList2025.csv'
SPELMAN_DRAW_FILENAME = 'SpelmanTimeOrder2025.csv' # Specific file for Spelman draw times

RES_COLLEGE_TOP_N = 50 # Number of top drawers in *other* res colleges likely to take a spot there

# --- Helper Functions ---

def load_draw_data(filepath):
    """Loads data from a draw time CSV file (Upperclass or Res College)."""
    data = []
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return None
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            required_cols = ['PUID', 'Draw Time', 'Last Name', 'First Name']
            if not all(col in reader.fieldnames for col in required_cols):
                missing = [col for col in required_cols if col not in reader.fieldnames]
                print(f"Error: File {filepath} is missing required columns: {missing}. Check CSV header.")
                return None

            for i, row in enumerate(reader):
                try:
                    # Attempt to parse the Draw Time
                    row['Draw Time Obj'] = datetime.strptime(row['Draw Time'], '%m/%d/%y %I:%M %p')
                    # Store original row number for tie-breaking if times are identical
                    row['Original Row'] = i
                    data.append(row)
                except ValueError as e:
                    print(f"Warning: Could not parse date in row: {row} from {filepath}. Error: {e}. Skipping row.")
                except KeyError as e:
                    # This check is less likely now due to the fieldname check above, but keep for safety
                    print(f"Warning: Missing expected column '{e}' in file {filepath}. Check CSV header. Skipping row {row}")
                    continue
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None

    # Sort primarily by Draw Time Object, secondarily by original row number for stable sort
    data.sort(key=lambda x: (x.get('Draw Time Obj', datetime.max), x.get('Original Row', float('inf'))))
    return data

def load_rooms_data(filepath):
    """Loads data from the available rooms CSV file."""
    data = []
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return None
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            required_cols = ['College', 'Dorm', 'Room', 'Type'] # Sq Foot and Independent are optional for this logic
            if not all(col in reader.fieldnames for col in required_cols):
                missing = [col for col in required_cols if col not in reader.fieldnames]
                print(f"Error: File {filepath} is missing required columns: {missing}. Check CSV header.")
                return None
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None
    return data

def calculate_spelman_capacity(rooms_data):
    """Calculates the total number of student spots available in Spelman."""
    capacity = 0
    # Define capacity mapping for room types
    room_type_map = {
        'SINGLE': 1,
        'DOUBLE': 2,
        'TRIPLE': 3,
        'QUAD': 4,
        'QUINT': 5,
        '6PERSON': 6
    }
    count_spelman_rooms = 0

    if not rooms_data:
        print("Warning: Cannot calculate Spelman capacity because room data failed to load.")
        return 0

    for room in rooms_data:
        # Check if the room is in Upperclass Spelman
        # Case-insensitive matching for robustness
        college = room.get('College', '').strip().lower()
        dorm = room.get('Dorm', '').strip().lower()

        if college == 'upperclass' and dorm == 'spelman':
            count_spelman_rooms += 1
            room_type = room.get('Type', '').strip().upper()
            spots = room_type_map.get(room_type, 0)
            if spots == 0 and room_type:
                print(f"Warning: Unknown room type '{room.get('Type')}' for Spelman room {room.get('Room')}. Assuming 0 capacity.")
            capacity += spots

    print(f"Found {count_spelman_rooms} rooms listed in Upperclass Spelman.")
    return capacity

def get_top_spelman_drawers(spelman_data, capacity):
    """Gets PUIDs of the top 'capacity' number of drawers from the Spelman-specific list."""
    puids = set()
    if not spelman_data:
        print("Warning: Cannot get top Spelman drawers because Spelman draw data failed to load.")
        return puids
    if capacity <= 0:
        print("Warning: Calculated Spelman capacity is zero or less. No Spelman drawers will be filtered.")
        return puids

    count = 0
    for person in spelman_data:
        if count < capacity:
            puid = person.get('PUID')
            if puid:
                puids.add(puid)
                count += 1
            else:
                print(f"Warning: Row in Spelman data missing PUID: {person}. Skipping for top drawer check.")
        else:
            break # Stop after processing 'capacity' number of drawers
    print(f"Identified the top {count} PUIDs from the Spelman draw list based on calculated capacity.")
    return puids


def find_user_position(data, first_name, last_name):
    """Finds the user's dictionary and index in the data list."""
    first_name_lower = first_name.lower()
    last_name_lower = last_name.lower()
    for index, person in enumerate(data):
        # Compare case-insensitively and strip whitespace
        if (person.get('First Name', '').strip().lower() == first_name_lower and
            person.get('Last Name', '').strip().lower() == last_name_lower):
            return person, index
    return None, -1 # User not found

def get_residential_college_early_drawers(top_n, exclude_file=None):
    """Gets PUIDs of top N drawers from multiple residential college files, excluding one."""
    early_drawer_puids = set()
    print(f"\nEnter paths to OTHER Residential College CSV files (excluding {exclude_file}).")
    print("Press Enter without typing a path when you are done adding files.")

    while True:
        filepath = input("Path to OTHER Residential College CSV (or press Enter to finish): ").strip()
        if not filepath:
            break

        # Normalize paths for comparison (optional but good practice)
        normalized_filepath = os.path.normpath(filepath)
        normalized_exclude_file = os.path.normpath(exclude_file) if exclude_file else None

        if normalized_exclude_file and normalized_filepath == normalized_exclude_file:
            print(f"Skipping {filepath} as it's the designated Spelman file.")
            continue

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

print("--- Upperclassmen Housing Draw Estimator (v2) ---")

# 1. Load Upperclassmen Data
print(f"\nLoading upperclassmen data from {UPPERCLASS_FILENAME}...")
upperclass_data = load_draw_data(UPPERCLASS_FILENAME)
if not upperclass_data:
    print("Critical Error: Could not load upperclassmen data. Exiting.")
    exit()
print(f"Loaded {len(upperclass_data)} entries from upperclassmen list.")

# 2. Load Available Rooms Data
print(f"\nLoading available rooms data from {AVAILABLE_ROOMS_FILENAME}...")
rooms_data = load_rooms_data(AVAILABLE_ROOMS_FILENAME)
if not rooms_data:
    print("Warning: Could not load available rooms data. Spelman capacity calculation will be skipped.")
    # Allow continuation, but Spelman filtering won't work

# 3. Calculate Spelman Capacity
print("\nCalculating Spelman capacity...")
spelman_capacity = calculate_spelman_capacity(rooms_data)
print(f"Calculated capacity (Y) for Spelman Hall: {spelman_capacity} spots")

# 4. Load Spelman Draw Data
print(f"\nLoading Spelman draw times from {SPELMAN_DRAW_FILENAME}...")
spelman_data = load_draw_data(SPELMAN_DRAW_FILENAME)
if not spelman_data:
    print(f"Warning: Could not load Spelman draw data from {SPELMAN_DRAW_FILENAME}. Spelman-specific filtering will be skipped.")
    # Allow continuation

# 5. Identify Top Spelman Drawers based on Capacity
print("\nIdentifying top Spelman drawers based on capacity...")
top_spelman_puids = get_top_spelman_drawers(spelman_data, spelman_capacity)

# 6. Get User Input
user_first_name = input("\nEnter your First Name: ").strip()
user_last_name = input("Enter your Last Name: ").strip()

# 7. Find User in Upperclassmen List
user_info, user_index = find_user_position(upperclass_data, user_first_name, user_last_name)

if user_index == -1:
    print(f"\nUser '{user_first_name} {user_last_name}' not found in the upperclassmen list ({UPPERCLASS_FILENAME}).")
    exit()

print(f"\nFound user: {user_info['First Name']} {user_info['Last Name']}")
print(f"  Draw Time: {user_info['Draw Time']}")
print(f"  Position in Upperclassmen Draw: {user_index + 1} out of {len(upperclass_data)}")

# 8. Identify People Ahead of the User (Initially)
people_ahead_initial = upperclass_data[:user_index]
initial_count = len(people_ahead_initial)
print(f"\nInitially, there are {initial_count} people scheduled to draw before you in the upperclassmen draw.")

if initial_count == 0:
    print("You have the first draw time! No filtering needed.")
    exit()

# 9. Get OTHER Residential College Early Drawers (Top N)
print(f"\nNow, let's identify students likely to take spots in OTHER Residential Colleges (Top {RES_COLLEGE_TOP_N}).")
early_res_college_puids = get_residential_college_early_drawers(RES_COLLEGE_TOP_N, exclude_file=SPELMAN_DRAW_FILENAME)
print(f"\nIdentified {len(early_res_college_puids)} unique PUIDs from the top {RES_COLLEGE_TOP_N} of provided OTHER residential college lists.")

# 10. Filter the "Ahead" List based on BOTH criteria
people_ahead_filtered = []
removed_res_college_count = 0
removed_spelman_count = 0
puids_already_removed = set() # To avoid double counting if someone is in both sets

print("\nFiltering the list of people ahead of you based on Res College and Spelman draws...")

for person in people_ahead_initial:
    puid = person.get('PUID')
    removed = False
    reason = ""

    if not puid:
        print(f"Warning: Person ahead ({person.get('First Name')} {person.get('Last Name')}) has no PUID. Cannot filter, keeping.")
        people_ahead_filtered.append(person)
        continue

    # Check Spelman criteria first
    if puid in top_spelman_puids:
        if puid not in puids_already_removed:
            removed_spelman_count += 1
            puids_already_removed.add(puid)
        removed = True
        reason = f"likely taking Spelman spot (Top {spelman_capacity})"
        # print(f"  - Removing {person.get('First Name')} {person.get('Last Name')} (PUID: {puid}) - {reason}.") # Uncomment for verbose output

    # Check general res college criteria IF NOT already removed for Spelman
    elif puid in early_res_college_puids:
         if puid not in puids_already_removed:
             removed_res_college_count += 1
             puids_already_removed.add(puid)
         removed = True
         reason = f"likely taking other Res College spot (Top {RES_COLLEGE_TOP_N})"
         # print(f"  - Removing {person.get('First Name')} {person.get('Last Name')} (PUID: {puid}) - {reason}.") # Uncomment for verbose output

    if not removed:
        people_ahead_filtered.append(person)

final_count = len(people_ahead_filtered)
total_removed = removed_spelman_count + removed_res_college_count

# 11. Display Final Results
print("\n--- Final Estimate ---")
print(f"User: {user_info['First Name']} {user_info['Last Name']}")
print(f"Your Upperclassmen Draw Position: {user_index + 1}")
print(f"\nInitial number of people drawing before you: {initial_count}")
print(f"  - Removed because likely taking Spelman spot (Top {spelman_capacity}): {removed_spelman_count}")
print(f"  - Removed because likely taking OTHER Res College spot (Top {RES_COLLEGE_TOP_N}): {removed_res_college_count}")
print(f"Total removed: {total_removed}")
print(f"\nEstimated number of people ACTUALLY drawing for Upperclassmen housing before you: {final_count}")

# Optional: Print the names of those still ahead
# print("\nPeople estimated to draw before you for Upperclassmen Housing:")
# if final_count > 0:
#     for i, person in enumerate(people_ahead_filtered):
#         print(f"  {i+1}. {person.get('First Name')} {person.get('Last Name')} (PUID: {person.get('PUID')}, Time: {person.get('Draw Time')})")
# else:
#      print("  (None)")

print("\nDone.")