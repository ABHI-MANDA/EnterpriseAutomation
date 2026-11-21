"""Enterprise Real Estate Data Cleaning, Standardization, and Validation Engine.
Specialized for 800,000+ Indian real estate lead records.
Handles:
- City and Locality alias normalization (e.g. Bangalore/B'lore -> Bengaluru, White Field -> Whitefield)
- Property Type standardization (e.g. 2BHK/Flat -> Apartment - 2 BHK)
- Indian Mobile (+91) format validation and cleaning
- Email RFC-compliant structure validation and domain normalization
- Budget price range validation (min_price <= max_price)
- Detailed Data Quality Reporting and unmatched value aggregation
"""
import re
from typing import Dict, Any, Tuple, List, Optional

# --- Master Standardization Dictionaries ---

CITY_ALIASES: Dict[str, str] = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "banglore": "Bengaluru",
    "b'lore": "Bengaluru",
    "blr": "Bengaluru",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "delhi": "Delhi NCR",
    "new delhi": "Delhi NCR",
    "ncr": "Delhi NCR",
    "gurgaon": "Delhi NCR",
    "gurugram": "Delhi NCR",
    "noida": "Delhi NCR",
    "greater noida": "Delhi NCR",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "hyderabad": "Hyderabad",
    "secunderabad": "Hyderabad",
    "chennai": "Chennai",
    "madras": "Chennai",
    "pune": "Pune",
    "ahmedabad": "Ahmedabad"
}

LOCALITY_ALIASES: Dict[str, str] = {
    "whitefield": "Whitefield",
    "white field": "Whitefield",
    "white-field": "Whitefield",
    "indiranagar": "Indiranagar",
    "indirangar": "Indiranagar",
    "indira nagar": "Indiranagar",
    "hsr": "HSR Layout",
    "hsr layout": "HSR Layout",
    "h.s.r layout": "HSR Layout",
    "koramangala": "Koramangala",
    "kora": "Koramangala",
    "electronic city": "Electronic City",
    "e-city": "Electronic City",
    "marathahalli": "Marathahalli",
    "bellandur": "Bellandur",
    "cyber city": "Cyber City",
    "golf course road": "Golf Course Road",
    "bandra": "Bandra West",
    "bandra west": "Bandra West",
    "bandra (w)": "Bandra West",
    "powai": "Powai",
    "worli": "Worli",
    "andheri": "Andheri West",
    "salt lake": "Salt Lake Sector V",
    "new town": "New Town",
    "gachibowli": "Gachibowli",
    "hitec city": "HITEC City",
    "jubilee hills": "Jubilee Hills"
}

PROPERTY_TYPE_ALIASES: Dict[str, str] = {
    "1bhk": "Apartment - 1 BHK",
    "1 bhk": "Apartment - 1 BHK",
    "studio": "Apartment - 1 BHK",
    "2bhk": "Apartment - 2 BHK",
    "2 bhk": "Apartment - 2 BHK",
    "flat": "Apartment - 2 BHK",
    "apartment": "Apartment - 2 BHK",
    "3bhk": "Apartment - 3 BHK",
    "3 bhk": "Apartment - 3 BHK",
    "4bhk": "Apartment - 4 BHK",
    "4 bhk": "Apartment - 4 BHK",
    "penthouse": "Penthouse",
    "sky villa": "Penthouse",
    "villa": "Villa",
    "rowhouse": "Villa",
    "bungalow": "Villa",
    "independent house": "Villa",
    "plot": "Plot",
    "land": "Plot",
    "site": "Plot",
    "commercial": "Commercial Space",
    "office": "Commercial Space",
    "retail": "Commercial Space"
}

