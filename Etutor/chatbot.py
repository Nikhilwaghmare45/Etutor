import re
import random
from together import Together

# Hardcode the API key directly into the code
api_key = "e2cdedaed5b8fa5245a0796f93c6d1ced06d90e710138d0da4aa74c1ddd67952"  # Replace with your actual API key

# Initialize the Together client with your API key
client = Together(api_key=api_key)

class Chatbot:
    def __init__(self):
        self.course_data = None
        self.knowledge_base = {
            "python": {},
            "data_analytics": {},
            "full_stack": {}
        }
        self.greetings = ["hi", "hello", "hey", "greetings", "what's up"]
        self.greeting_responses = [
            "Hello! How can I assist you with your learning today?",
            "Hi there! What would you like to know about the course material?",
            "Hey! I’m here to help with your studies. What’s on your mind?",
            "Greetings! Ready to dive into some course content?",
            "Hello! What part of the material can I help you with?"
        ]
        self.farewells = ["bye", "goodbye", "see you", "see ya", "farewell"]
        self.farewell_responses = [
            "Goodbye! Keep up the great work with your studies!",
            "See you later! Feel free to come back with more questions.",
            "Bye! Happy learning!",
            "Farewell! Practice makes perfect—keep at it!",
            "See you soon! Don’t hesitate to ask if you need more help."
        ]
        self.thanks = ["thank you", "thanks", "appreciate it", "thank"]
        self.thanks_responses = [
            "You’re welcome! Anything else I can help with?",
            "My pleasure! What’s your next question?",
            "No problem! I’m here to assist whenever you need me.",
            "Glad to help! What else can I explain?",
            "You’re welcome! Keep the questions coming if you’d like."
        ]
        self.fallback_responses = [
            "I’m not sure I understood that. Could you ask about a specific topic from the course?",
            "Hmm, I might need more details. What part of the material are you curious about?",
            "I don’t have an answer for that yet. Try asking about a concept from the chapter.",
            "Let’s focus on the course content—any particular topic you’d like me to explain?",
            "I’m here to help with the course material. What would you like to discuss?"
        ]

    def load_course_data(self, course_data):
        """Load course data from provided JSON data (courses.json structure)"""
        self.course_data = course_data
        self._build_knowledge_base()

    def _build_knowledge_base(self):
        """Build a knowledge base from the courses.json structure"""
        if not self.course_data:
            return
        
        for course_name, course_info in self.course_data.items():
            self.knowledge_base[course_name]["chapters"] = {}
            for chapter in course_info.get("chapters", []):
                chapter_id = chapter["id"]
                self.knowledge_base[course_name]["chapters"][chapter_id] = {
                    "title": chapter.get("title", ""),
                    "content": chapter.get("content", "")
                }

    def get_response(self, user_input, current_course=None, current_chapter=None):
        """Generate a response based on user input and context"""
        user_input = user_input.lower().strip()
        
        # Handle basic interactions
        if any(greeting in user_input for greeting in self.greetings):
            return random.choice(self.greeting_responses)
        
        if any(farewell in user_input for farewell in self.farewells):
            return random.choice(self.farewell_responses)
        
        if any(thank in user_input for thank in self.thanks):
            return random.choice(self.thanks_responses)

        # Handle help requests
        if "help" in user_input or "assist" in user_input:
            return "I can explain topics from the course material, answer questions about specific chapters, or clarify anything you’re unsure about. What do you need help with?"

        # Check if course data is loaded
        if not self.course_data:
            return "I couldn’t load the course data. Please ensure the data is provided and try again."

        # Determine course and chapter context
        course = current_course if current_course else self._identify_course(user_input)
        chapter_id = current_chapter if current_chapter else self._identify_chapter(user_input)

        if not course:
            course = self._identify_course(user_input)
            if not course:
                return random.choice(self.fallback_responses)

        if course not in self.knowledge_base:
            return f"I don’t have information on {course} yet. I can help with 'python', 'data_analytics', or 'full_stack'. What would you like to explore?"

        # Handle chapter-specific questions
        if chapter_id and chapter_id in self.knowledge_base[course]["chapters"]:
            chapter_data = self.knowledge_base[course]["chapters"][chapter_id]
            response = self._generate_chapter_response(user_input, chapter_data, course, chapter_id)
            if response:
                return response
        elif chapter_id:  # Chapter specified but not found
            return f"I couldn’t find Chapter {chapter_id} in {course}. Try asking about a chapter that exists, like Chapter 1!"

        # Handle general course questions
        response = self._generate_course_response(user_input, course)
        if response:
            return response

        # Fallback if no specific match
        return random.choice(self.fallback_responses)

    def _identify_course(self, query):
        """Identify the course from the query"""
        course_keywords = {
            "python": ["python", "programming", "variable", "loop", "function", "data type", "list", "dictionary"],
            "data_analytics": ["data", "analytics", "analysis", "visualization", "statistics", "lifecycle"],
            "full_stack": ["web", "frontend", "backend", "html", "css", "javascript", "full stack", "http"]
        }
        matches = {course: 0 for course in course_keywords}
        for course, keywords in course_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    matches[course] += 1
        max_matches = max(matches.values())
        if max_matches > 0:
            for course, count in matches.items():
                if count == max_matches:
                    return course
        return None

    def _identify_chapter(self, query):
        """Identify the chapter number from the query"""
        chapter_match = re.search(r'chapter (\d+)', query)
        return int(chapter_match.group(1)) if chapter_match else None

    def _generate_chapter_response(self, query, chapter_data, course_name, chapter_id):
        """Generate a response based on chapter-specific content"""
        content = chapter_data["content"].lower()
        chapter_title = chapter_data["title"]

        # Use the Together API for complex queries
        try:
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",  # Ensure this model exists and is available
                messages=[{"role": "user", "content": f"Please explain '{query}' in the context of {course_name} Chapter {chapter_id}."}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error fetching response: {str(e)}"

    def _generate_course_response(self, query, course_name):
        """Generate a response for general course questions"""
        chapters = self.knowledge_base[course_name]["chapters"]
        course_info = self.course_data[course_name]
        
        # Use the Together API for general queries
        try:
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",  # Ensure this model exists and is available
                messages=[{"role": "user", "content": f"Please explain the {course_name} course and its chapters, focusing on {query}."}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error fetching response: {str(e)}"

def get_chatbot(course_data=None):
    chatbot = Chatbot()
    if course_data is not None:
        chatbot.load_course_data(course_data)
    return chatbot
