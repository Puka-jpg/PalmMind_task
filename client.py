from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import json
import asyncio
import nest_asyncio

nest_asyncio.apply()
load_dotenv()

class PalmMindChatBot:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        # Tools list required for Anthropic API
        self.available_tools = []
        # Sessions dict maps tool names to MCP client sessions
        self.sessions = {}
        self.conversation_history = []

    async def connect_to_server(self, server_name, server_config):
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            
            try:
                response = await session.list_tools()
                if server_name == "filesystem":
                    allowed_tools = ['read_file', 'search_files', 'list_directory']
                elif server_name == "palmmind":
                    allowed_tools = ['collect_contact_info', 'book_appointment']  # Added book_appointment
                else:
                    allowed_tools = []
                    
                for tool in response.tools:
                    if tool.name in allowed_tools:
                        self.sessions[tool.name] = session
                        self.available_tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        })
                        print(f"Loaded tool: {tool.name}")
            
            except Exception as e:
                print(f"Error loading tools from {server_name}: {e}")
                
        except Exception as e:
            print(f"Error connecting to {server_name}: {e}")

    async def connect_to_servers(self):
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            servers = data.get("mcpServers", {})
            
            print("🔗 Connecting to MCP servers...")
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
            
            print(f"✅ Connected to {len(servers)} server(s)")
            print(f"Loaded {len(self.available_tools)} tools")
            
        except Exception as e:
            print(f"Error loading server config: {e}")
            raise
    
    async def process_query(self, query):
        """Process user query and handle tool calls"""
        if not hasattr(self, 'conversation_history'):
            self.conversation_history = []
        
        self.conversation_history.append({'role': 'user', 'content': query})
        
        while True:
            response = self.anthropic.messages.create(
                max_tokens=2024,
                model='claude-3-5-sonnet-20241022', 
                tools=self.available_tools,
                messages=self.conversation_history,
                system="""You are Paul, a friendly AI assistant for PalmMind Technology. 

CONVERSATION STYLE:
- Be natural, conversational, and helpful (not corporate or sales-y)
- Keep responses concise and engaging
- Only use tools when users ask SPECIFIC questions about company information or want to take actions

WHEN TO USE TOOLS:
USE tools when users ask about:
- "What services do you offer?" → search for services info
- "Tell me about your company" → read company info  
- "Do you have testimonials?" → read testimonials
- "What's your team like?" → read team info
- Want to be contacted/reached/meeting/collaboration/speak to team → use collect_contact_info
- Want to book/schedule appointment/meeting → use book_appointment

TOOL USAGE RULES:
- Use search_files FIRST to find relevant files
- Then read_file only the most relevant file
- For contact requests: use collect_contact_info
- For appointment requests: use book_appointment

COMPANY BASICS (use without tools):
PalmMind is an AI/ML company (7+ years, 100+ projects) offering AI agents for customer experience, internal teams, and workflow automation.

Be helpful but don't over-fetch information!"""
            )
            
            assistant_content = []
            has_tool_use = False
            
            for content in response.content:
                if content.type == 'text':
                    print(content.text)
                    assistant_content.append(content)
                elif content.type == 'tool_use':
                    has_tool_use = True
                    assistant_content.append(content)
                    
                    # Getting session and calling tool
                    session = self.sessions.get(content.name)
                    if not session:
                        print(f" Tool '{content.name}' not found.")
                        break
                    
                    try:
                        # Show tool usage for legitimate requests
                        if any(keyword in query.lower() for keyword in 
                               ['service', 'company', 'team', 'testimonial', 'about', 'what', 'tell me', 
                                'contact', 'call', 'reach', 'appointment', 'book', 'schedule', 'meeting']):
                            print(f"🔧 {content.name}")
                        
                        result = await session.call_tool(content.name, arguments=content.input)
                        
                        # Print the tool result immediately so user can see it - extract text properly
                        if result.content:
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    print(item.text)
                        
                        # Adding assistant message with tool use
                        self.conversation_history.append({'role': 'assistant', 'content': assistant_content})
                        
                        # Add tool result
                        self.conversation_history.append({
                            "role": "user", 
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": result.content
                                }
                            ]
                        })
                        
                    except Exception as e:
                        print(f"Error calling tool {content.name}: {e}")
                        break
            
            # Exit loop if no tool was used
            if not has_tool_use:
                break
    
    async def chat_loop(self):
        """Main chat interface"""
        print("\n" + "="*50)
        print("🤖 PalmMind AI Assistant")
        print("="*50)
        print("Hi! I'm Paul from PalmMind Technology.")
        print("Ask me about our AI solutions, team, services, or book an appointment!")
        print("="*50)
        
        while True:
            try:
                query = input("\n💬 You: ").strip()
                if not query:
                    continue
        
                if query.lower() in ['quit', 'exit', 'bye']:
                    print("\n🤖 Paul: Thanks for chatting! Feel free to reach out anytime. 👋")
                    break
                
                print("\n🤖 Paul:")
                await self.process_query(query)
                    
            except KeyboardInterrupt:
                print("\n🤖 Paul: Thanks for chatting! Feel free to reach out anytime. 👋")
                break
            except Exception as e:
                print(f"\nSorry, something went wrong: {str(e)}")
                print("Please try asking your question differently.")
    
    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    chatbot = PalmMindChatBot()
    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())