class CleaningEngine:
    """High-throughput cleaning & standardization engine for real estate datasets."""

    @staticmethod
    def standardize_city(raw_city: Optional[str]) -> Tuple[str, bool]:
        """Standardize city name against master dictionary."""
        if not raw_city:
            return "Bengaluru", False  # Default regional hub
        clean = str(raw_city).strip().lower()
        if clean in CITY_ALIASES:
            return CITY_ALIASES[clean], True
        # Title case fallback
        return str(raw_city).strip().title(), False

    @staticmethod
    def standardize_locality(raw_locality: Optional[str]) -> Tuple[str, bool]:
        """Standardize locality name against master dictionary."""
        if not raw_locality:
            return "Central", False
        clean = str(raw_locality).strip().lower()
        if clean in LOCALITY_ALIASES:
            return LOCALITY_ALIASES[clean], True
        return str(raw_locality).strip().title(), False

    @staticmethod
    def standardize_property_type(raw_type: Optional[str]) -> Tuple[str, bool]:
        """Standardize property type (e.g. 2BHK/Flat -> Apartment - 2 BHK)."""
        if not raw_type:
            return "Apartment - 3 BHK", False
        clean = str(raw_type).strip().lower()
        if clean in PROPERTY_TYPE_ALIASES:
            return PROPERTY_TYPE_ALIASES[clean], True
        return str(raw_type).strip().title(), False

    @staticmethod
    def validate_indian_mobile(raw_phone: Optional[str]) -> Tuple[str, bool]:
        """Validate and normalize Indian mobile phone numbers.
        Indian mobiles are 10 digits starting with 6, 7, 8, or 9.
        Returns: (normalized_10_digits, is_valid)
        """
        if not raw_phone:
            return "", False
        digits = re.sub(r"[^\d]", "", str(raw_phone))
        # Handle +91 or 91 country code prefix
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith("0") and len(digits) == 11:
            digits = digits[1:]
        
        # Check standard 10-digit Indian mobile range [6-9]
        if len(digits) == 10 and digits[0] in ("6", "7", "8", "9"):
            return digits, True
        return digits, False

    @staticmethod
    def validate_email(raw_email: Optional[str]) -> Tuple[str, bool]:
        """Validate email format and lowercase domain."""
        if not raw_email:
            return "", False
        clean = str(raw_email).strip().lower()
        # Basic RFC-like regex
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if re.match(pattern, clean):
            return clean, True
        return clean, False

    @staticmethod
    def validate_budget_range(
        min_p: Optional[Any],
        max_p: Optional[Any],
        budget_fallback: float = 10000000.0
    ) -> Tuple[float, float, bool]:
        """Validates min_price <= max_price. If inverted or single budget given, normalizes range."""
        try:
            min_val = float(min_p) if min_p is not None and str(min_p).strip() else None
        except (ValueError, TypeError):
            min_val = None

        try:
            max_val = float(max_p) if max_p is not None and str(max_p).strip() else None
        except (ValueError, TypeError):
            max_val = None

        if min_val is not None and max_val is not None:
            if min_val > max_val:
                # Inverted: swap
                return max_val, min_val, False
            return min_val, max_val, True
        elif min_val is not None:
            return min_val, min_val * 1.3, True
        elif max_val is not None:
            return max_val * 0.7, max_val, True
        else:
            return budget_fallback * 0.8, budget_fallback * 1.2, True

    @classmethod
    def clean_record(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Cleans, normalizes, and validates a single lead data dictionary."""
        name = str(raw.get("name") or raw.get("Customer Name") or raw.get("customer_name") or "Unnamed Lead").strip()
        
        phone_raw = raw.get("mobile") or raw.get("Mobile Number") or raw.get("phone") or ""
        norm_phone, phone_valid = cls.validate_indian_mobile(phone_raw)
        
        email_raw = raw.get("email") or raw.get("Email ID") or raw.get("email_id") or ""
        norm_email, email_valid = cls.validate_email(email_raw)

        raw_city = raw.get("city") or raw.get("City Name") or raw.get("region") or ""
        std_city, city_matched = cls.standardize_city(raw_city)

        raw_locality = raw.get("locality") or raw.get("Locality Name") or raw.get("branch") or ""
        std_locality, loc_matched = cls.standardize_locality(raw_locality)

        raw_prop_type = raw.get("property_type") or raw.get("Property Type") or ""
        std_prop_type, prop_matched = cls.standardize_property_type(raw_prop_type)

        min_p = raw.get("min_price") or raw.get("Minimum Price")
        max_p = raw.get("max_price") or raw.get("Maximum Price") or raw.get("budget")
        std_min_p, std_max_p, budget_valid = cls.validate_budget_range(min_p, max_p)

        is_valid = bool(phone_valid and (email_valid or not norm_email))

        return {
            "name": name,
            "raw_phone": str(phone_raw).strip(),
            "phone": norm_phone,
            "mobile": norm_phone,
            "phone_valid": phone_valid,
            "mobile_valid": phone_valid,
            "is_valid_phone": phone_valid,
            "raw_email": str(email_raw).strip(),
            "email": norm_email,
            "email_valid": email_valid,
            "is_valid_email": email_valid,
            "city": std_city,
            "city_matched": city_matched,
            "locality": std_locality,
            "locality_matched": loc_matched,
            "property_type": std_prop_type,
            "property_type_matched": prop_matched,
            "min_price": std_min_p,
            "max_price": std_max_p,
            "budget_valid": budget_valid,
            "is_valid": is_valid,
            "project_name": str(raw.get("project_name") or raw.get("Project Name") or "").strip(),
            "allocated_to": str(raw.get("allocated_to") or raw.get("Allocated To") or "").strip()
        }
