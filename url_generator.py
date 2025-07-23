from datetime import datetime, timedelta
from urllib.parse import quote

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