import re
from datetime import datetime, timedelta

def parse_time(time_str):
    """
    Parses a time string (e.g., '10:50:49 AM') into a datetime object for today.
    """
    try:
        # Clean the string
        time_str = time_str.strip()
        
        # Parse format: HH:MM:SS AM/PM
        # Note: Keka seems to use 12-hour format with AM/PM
        time_obj = datetime.strptime(time_str, "%I:%M:%S %p")
        
        # Combine with today's date
        now = datetime.now()
        return now.replace(hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second, microsecond=0)
    except ValueError:
        try:
             # Try without seconds: HH:MM AM/PM
            time_obj = datetime.strptime(time_str, "%I:%M %p")
            now = datetime.now()
            return now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
        except ValueError:
            return None

def calculate_remaining_time(clock_in_time, work_hours=9):
    """
    Calculates the remaining time until clock out.
    """
    if not clock_in_time:
        return None
        
    clock_out_time = clock_in_time + timedelta(hours=work_hours)
    now = datetime.now()
    remaining = clock_out_time - now
    
    # If remaining is negative, it means overtime
    return remaining

def find_clock_in_time_in_text(text):
    """
    Searches for a time pattern in the text associated with 'Clock In'.
    Returns the first match as a datetime object.
    """
    # Regex for HH:MM:SS AM/PM or HH:MM AM/PM
    # We look for patterns that might be near "Clock In"
    # But for now, let's just find all times and assume the earliest one is clock-in? 
    # No, that's risky.
    
    # Let's look for specific lines in the text dump.
    # "Remote Clock In 10:50:49 AM"
    # "Web Clock In 09:30:00 AM"
    
    # Regex to capture time after "Clock In"
    # Matches: "Clock In" followed by optional characters then a time.
    pattern = r"(?:Web|Remote|Mobile)?\s*Clock\s*In.*(\d{1,2}:\d{2}(?::\d{2})?\s*[AP]M)"
    
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    if matches:
        # Return the first valid time found
        for match in matches:
            parsed = parse_time(match)
            if parsed:
                return parsed
                
    return None
