from datetime import datetime
from datetime import timedelta






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

def combine_dicts(**kwargs):
    combined_dict = {}
    for dictionary in kwargs.values():
        combined_dict.update(dictionary)
    return combined_dict



# Example usage:
date_to_check = datetime(2023, 3, 17)  # Change the date to the one you want to check
holiday = check_holiday(date_to_check)
if holiday:
    print(f"The date {date_to_check.strftime('%Y-%m-%d')} is {holiday}.")
else:
    print(f"The date {date_to_check.strftime('%Y-%m-%d')} is not a known holiday.")
