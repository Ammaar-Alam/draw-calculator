import csv
from datetime import datetime
import os
import json
import glob # Keep glob for finding required files

# --- Configuration ---
# Assuming the python script is in the PARENT directory of 'room-draw-analysis'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REACT_APP_DIR = os.path.join(BASE_DIR, 'room-draw-analysis')
PUBLIC_DIR = os.path.join(REACT_APP_DIR, 'public')
OUTPUT_JSON_PATH = os.path.join(PUBLIC_DIR, 'dashboard-data.json') # Output path

# Required file patterns (for finding the main files)
REQUIRED_FILES = {
    'upperclass': 'UpperclassTimeOrder*.csv',
    'rooms': 'AvailableRoomsList*.csv',
    'spelman': 'SpelmanTimeOrder*.csv'
}
# Example of another potential Res College file pattern (used in prompt)
NCW_PATTERN_EXAMPLE = 'NCW*.csv'


RES_COLLEGE_TOP_N = 50

# Define capacity mapping for room types globally
ROOM_TYPE_MAP = {
    'SINGLE': 1,
    'DOUBLE': 2,
    'TRIPLE': 3,
    'QUAD': 4,
    'QUINT': 5,
    '6PERSON': 6
}

def find_csv_file(pattern):
    """Find the first CSV file matching the given pattern in BASE_DIR."""
    # Search relative to the script's directory (BASE_DIR)
    search_pattern = os.path.join(BASE_DIR, pattern)
    files = glob.glob(search_pattern)
    if not files:
        print(f"Error: No file found matching pattern: {pattern} in {BASE_DIR}")
        return None
    # Return only the basename for consistency, load_data will prepend BASE_DIR
    relative_path = os.path.relpath(files[0], BASE_DIR)
    if len(files) > 1:
        print(f"Warning: Multiple files found matching pattern '{pattern}'. Using: {relative_path}")
    return relative_path # Return relative path

