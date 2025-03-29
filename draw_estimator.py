import csv
from datetime import datetime
import os
import json # Import the json library

# --- Configuration ---
# Assuming the python script is in the PARENT directory of 'room-draw-analysis'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REACT_APP_DIR = os.path.join(BASE_DIR, 'room-draw-analysis')
PUBLIC_DIR = os.path.join(REACT_APP_DIR, 'public')
OUTPUT_JSON_PATH = os.path.join(PUBLIC_DIR, 'dashboard-data.json') # Output path

# Input file paths (relative to the script's location)
UPPERCLASS_FILENAME = 'UpperclassTimeOrder2025 (1).csv'
AVAILABLE_ROOMS_FILENAME = 'AvailableRoomsList2025.csv'
SPELMAN_DRAW_FILENAME = 'SpelmanTimeOrder2025.csv'
NCW_DRAW_FILENAME = 'NCWTimeOrder2025 (1).csv' # Add NCW filename explicitly if needed for input prompt example

RES_COLLEGE_TOP_N = 50

# Define capacity mapping for room types globally
ROOM_TYPE_MAP = {
    'SINGLE': 1,
    'DOUBLE': 2,
    'TRIPLE': 3,
    'QUAD': 4,
    'QUINT': 5,
    '6PERSON': 6
    # Add other types if they exist
}

# --- Helper Functions ---

