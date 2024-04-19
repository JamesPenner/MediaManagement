from datetime import timedelta, datetime
from dateutil import parser


import csv
import sys
sys.path.append(r'C:\Media Management\Scripts')
# from config import people_lookup


default_date_format = "%Y-%m-%d %H:%M:%S"


def parse_date_string(date_str):
    try:
        # Attempt to parse the date string using dateutil.parser
        parsed_date = parser.parse(date_str)
        return parsed_date.strftime(default_date_format)  # Convert to 'YYYY-MM-DD' format
    except ValueError:
        # Handle the case where the date string is not in a recognized format
        print(f"Warning: Invalid date format: {date_str}")
        return None



def date_difference(start_time, end_time, unit):
    """
    Calculate the difference between two date/time objects and return the result in the specified unit.

    Args:
    - start_time (datetime object or str): The starting date/time. If provided as a string,
      it should be in ISO format ('YYYY-MM-DDTHH:MM:SS').
    - end_time (datetime object or str): The ending date/time. If provided as a string,
      it should be in ISO format ('YYYY-MM-DDTHH:MM:SS').
    - unit (str): The unit of measurement for the result. Supported units: 'seconds', 'minutes',
      'hours', 'days', 'weeks', 'months', 'years'.

    Returns:
    - float or None: The difference between the two date/time objects in the specified unit.
      If the unit provided is invalid or unsupported, it returns None.

    Notes:
    - The function checks if the provided inputs are strings and converts them to datetime objects if needed.
    - The 'months' unit calculates the difference in months based on the calendar months, 
      considering the year differences as well.
    - If the unit provided is not one of the supported units, the function returns None.
    """


    # Check if the inputs are strings and convert them to datetime objects if needed
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time)
    
    # Calculate the time difference between the provided dates
    time_delta = end_time - start_time
    
    # Define conversion factors for different units
    conversion_factors = {
        'seconds': time_delta.total_seconds(),
        'minutes': time_delta.total_seconds() / 60,
        'hours': time_delta.total_seconds() / 3600,
        'days': time_delta.days,
        'weeks': time_delta.days / 7,
        'months': (end_time.year - start_time.year) * 12 + end_time.month - start_time.month,
        'years': end_time.year - start_time.year
    }
    
    # Return the difference based on the specified unit
    return conversion_factors.get(unit.lower(), None)

# Function to calculate Easter (Gauss's algorithm)
def calculate_easter(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day)

# Function to calculate Good Friday (two days before Easter)
def calculate_good_friday(year):
    easter_date = calculate_easter(year)
    return easter_date - timedelta(days=2)

def calculate_mothers_day(year):
    # Finding the second Sunday of May
    first_may = datetime(year, 5, 1)
    first_sunday = first_may + timedelta(days=(6 - first_may.weekday()))  # first Sunday
    second_sunday = first_sunday + timedelta(weeks=1)  # second Sunday
    return second_sunday

def calculate_fathers_day(year):
    # Finding the second Sunday of June
    first_june = datetime(year, 6, 1)
    first_sunday = first_june + timedelta(days=(6 - first_june.weekday()))  # first Sunday
    second_sunday = first_sunday + timedelta(weeks=1)  # second Sunday
    return second_sunday

def calculate_bc_day(year):
    # Finding the first Monday of August
    first_august = datetime(year, 8, 1)
    first_monday = first_august + timedelta(days=(0 - first_august.weekday() + 7) % 7)
    return first_monday

def calculate_canadian_thanksgiving(year):
    # Finding the second Monday of October
    first_october = datetime(year, 10, 1)
    first_monday = first_october + timedelta(days=(0 - first_october.weekday() + 7) % 7)
    second_monday = first_monday + timedelta(weeks=1)
    return second_monday

def calculate_labour_day(year):
    # Finding the first Monday of September
    first_september = datetime(year, 9, 1)
    first_monday = first_september + timedelta(days=(0 - first_september.weekday() + 7) % 7)
    return first_monday

def calculate_victoria_day(year):
    # Finding the last Monday before May 25
    may_25 = datetime(year, 5, 25)
    last_monday = may_25 - timedelta(days=((may_25.weekday() + 1) % 7) + 1)
    return last_monday

def calculate_truth_and_reconciliation_day(year):
    if year >= 2013:
        return datetime(year, 9, 30)
    else:
        return None  # Returning None for years before 2013

def calculate_family_day_bc(year):
    # Finding the second Monday of February
    first_february = datetime(year, 2, 1)
    first_monday = first_february + timedelta(days=(0 - first_february.weekday() + 7) % 7)
    second_monday = first_monday + timedelta(weeks=1)
    return second_monday

