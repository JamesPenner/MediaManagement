regex_library = {
    "Alphabetic Characters Only": r"^[a-zA-Z]+$",
    "Alphanumeric Characters": r"^[a-zA-Z0-9]+$",
    "Credit Card Number (Simple)": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "Date (YYYY-MM-DD)": r"\b\d{4}-\d{2}-\d{2}\b",
    "Email Validation": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
    "File Extension Matching": r"(\.jpg|\.jpeg|\.png|\.gif)$"
    "Hexadecimal Color Code": r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
    "HTML Tag Matching": r"<([a-z1-6]+)([^<]+)*(?:>(.*)<\/\1>|\s+\/>)",
    "IP Address Validation": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "Markdown Link": r"\[([^\]]+)\]\(([^)]+)\)",
    "Numeric Validation": r"^-?\d*\.?\d+$",
    "Password Strength": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
    "Phone Number (US Format)": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "Social Security Number (SSN)": r"^\d{3}-\d{2}-\d{4}$",
    "Special Characters": r"[^a-zA-Z0-9\s]",
    "Time in HH:MM format": r"^(?:[01]\d|2[0-3]):[0-5]\d$",
    "Tranbc Highway Reference": r"\b(bc)*h[ighway]*[\s#]*(\d+[abcd]*)\b"
    "URL Validation": r"https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?",
    "Username Validation (Alphanumeric)": r"^[a-zA-Z0-9_]+$",
    "Whitespace Removal": r"^\s+|\s+$",
    "Zip Code (US)": r"^\d{5}(?:[-\s]\d{4})?$",
}
