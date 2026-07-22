from datetime import datetime, timedelta
from urllib.parse import quote

LOCATIONS = {
    "honor_oak": "09210dea-3498-43d1-8483-29490e230247",
    "belair_park": "e014e2b3-7f87-4fe0-9261-4a2b5ba0fa49",
    "dulwich_park": "aae62282-2de2-4950-ac4a-0ea947476505",
}

AREAS = {
    "dulwich": ["belair_park", "dulwich_park"],
    "honor_oak": ["honor_oak"],
}

PROGRAMME_CATEGORIES = {
    "clinics": "bfc46cba-fed0-47a0-aea1-2f7aa643cb67",
}

class ClubSparkURLGenerator:
    """Generates ClubSpark URLs for 6 weeks from today"""
    
    def __init__(self):
        self.base_url = "https://clubspark.lta.org.uk/VamosTennis/Admin/Coaching/CoachingReports"
    
    def get_courses_url(self) -> str:
        """Generate ClubSpark courses URL for next 6 weeks"""
        today = datetime.now()
        end_date = today + timedelta(weeks=6)
        
        start_str = today.strftime("%Y/%m/%d")
        end_str = end_date.strftime("%Y/%m/%d")
        
        start_encoded = quote(start_str)
        end_encoded = quote(end_str)
        
        return f"{self.base_url}/Coaching_Courses?startdateforfiltering={start_encoded}&enddateforfiltering={end_encoded}&category=&status=Upcoming&leadcoachforfiltering=&venue="
    
    def get_sessions_url(self) -> str:
        """Generate ClubSpark sessions URL for next 6 weeks"""
        today = datetime.now()
        end_date = today + timedelta(weeks=6)
        
        start_str = today.strftime("%Y/%m/%d")
        end_str = end_date.strftime("%Y/%m/%d")
        
        start_encoded = quote(start_str)
        end_encoded = quote(end_str)
        
        return f"{self.base_url}/Coaching_Sessions?startdateforfiltering={start_encoded}&enddateforfiltering={end_encoded}&category=&status=Upcoming&leadcoachforfiltering=&venue="

    def get_programme_category_url(self, category: str) -> str:
        """Generate ClubSpark URL filtered to a specific programme category"""
        programme_id = PROGRAMME_CATEGORIES[category]
        programme_id_encoded = quote(programme_id)

        return f"https://clubspark.lta.org.uk/VamosTennis/Coaching/Adult?programme-id%5B%5D={programme_id_encoded}"