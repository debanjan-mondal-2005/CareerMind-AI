import re
from typing import Optional

def detect_language_command(text: str) -> Optional[str]:
    """
    Detects if the user text is an explicit command to switch language.
    Returns 'bengali' or 'english' if a command is detected, else None.
    """
    if not text:
        return None
        
    text_clean = text.lower().strip().replace("?", "").replace(".", "").replace("!", "")
    
    bengali_patterns = [
        r'\btalk\s+in\s+bengali\b',
        r'\bbengali\s+please\b',
        r'\bspeak\s+bengali\b',
        r'\banswer\s+in\s+bengali\b',
        r'\bswitch\s+to\s+bengali\b',
        r'বাংলায়\s+কথা\s+বলো',
        r'বাংলা\s+বলো',
        r'বাংলায়\s+কথা\s+বলুন',
        r'বাংলা\s+বলুন',
        r'বাংলায়\s+উত্তর\s+দাও',
        r'বাংলায়\s+কথা\s+বলবেন',
        r'বাংলা\s+ভাষা\s+চালু\s+করো'
    ]
    
    english_patterns = [
        r'\btalk\s+in\s+english\b',
        r'\benglish\s+please\b',
        r'\bspeak\s+english\b',
        r'\banswer\s+in\s+english\b',
        r'\bswitch\s+to\s+english\b',
        r'ইংরেজিতে\s+কথা\s+বলো',
        r'ইংরেজি\s+বলো',
        r'ইংরেজিতে\s+কথা\s+বলুন',
        r'ইংরেজি\s+বলুন',
        r'ইংরেজিতে\s+উত্তর\s+দাও',
        r'ইংরেজিতে\s+কথা\s+বলবেন',
        r'ইংরেজি\s+ভাষা\s+চালু\s+করো'
    ]
    
    for pattern in bengali_patterns:
        if re.search(pattern, text_clean):
            return "bengali"
            
    for pattern in english_patterns:
        if re.search(pattern, text_clean):
            return "english"
            
    return None
