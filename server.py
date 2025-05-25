import os
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from dateutil import parser
import re

mcp = FastMCP("palmmind")

# Global user info shared across tools during chat session
user_info = {}
contact_state = {}
appointment_state = {}

def extract_name_from_text(text):
    """Extract name from various input patterns - with aggressive cleaning"""
    text = text.strip()
    
    # AGGRESSIVE CLEANING - Remove Claude's added context
    # Remove patterns like "Name: Pukar Kafle - context"
    if " - " in text:
        text = text.split(" - ")[0]
    
    # Remove "Name:" prefix if Claude added it
    if text.lower().startswith("name:"):
        text = text[5:].strip()
    
    # Remove any remaining prefixes
    text = re.sub(r'^(name:?\s*)', '', text, flags=re.IGNORECASE)
    
    # Pattern 1: "My name is John Doe"
    match = re.search(r"my name is (.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: "I'm John Doe" or "I am John Doe"
    match = re.search(r"i'?m (.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    match = re.search(r"i am (.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Pattern 3: Just the name directly
    return text.strip()

def parse_date_from_text(date_text):
    """Parse natural language date to YYYY-MM-DD format"""
    try:
        date_text = date_text.lower().strip()
        today = datetime.now().date()
        
        # Handle relative dates
        if 'today' in date_text:
            return today.strftime('%Y-%m-%d')
        elif 'tomorrow' in date_text:
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'next week' in date_text:
            return (today + timedelta(days=7)).strftime('%Y-%m-%d')
        elif 'next monday' in date_text:
            days_ahead = 0 - today.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'next tuesday' in date_text:
            days_ahead = 1 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'next wednesday' in date_text:
            days_ahead = 2 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'next thursday' in date_text:
            days_ahead = 3 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'next friday' in date_text:
            days_ahead = 4 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'next saturday' in date_text:
            days_ahead = 5 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'next sunday' in date_text:
            days_ahead = 6 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif re.search(r'in (\d+) days?', date_text):
            days = int(re.search(r'in (\d+) days?', date_text).group(1))
            return (today + timedelta(days=days)).strftime('%Y-%m-%d')
        else:
            # Try to parse other formats like "May 30", "2025-05-30", etc.
            parsed_date = parser.parse(date_text, fuzzy=True)
            return parsed_date.strftime('%Y-%m-%d')
            
    except Exception as e:
        print(f"Date parsing error: {e}")
        return None

def save_appointment_to_file(date, user_name, status="confirmed"):
    """Save appointment to text file"""
    try:
        os.makedirs("./palmmind_resources/user_info", exist_ok=True)
        entry = f"""
=== APPOINTMENT REQUEST ===
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Appointment Date: {date}
Name: {user_name}
Status: {status}
===========================

"""
        with open("./palmmind_resources/user_info/appointments.txt", "a") as f:
            f.write(entry)
        return True
    except Exception as e:
        print(f"File save error: {e}")
        return False

@mcp.tool()
def collect_contact_info(user_message: str, session_id: str = "default") -> str:
    """Collect contact information when user wants to be reached"""
    global contact_state, user_info

    # Clean and process input
    if isinstance(user_message, list):
        user_message = " ".join(str(item) for item in user_message)
    elif not isinstance(user_message, str):
        user_message = str(user_message)
    
    # AGGRESSIVE CLEANING - Remove Claude's context injection
    user_message = user_message.strip()
    if " - " in user_message and ("would like" in user_message.lower() or "want" in user_message.lower()):
        user_message = user_message.split(" - ")[0]
    if user_message.lower().startswith("name:"):
        user_message = user_message[5:].strip()
    
    # Check if we already have user name from shared session
    if 'name' in user_info and session_id not in contact_state:
        contact_state[session_id] = {"step": "contact", "info": {"name": user_info['name']}}
        return f"Great {user_info['name']}! Please provide your phone and email:"
    
    if session_id not in contact_state:
        contact_state[session_id] = {"step": "name", "info": {}}
        return "I'd be happy to arrange that! What's your name?"
    
    state = contact_state[session_id]
    
    if state["step"] == "name":
        extracted_name = extract_name_from_text(user_message)
        state["info"]["name"] = extracted_name
        user_info['name'] = extracted_name  # Store in global user info
        state["step"] = "contact"
        return f"Great, {extracted_name}! Please provide your phone and email:"
    
    elif state["step"] == "contact":
        if "@" not in user_message or not any(c.isdigit() for c in user_message):
            return "Please provide both phone and email:"
        
        state["info"]["contact"] = user_message.strip()
        state["step"] = "confirm"
        return f"Confirm:\nName: {state['info']['name']}\nContact: {state['info']['contact']}\n\nCorrect? (yes/no)"
    
    elif state["step"] == "confirm":
        if user_message.lower().startswith('y'):
            try:
                os.makedirs("./palmmind_resources/user_info", exist_ok=True)
                entry = f"""
=== CONTACT REQUEST ===
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Name: {state['info']['name']}
Contact: {state['info']['contact']}
========================

"""
                with open("./palmmind_resources/user_info/contacts.txt", "a") as f:
                    f.write(entry)
                
                name = state['info']['name']
                del contact_state[session_id]
                return f"✅ Thanks {name}! We'll contact you soon!"
            except Exception as e:
                print(f"Contact save error: {e}")
                return "Error saving contact. Please try again."
        else:
            contact_state[session_id] = {"step": "name", "info": {}}
            return "Let's start over. What's your name?"
    
    return "Something went wrong. Let me start over - what's your name?"

@mcp.tool()
def book_appointment(user_message: str, session_id: str = "default") -> str:
    """Book appointment with file storage and date format validation"""
    global appointment_state, user_info

    # Clean and process input
    if isinstance(user_message, list):
        user_message = " ".join(str(item) for item in user_message)
    elif not isinstance(user_message, str):
        user_message = str(user_message)
    
    # AGGRESSIVE CLEANING - Remove Claude's context injection
    user_message = user_message.strip()
    if " - " in user_message and ("would like" in user_message.lower() or "want" in user_message.lower()):
        user_message = user_message.split(" - ")[0]
    if user_message.lower().startswith("name:"):
        user_message = user_message[5:].strip()
    
    # Check if we already have user name from shared session and no active appointment session
    if 'name' in user_info and session_id not in appointment_state:
        appointment_state[session_id] = {"step": "date", "info": {"name": user_info['name']}}
        return f"Great {user_info['name']}! When would you like to schedule your appointment? (e.g., 'tomorrow', 'next Monday', 'May 30th')"
    
    # Initialize appointment session if it doesn't exist
    if session_id not in appointment_state:
        appointment_state[session_id] = {"step": "name", "info": {}}
        return "I'll help you book an appointment! What's your name?"
    
    state = appointment_state[session_id]
    
    # Handle name collection
    if state["step"] == "name":
        extracted_name = extract_name_from_text(user_message)
        state["info"]["name"] = extracted_name
        user_info['name'] = extracted_name  # Store in global user info
        state["step"] = "date"
        return f"Great {extracted_name}! When would you like to schedule your appointment? (e.g., 'tomorrow', 'next Monday', 'May 30th')"
    
    # Handle date collection
    elif state["step"] == "date":
        # Parse the date
        parsed_date = parse_date_from_text(user_message)
        
        if not parsed_date:
            return "I couldn't understand that date. Please try again (e.g., 'tomorrow', 'next Monday', 'May 30th'):"
        
        # Check if date is in the past
        if parsed_date < datetime.now().strftime('%Y-%m-%d'):
            return "That date is in the past. Please choose a future date:"
        
        state["info"]["date"] = parsed_date
        state["step"] = "confirm"
        return f"Perfect! I'll schedule your appointment for {parsed_date}. Confirm appointment for {state['info']['name']} on {parsed_date}? (yes/no)"
    
    # Handle confirmation
    elif state["step"] == "confirm":
        if user_message.lower() in ['yes', 'y', 'yeah', 'yep', 'confirm']:
            name = state['info']['name']
            date = state['info']['date']
            
            # Save appointment to file
            if save_appointment_to_file(date, name, "confirmed"):
                # Clean up session state
                del appointment_state[session_id]
                return f"✅ Appointment booked successfully!\n\n📅 {name} - {date}\n💾 Your appointment has been saved and we'll confirm the exact time with you soon!"
            else:
                return "Error saving appointment. Please try again."
        else:
            # Reset appointment state
            appointment_state[session_id] = {"step": "name", "info": {}}
            return "Let's start over. What's your name?"
    
    # Fallback
    return "Something went wrong. Let me start over - what's your name?"

if __name__ == "__main__":
    print("Starting PalmMind MCP Server with Appointment Booking...")
    mcp.run(transport='stdio')