def calculate_family_day_bc(year):
    if year >= 2013:
        # Finding the second Monday of February
        first_february = datetime(year, 2, 1)
        first_monday = first_february + timedelta(days=(0 - first_february.weekday() + 7) % 7)
        second_monday = first_monday + timedelta(weeks=1)
        return second_monday
    else:
        return None  # Returning None for years before 2013
    
    # ##########################################################################################
    # Date Sub Functions #######################################################################
    # ##########################################################################################

def check_holiday(date):
    # print(f"check_holiday Date: {date}")

    holidays = {
        "Remembrance Day": (11, 11),
        "Christmas Day": (12, 25),
        "Easter": None,
        "Canada Day": (7, 1),
        "Boxing Day": (12, 26),
        "St. Patrick's Day": (3, 17),
        "Good Friday": None,
        "BC Day": None,
        "Christmas": (12, 25),
        "New Year's Eve": (12, 31),
        "Mother's Day": None,
        "Father's Day": None,
        "Halloween": (10, 31),
        "Thanksgiving": None,
        "Labour Day": None,
        "Valentine's Day": (2, 14),
        "Victoria Day": None,
        "Indigenous Peoples Day": None,
        "Flag of Canada Day": None,
        "Truth and Reconciliation Day": None,
        "Family Day BC": None
    }
    
    for holiday, holiday_date in holidays.items():
        if holiday_date is not None:
            # print(holiday_date)
            if date.month == holiday_date[0] and date.day == holiday_date[1]:
                return holiday
    
    # For holidays needing special calculations
    if date == calculate_easter(date.year):
        return "Easter"
    if date == calculate_good_friday(date.year):
        return "Good Friday"
    if date == calculate_mothers_day(date.year):
        return "Mother's Day"
    if date == calculate_fathers_day(date.year):
        return "Father's Day"
    if date == calculate_bc_day(date.year):
        return "BC Day"
    if date == calculate_canadian_thanksgiving(date.year):
        return "Thanksgiving"
    if date == calculate_labour_day(date.year):
        return "Labour Day"
    if date == calculate_victoria_day(date.year):
        return "Victoria Day"
    truth_day = calculate_truth_and_reconciliation_day(date.year)
    if truth_day and date == truth_day:
        return "Truth and Reconciliation Day"
    family_day_bc = calculate_family_day_bc(date.year)
    if family_day_bc and date == family_day_bc:
        return "Family Day BC"
    return None

def process_metadata_and_people_lookup(create_date, people_list, people_lookup_path):

    # print(f"Create Date is: {create_date}")
    if create_date is None:
        # Handle the case where create_date is None
        return {}

    # If only 1 person is in the image, it's returned as a string. This turns it into a single-item list 
    if isinstance(people_list, str):
        people_list = [people_list]
    # print(people_list)

    # Convert create_date to 'YYYY-MM-DD' string format
    if isinstance(create_date, str):
        create_date = datetime.strptime(create_date, default_date_format)
    create_date_str = create_date.strftime(default_date_format)

    # Convert all names in people_list to lowercase for case-insensitive comparison
    people_list_lower = [''.join(person.split()).lower() for person in people_list]
    # print(people_list_lower)

    # Load people lookup data from the CSV file
    people_data = {}
    with open(people_lookup_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Metadata Name']
            people_data[''.join(name.split()).lower()] = {
                'Date - Birth': row['Date - Birth'],
                'Date - Marriage': row['Date - Marriage'],
                'Date - Death': row['Date - Death'],
                'Spouse Name': row['Spouse Name']
            }


    # Process people list
    results = {}
    for person in people_list:
        person_lower = ''.join(person.split()).lower()
        person_data = people_data.get(person_lower, None)
        if person_data:
            person_data["Person"] = person
            birth_date_str = person_data['Date - Birth']
            marriage_date_str = person_data['Date - Marriage']
            spouse_name = person_data['Spouse Name']

            # print(f"Processing person: {person}")
            # print(f"birth_date_str: {birth_date_str}")

            # Check for exact matches without considering time
            if birth_date_str and create_date_str == parse_date_string(birth_date_str):
                results["XMP:BirthName"] = person
            else:
                parsed_birth_date_str = parse_date_string(birth_date_str)
                if parsed_birth_date_str and create_date_str == parsed_birth_date_str:
                    results["XMP:BirthdayName"] = person

            # Check for marriage match
            if marriage_date_str and create_date_str == marriage_date_str and spouse_name:
                if spouse_name:
                    marriage_string = f"{create_date} {person} and {spouse_name}"
                    results["XMP:Wedding"] = marriage_string

    return results