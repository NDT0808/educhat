import re
from typing import List
from unidecode import unidecode

class IntentService:
    def extract_constraints(self, text: str) -> List[str]:
        constraints = []
        # Normalize: convert to lowercase and remove accents
        text_normalized = unidecode(text.lower())
        
        # Day extraction
        # Map unaccented phrases to constraints
        day_map = {
            "thu 2": "no_monday", "thu hai": "no_monday",
            "thu 3": "no_tuesday", "thu ba": "no_tuesday",
            "thu 4": "no_wednesday", "thu tu": "no_wednesday",
            "thu 5": "no_thursday", "thu nam": "no_thursday",
            "thu 6": "no_friday", "thu sau": "no_friday",
            "thu 7": "no_saturday", "thu bay": "no_saturday",
            "chu nhat": "no_sunday", "cn": "no_sunday"
        }
        
        # Check for negative day constraints
        # "khong", "tranh" are unaccented versions of "không", "tránh"
        negation_keywords = ["khong", "tranh", "no", "without"]
        
        for key, value in day_map.items():
            # Check pattern: negation + day
            # Simple check: if negation keyword and day keyword are in text
            if key in text_normalized:
                # Check for negation in proximity or just generic presence for now
                if any(neg in text_normalized for neg in negation_keywords):
                    constraints.append(value)

        # Time extraction
        if "sang" in text_normalized and any(neg in text_normalized for neg in negation_keywords):
             # "khong sang" -> afternoon_only
            constraints.append("afternoon_only")
        elif "chieu" in text_normalized and any(neg in text_normalized for neg in negation_keywords):
            # "khong chieu" -> morning_only
            constraints.append("morning_only")
        elif "chi sang" in text_normalized or "buoi sang" in text_normalized or "morning" in text_normalized:
             # "chi sang" -> morning_only
            constraints.append("morning_only")
        elif "chi chieu" in text_normalized or "buoi chieu" in text_normalized or "afternoon" in text_normalized:
             # "chi chieu" -> afternoon_only
            constraints.append("afternoon_only")
            
        # Optimization goals
        if "it ngay" in text_normalized or "gom" in text_normalized or "toi thieu" in text_normalized:
            constraints.append("minimize_days")
            
        return list(set(constraints))