# --- Helper Functions (load_draw_data, load_rooms_data, etc. remain mostly the same) ---
def load_draw_data(filepath_relative):
    """Loads data from a draw time CSV file (Upperclass or Res College).
       Expects filepath_relative to be relative to BASE_DIR.
    """
    data = []
    absolute_filepath = os.path.join(BASE_DIR, filepath_relative)
    if not os.path.exists(absolute_filepath):
        print(f"Error: File not found at {absolute_filepath}")
        return None
    try:
        with open(absolute_filepath, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            required_cols = ['PUID', 'Draw Time', 'Last Name', 'First Name']
            missing = [col for col in required_cols if col not in (reader.fieldnames or [])]
            if missing:
                print(f"Error: File {filepath_relative} is missing required columns: {missing}. Check CSV header.")
                return None

            for i, row in enumerate(reader):
                try:
                    row = {k.strip(): v.strip() for k, v in row.items()}
                    row['Draw Time Obj'] = datetime.strptime(row['Draw Time'], '%m/%d/%y %I:%M %p')
                    row['Original Row'] = i
                    data.append(row)
                except ValueError as e:
                    print(f"Warning: Could not parse date in row: {row} from {filepath_relative}. Error: {e}. Skipping row.")
                except KeyError as e:
                    print(f"Warning: Missing expected column '{e}' in file {filepath_relative}. Skipping row {row}")
                    continue
    except Exception as e:
        print(f"Error reading file {filepath_relative}: {e}")
        return None

    data.sort(key=lambda x: (x.get('Draw Time Obj', datetime.max), x.get('Original Row', float('inf'))))
    return data

def load_rooms_data(filepath_relative):
    """Loads data from the available rooms CSV file.
       Expects filepath_relative to be relative to BASE_DIR.
    """
    data = []
    absolute_filepath = os.path.join(BASE_DIR, filepath_relative)
    if not os.path.exists(absolute_filepath):
        print(f"Error: File not found at {absolute_filepath}")
        return None
    try:
        with open(absolute_filepath, mode='r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            required_cols = ['College', 'Dorm', 'Room', 'Type']
            missing = [col for col in required_cols if col not in (reader.fieldnames or [])]
            if missing:
                print(f"Error: File {filepath_relative} is missing required columns: {missing}. Check CSV header.")
                return None
            for row in reader:
                row = {k.strip(): v.strip() for k, v in row.items()}
                data.append(row)
    except Exception as e:
        print(f"Error reading file {filepath_relative}: {e}")
        return None
    return data

def calculate_room_stats(rooms_data):
    """Calculates total available spots and single spots in Upperclass housing."""
    spelman_capacity = 0
    total_upperclass_singles = 0
    if not rooms_data:
        print("Warning: Cannot calculate room stats because room data failed to load.")
        return 0, 0

    count_spelman_rooms = 0
    count_upperclass_singles = 0

    for room in rooms_data:
        college = room.get('College', '').lower()
        dorm = room.get('Dorm', '').lower()
        room_type = room.get('Type', '').upper()
        spots = ROOM_TYPE_MAP.get(room_type, 0)

        if college == 'upperclass':
            if dorm == 'spelman':
                count_spelman_rooms += 1
                if spots == 0 and room_type:
                    print(f"Warning: Unknown room type '{room.get('Type')}' for Spelman room {room.get('Room')}. Assuming 0 capacity.")
                spelman_capacity += spots
            if room_type == 'SINGLE':
                total_upperclass_singles += 1
                count_upperclass_singles += 1

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

# *** REVERTED THIS FUNCTION TO MANUAL INPUT ***
def get_residential_college_early_drawers(top_n, exclude_file=None):
    """Gets PUIDs of top N drawers from multiple residential college files, excluding one."""
    early_drawer_puids = set()
    ncw_example_file = find_csv_file(NCW_PATTERN_EXAMPLE) or "NCWTimeOrder....csv"

    print(f"\nEnter relative paths (from script location) to OTHER Residential College CSV files (e.g., {ncw_example_file}).")
    if exclude_file:
        print(f"(Excluding {exclude_file})")
    print("Press Enter without typing a path when you are done adding files.")

    while True:
        filepath_relative = input("Path to OTHER Residential College CSV (or press Enter to finish): ").strip()
        if not filepath_relative:
            break

        # Normalize paths for comparison (optional but good practice)
        normalized_filepath = os.path.normpath(filepath_relative)
        normalized_exclude_file = os.path.normpath(exclude_file) if exclude_file else None

        if normalized_exclude_file and normalized_filepath == normalized_exclude_file:
            print(f"Skipping {filepath_relative} as it's the designated Spelman file.")
            continue

        print(f"Processing {filepath_relative}...")
        # Pass the relative path directly to load_draw_data
        college_data = load_draw_data(filepath_relative)

        if college_data:
            count = 0
            for person in college_data:
                if count < top_n:
                    puid = person.get('PUID')
                    if puid:
                        early_drawer_puids.add(puid)
                        count += 1
                    else:
                         print(f"Warning: Row in {filepath_relative} missing PUID: {person}. Skipping for early drawer check.")
                else:
                    break # Stop after processing top_n
            print(f"Added PUIDs for the top {count} drawers from {filepath_relative}.")
        else:
            print(f"Skipping file {filepath_relative} due to loading errors.")

    return early_drawer_puids
# *** END OF REVERTED FUNCTION ***

def calculate_probability(available, position):
    """Calculates the probability (0-100) of getting a spot."""
    # Position here is the number of people *ahead* of the user
    rank_among_competitors = position + 1
    if position < 0 : # Should not happen, but safety check
        return 100
    if available <= 0: return 0
    # If the number of available singles is >= the user's rank among competitors, it's 100%
    if available >= rank_among_competitors: return 100
    # If the user is literally the next person after available spots run out
    if available == position: return 0 # Technically very low, but round to 0 for simplicity
    # Simple linear probability based on rank vs available spots
    # Example: 10 spots, rank 11 (position 10) -> ~0%
    # Example: 10 spots, rank 20 (position 19) -> ~50% (10/20)? Or 10/19? Let's stick to position
    # If position (ahead) >= available, prob is roughly available / (position + 1) ??
    # Let's use the previous logic: available / position (ahead) -> this feels more intuitive
    # If 10 spots, 10 people ahead (rank 11), prob = 10/10 = 100? No.
    # If 10 spots, 11 people ahead (rank 12), prob = 10/11 = ~91%? Seems too high.
    # Let's rethink: Probability is the chance your rank (position+1) is <= available spots.
    # If spots >= rank -> 100%.
    # If spots < rank: maybe estimate as spots / rank?
    # Example: 10 spots, rank 11 -> 10/11 = 91%
    # Example: 10 spots, rank 20 -> 10/20 = 50%
    # Example: 10 spots, rank 100 -> 10/100 = 10%
    # This seems more reasonable than using 'position' (people ahead) in the denominator.
    probability = (available / rank_among_competitors) * 100
    return max(0, round(probability))


# --- Main Program Logic ---
# (Keep the rest of the main logic the same as the previous version,
#  including finding required files, loading data, getting user input,
#  finding user, initial analysis, calling the *reverted*
#  get_residential_college_early_drawers, filtering, calculating final stats,
#  preparing JSON, and writing JSON)

# ... [Rest of the main logic from the previous correct answer] ...

# --- Main Program Logic ---

print("--- Upperclassmen Housing Draw Estimator & Dashboard Updater ---")

# 1. Find required files
print("\nSearching for required CSV files...")
upperclass_file = find_csv_file(REQUIRED_FILES['upperclass'])
rooms_file = find_csv_file(REQUIRED_FILES['rooms'])
spelman_file = find_csv_file(REQUIRED_FILES['spelman'])

if not all([upperclass_file, rooms_file, spelman_file]):
    print("\nError: Could not find all required files. Please ensure the following patterns match files in the script directory:")
    for key, pattern in REQUIRED_FILES.items():
        print(f"- {pattern}")
    exit(1)

print("\nFound all required files:")
print(f"- Upperclass: {upperclass_file}")
print(f"- Rooms: {rooms_file}")
print(f"- Spelman: {spelman_file}")

# 2. Load Data
print(f"\nLoading upperclassmen data from {upperclass_file}...")
upperclass_data = load_draw_data(upperclass_file)
if not upperclass_data: exit("Critical Error: Could not load upperclassmen data.")

print(f"\nLoading available rooms data from {rooms_file}...")
rooms_data = load_rooms_data(rooms_file)
# Don't exit if rooms fail, just disable features

print(f"\nLoading Spelman draw times from {spelman_file}...")
spelman_data = load_draw_data(spelman_file)
# Don't exit if Spelman fails, just disable features

print("\nCalculating Room Stats...")
spelman_capacity, available_singles = calculate_room_stats(rooms_data)
print(f"Calculated Spelman Capacity (Y): {spelman_capacity}")
print(f"Calculated Available Upperclass Singles: {available_singles}")


print("\nIdentifying top Spelman drawers...")
top_spelman_puids = get_top_spelman_drawers(spelman_data, spelman_capacity)

# 3. Get User Input
user_first_name = input("\nEnter your First Name: ").strip()
user_last_name = input("Enter your Last Name: ").strip()

# 4. Find User
user_info, user_index = find_user_position(upperclass_data, user_first_name, user_last_name)

if user_index == -1:
    exit(f"\nUser '{user_first_name} {user_last_name}' not found in {upperclass_file}.")

# Extract user details safely
user_puid = user_info.get('PUID', 'N/A')
user_draw_time_str = user_info.get('Draw Time', 'N/A')
user_full_name = f"{user_info.get('First Name', '')} {user_info.get('Last Name', '')}".strip()

print(f"\nFound user: {user_full_name}")
print(f"  Draw Time: {user_draw_time_str}")
print(f"  Position in Upperclassmen Draw: {user_index + 1} out of {len(upperclass_data)}")

# 5. Initial Analysis
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
    # 6. Get Other Res College Drawers (Using Manual Input Again)
    print(f"\nIdentifying students likely to take spots in OTHER Residential Colleges (Top {RES_COLLEGE_TOP_N}).")
    early_res_college_puids = get_residential_college_early_drawers(RES_COLLEGE_TOP_N, exclude_file=spelman_file)
    print(f"\nIdentified {len(early_res_college_puids)} unique PUIDs from the top {RES_COLLEGE_TOP_N} of other colleges entered.")

    # 7. Filter List
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

        # Check Spelman first (more specific filter)
        if puid in top_spelman_puids:
            if puid not in puids_already_removed:
                removed_spelman_count += 1
                puids_already_removed.add(puid)
            removed = True
        # Only check other res colleges if not removed for Spelman
        elif puid in early_res_college_puids:
             if puid not in puids_already_removed:
                 removed_res_college_count += 1
                 puids_already_removed.add(puid)
             removed = True

        if not removed:
            people_ahead_filtered.append(person)

    final_count = len(people_ahead_filtered) # This is people *ahead*
    total_removed = removed_spelman_count + removed_res_college_count

# 8. Calculate Final Stats & Probability
print("\n--- Final Estimate ---")
print(f"Initial number ahead: {initial_count}")
print(f"  - Removed (Spelman Top {spelman_capacity}): {removed_spelman_count}")
print(f"  - Removed (Other Res College Top {RES_COLLEGE_TOP_N}): {removed_res_college_count}")
print(f"Total removed: {total_removed}")
print(f"Estimated number ACTUALLY drawing before you: {final_count}")

# Probability calculation uses the *rank* among competitors (people ahead + 1)
user_rank_among_competitors = final_count + 1
probability_single = calculate_probability(available_singles, user_rank_among_competitors) # Pass rank here

print(f"\nAvailable Upperclass Singles: {available_singles}")
print(f"Your Estimated Rank for a Single: {user_rank_among_competitors}")
print(f"Estimated Probability of getting a Single: {probability_single}%")

# 9. Prepare Data for JSON Output
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
    "finalPositionEstimate": final_count, # Number of competitors ahead
    "userRankAmongCompetitors": user_rank_among_competitors, # Explicitly add rank
    "availableSingles": available_singles,
    "probabilitySingle": probability_single,
    "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Add timestamp
}

# 10. Write JSON file
try:
    # Ensure the public directory exists
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(OUTPUT_JSON_PATH, 'w') as outfile:
        json.dump(output_data, outfile, indent=2) # Use indent for readability
    print(f"\nSuccessfully updated dashboard data at: {OUTPUT_JSON_PATH}")
except Exception as e:
    print(f"\nError writing dashboard data file: {e}")

print("\nPython script finished.")