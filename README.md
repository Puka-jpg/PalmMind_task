# PalmMind AI Chatbot

A conversational AI assistant for PalmMind Technology that answers company questions and handles appointment bookings.

## What This Does

Built a chatbot that acts like a company representative. It can:
- Answer questions about PalmMind's services, team, and achievements 
- Collect user contact info when they want to talk to the team
- Book appointments with smart date parsing ("tomorrow" → "2025-05-26")
- Save everything to files for the company to follow up

## How I Got The Data

Scraped all the content from PalmMind's website - their services, testimonials, company info, etc. Put it all in markdown files organized by category. The bot reads these files to answer questions about the company.

## Project Structure

```
├── server.py              # MCP server with appointment/contact tools
├── client.py              # Main chatbot that connects everything
├── server_config.json     # MCP server configuration  
├── palmmind_resources/    # Scraped company data
│   ├── company/          # About, mission, achievements
│   ├── services/         # AI services they offer
│   └── testimonials/     # Client testimonials
└── user_info/            # Generated contact & appointment files
```

## The Architecture 

**Server** (`server.py`): Handles the conversational tools using MCP (Model Context Protocol). Has two main tools:
- `collect_contact_info` - Gets name, phone, email through conversation
- `book_appointment` - Handles appointment booking with date parsing

**Client** (`client.py`): The main chatbot that connects to Claude AI and the MCP servers. Handles document search, file reading, and tool execution.

## Tools Breakdown

**Document Tools** (built-in MCP):
- `search_files` - Finds relevant company files 
- `read_file` - Reads the content to answer questions
- `list_directory` - Explores the file structure

**Custom Tools**:
- `collect_contact_info` - Multi-step conversation to get user details
- `book_appointment` - Books appointments with natural language date parsing

## Smart Features

- **Date Intelligence**: "tomorrow", "next Monday", "May 30th" → proper YYYY-MM-DD format
- **Shared Sessions**: Remembers user name across tools (no asking twice)
- **Input Validation**: Checks email format, phone numbers, prevents past dates
- **Conversational Flow**: Step-by-step dialogs that feel natural

## Running It

```bash

# Start the chatbot
uv run  client.py
```

## Assignment Requirements Met

✅ Document-based Q&A from company files  
✅ Conversational user info collection  
✅ Appointment booking with date format extraction  
✅ Input validation (email, phone, dates)  
✅ Tool-agent integration via MCP  
✅ File storage for collected data  

## Sample Interaction

```
💬 "What services do you provide?"
🤖 [Reads service files and explains PalmMind's AI offerings]

💬 "I want to book an appointment"  
🤖 "What's your name?"
💬 "John Smith"
🤖 "When would you like to schedule?"
💬 "tomorrow"
🤖 "Confirm appointment for John Smith on 2025-05-26?"
💬 "yes"
🤖 "✅ Appointment booked!"
```

