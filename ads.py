# ads.py
import random

# Dynamic verify links
VERIFY_LINKS = [
    "https://example.com/verify1",
    "https://example.com/verify2",
    "https://example.com/verify3"
]

# Dynamic tutorial links
TUTORIAL_LINKS = [
    "https://example.com/tutorial1",
    "https://example.com/tutorial2",
    "https://example.com/tutorial3"
]

def get_verify_link():
    """Return a random verify link"""
    return random.choice(VERIFY_LINKS)

def get_tutorial_link():
    """Return a random tutorial link"""
    return random.choice(TUTORIAL_LINKS)

def get_ads():
    """Return both links as dict"""
    return {
        "verify": get_verify_link(),
        "tutorial": get_tutorial_link()
    }