def load_draw_data(filepath):
    """Loads data from a draw time CSV file (Upperclass or Res College)."""
    data = []
    absolute_filepath = os.path.join(BASE_DIR, filepath) # Use absolute path
    if not os.path.exists(absolute_filepath):
        print(f"Error: File not found at {absolute_filepath}")
        return None
    try:
        with open(absolute_filepath, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            required_cols = ['PUID', 'Draw Time', 'Last Name', 'First Name']
            # Use list comprehension for cleaner check
            missing = [col for col in required_cols if col not in (reader.fieldnames or [])]
            if missing:
                print(f"Error: File {filepath} is missing required columns: {missing}. Check CSV header.")
                return None

            for i, row in enumerate(reader):
                try:
                    # Standardize keys (optional but good practice)
                    row = {k.strip(): v.strip() for k, v in row.items()}
                    row['Draw Time Obj'] = datetime.strptime(row['Draw Time'], '%m/%d/%y %I:%M %p')
                    row['Original Row'] = i
                    data.append(row)
                except ValueError as e:
                    print(f"Warning: Could not parse date in row: {row} from {filepath}. Error: {e}. Skipping row.")
                except KeyError as e:
                    print(f"Warning: Missing expected column '{e}' in file {filepath}. Skipping row {row}")
                    continue
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None

    data.sort(key=lambda x: (x.get('Draw Time Obj', datetime.max), x.get('Original Row', float('inf'))))
    return data

def load_rooms_data(filepath):
    """Loads data from the available rooms CSV file."""
    data = []
    absolute_filepath = os.path.join(BASE_DIR, filepath) # Use absolute path
    if not os.path.exists(absolute_filepath):
        print(f"Error: File not found at {absolute_filepath}")
        return None
    try:
        with open(absolute_filepath, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            required_cols = ['College', 'Dorm', 'Room', 'Type']
            missing = [col for col in required_cols if col not in (reader.fieldnames or [])]
            if missing:
                print(f"Error: File {filepath} is missing required columns: {missing}. Check CSV header.")
                return None
            for row in reader:
                 # Standardize keys
                row = {k.strip(): v.strip() for k, v in row.items()}
                data.append(row)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None
    return data

def calculate_room_stats(rooms_data):
    """Calculates total available spots and single spots in Upperclass housing."""
    spelman_capacity = 0
    total_upperclass_singles = 0
    # total_upperclass_spots = 0 # Could calculate this too if needed

    if not rooms_data:
        print("Warning: Cannot calculate room stats because room data failed to load.")
        return 0, 0 # spelman_capacity, total_upperclass_singles

    count_spelman_rooms = 0
    count_upperclass_singles = 0

    for room in rooms_data:
        college = room.get('College', '').lower()
        dorm = room.get('Dorm', '').lower()
        room_type = room.get('Type', '').upper()
        spots = ROOM_TYPE_MAP.get(room_type, 0)

        if college == 'upperclass':
            # Calculate Spelman Capacity
            if dorm == 'spelman':
                count_spelman_rooms += 1
                if spots == 0 and room_type:
                    print(f"Warning: Unknown room type '{room.get('Type')}' for Spelman room {room.get('Room')}. Assuming 0 capacity.")
                spelman_capacity += spots

            # Count Upperclass Singles
            if room_type == 'SINGLE':
                total_upperclass_singles += 1
                count_upperclass_singles += 1
            # Could add total spots calculation here if needed
            # total_upperclass_spots += spots

    print(f"Found {count_spelman_rooms} rooms listed in Upperclass Spelman.")
    print(f"Found {count_upperclass_singles} SINGLE rooms listed in Upperclass housing.")
    return spelman_capacity, total_upperclass_singles


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
            break
    print(f"Identified the top {count} PUIDs from the Spelman draw list based on calculated capacity.")
    return puids

def find_user_position(data, first_name, last_name):
    """Finds the user's dictionary and index in the data list."""
    first_name_lower = first_name.lower()
    last_name_lower = last_name.lower()
    for index, person in enumerate(data):
        if (person.get('First Name', '').lower() == first_name_lower and
            person.get('Last Name', '').lower() == last_name_lower):
            return person, index
    return None, -1

def get_residential_college_early_drawers(top_n, exclude_file=None):
    """Gets PUIDs of top N drawers from multiple residential college files, excluding one."""
    early_drawer_puids = set()
    print(f"\nEnter paths to OTHER Residential College CSV files (e.g., {NCW_DRAW_FILENAME}).")
    print(f"(Will automatically exclude {exclude_file} if entered)")
    print("Press Enter without typing a path when you are done adding files.")

    absolute_exclude_path = os.path.normpath(os.path.join(BASE_DIR, exclude_file)) if exclude_file else None

    while True:
        filepath_input = input("Path to OTHER Residential College CSV (or press Enter to finish): ").strip()
        if not filepath_input:
            break

        absolute_filepath = os.path.normpath(os.path.join(BASE_DIR, filepath_input))

        if absolute_exclude_path and absolute_filepath == absolute_exclude_path:
            print(f"Skipping {filepath_input} as it's the designated Spelman file.")
            continue

        print(f"Processing {filepath_input}...")
        college_data = load_draw_data(filepath_input) # Pass relative path

        if college_data:
            count = 0
            for person in college_data:
                if count < top_n:
                    puid = person.get('PUID')
                    if puid:
                        early_drawer_puids.add(puid)
                        count += 1
                    else:
                         print(f"Warning: Row in {filepath_input} missing PUID: {person}. Skipping for early drawer check.")
                else:
                    break
            print(f"Added PUIDs for the top {count} drawers from {filepath_input}.")
        else:
            print(f"Skipping file {filepath_input} due to loading errors.")

    return early_drawer_puids

def calculate_probability(available, position):
    """Calculates the probability (0-100) of getting a spot."""
    if position <= 0: return 100 # If effective position is 0 or less, 100% chance
    if available <= 0: return 0   # If no spots available, 0% chance
    if available >= position: return 100 # More spots than people ahead
    # Linear probability estimate
    return max(0, round((available / position) * 100))


# --- Main Program Logic ---

print("--- Upperclassmen Housing Draw Estimator & Dashboard Updater ---")

# 1. Load Data
print(f"\nLoading upperclassmen data from {UPPERCLASS_FILENAME}...")
upperclass_data = load_draw_data(UPPERCLASS_FILENAME)
if not upperclass_data: exit("Critical Error: Could not load upperclassmen data.")

print(f"\nLoading available rooms data from {AVAILABLE_ROOMS_FILENAME}...")
rooms_data = load_rooms_data(AVAILABLE_ROOMS_FILENAME)
# Don't exit if rooms fail, just disable features

print(f"\nLoading Spelman draw times from {SPELMAN_DRAW_FILENAME}...")
spelman_data = load_draw_data(SPELMAN_DRAW_FILENAME)
# Don't exit if Spelman fails, just disable features

print("\nCalculating Room Stats...")
spelman_capacity, available_singles = calculate_room_stats(rooms_data)
print(f"Calculated Spelman Capacity (Y): {spelman_capacity}")
print(f"Calculated Available Upperclass Singles: {available_singles}")


print("\nIdentifying top Spelman drawers...")
top_spelman_puids = get_top_spelman_drawers(spelman_data, spelman_capacity)

# 2. Get User Input
user_first_name = input("\nEnter your First Name: ").strip()
user_last_name = input("Enter your Last Name: ").strip()

# 3. Find User
user_info, user_index = find_user_position(upperclass_data, user_first_name, user_last_name)

if user_index == -1:
    exit(f"\nUser '{user_first_name} {user_last_name}' not found in {UPPERCLASS_FILENAME}.")

# Extract user details safely
user_puid = user_info.get('PUID', 'N/A')
user_draw_time_str = user_info.get('Draw Time', 'N/A')
user_full_name = f"{user_info.get('First Name', '')} {user_info.get('Last Name', '')}".strip()

print(f"\nFound user: {user_full_name}")
print(f"  Draw Time: {user_draw_time_str}")
print(f"  Position in Upperclassmen Draw: {user_index + 1} out of {len(upperclass_data)}")

# 4. Initial Analysis
people_ahead_initial = upperclass_data[:user_index]
initial_count = len(people_ahead_initial)
print(f"\nInitially, there are {initial_count} people scheduled to draw before you.")

if initial_count == 0:
    print("You have the first draw time!")
    # Still generate JSON for consistency
    final_count = 0
    removed_spelman_count = 0
    removed_res_college_count = 0
    total_removed = 0
else:
    # 5. Get Other Res College Drawers
    print(f"\nIdentifying students likely to take spots in OTHER Residential Colleges (Top {RES_COLLEGE_TOP_N}).")
    early_res_college_puids = get_residential_college_early_drawers(RES_COLLEGE_TOP_N, exclude_file=SPELMAN_DRAW_FILENAME)
    print(f"\nIdentified {len(early_res_college_puids)} unique PUIDs from the top {RES_COLLEGE_TOP_N} of other colleges.")

    # 6. Filter List
    people_ahead_filtered = []
    removed_res_college_count = 0
    removed_spelman_count = 0
    puids_already_removed = set()

    print("\nFiltering the list of people ahead of you...")

    for person in people_ahead_initial:
        puid = person.get('PUID')
        removed = False

        if not puid:
            print(f"Warning: Person ahead ({person.get('First Name')} {person.get('Last Name')}) has no PUID. Keeping.")
            people_ahead_filtered.append(person)
            continue

        if puid in top_spelman_puids:
            if puid not in puids_already_removed:
                removed_spelman_count += 1
                puids_already_removed.add(puid)
            removed = True
        elif puid in early_res_college_puids:
             if puid not in puids_already_removed:
                 removed_res_college_count += 1
                 puids_already_removed.add(puid)
             removed = True

        if not removed:
            people_ahead_filtered.append(person)

    final_count = len(people_ahead_filtered)
    total_removed = removed_spelman_count + removed_res_college_count

# 7. Calculate Final Stats & Probability
print("\n--- Final Estimate ---")
print(f"Initial number ahead: {initial_count}")
print(f"  - Removed (Spelman Top {spelman_capacity}): {removed_spelman_count}")
print(f"  - Removed (Other Res College Top {RES_COLLEGE_TOP_N}): {removed_res_college_count}")
print(f"Total removed: {total_removed}")
print(f"Estimated number ACTUALLY drawing before you: {final_count}")

probability_single = calculate_probability(available_singles, final_count)
print(f"\nAvailable Upperclass Singles: {available_singles}")
print(f"Estimated Probability of getting a Single: {probability_single}%")

# 8. Prepare Data for JSON Output
output_data = {
    "userName": user_full_name,
    "puid": user_puid,
    "drawTime": user_draw_time_str,
    "rawPosition": user_index + 1,
    "initialAhead": initial_count,
    "removedSpelman": removed_spelman_count,
    "spelmanCapacity": spelman_capacity,
    "removedOtherRes": removed_res_college_count,
    "otherResTopN": RES_COLLEGE_TOP_N,
    "totalRemoved": total_removed,
    "finalPositionEstimate": final_count, # This is the number of competitors ahead
    "availableSingles": available_singles,
    "probabilitySingle": probability_single,
    "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Add timestamp
}

# 9. Write JSON file
try:
    # Ensure the public directory exists
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(OUTPUT_JSON_PATH, 'w') as outfile:
        json.dump(output_data, outfile, indent=2) # Use indent for readability
    print(f"\nSuccessfully updated dashboard data at: {OUTPUT_JSON_PATH}")
except Exception as e:
    print(f"\nError writing dashboard data file: {e}")

print("\nPython script finished.")