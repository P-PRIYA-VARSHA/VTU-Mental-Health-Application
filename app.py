from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import random
from werkzeug.security import generate_password_hash, check_password_hash

# Multi-language and transliteration imports
from langdetect import detect
from googletrans import Translator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

app = Flask(__name__)
app.secret_key = 'a_development_secret_key'  # Change to a secure random value in production

#############################################
# Multi-language Chatbot Class
#############################################
class RomanizedChatbot:
    def __init__(self):  # Correct initializer with double underscores
        self.translator = Translator()
        self.default_language = "en"
        # Extended responses with additional mental health prompts
        self.responses = {
            # English responses
            "hi": "Hello! How can I help you?",
            "hello": "Hello! How can I help you?",
            "how are you": "I'm a chatbot, so I'm always fine!",
            "bye": "Goodbye! Have a great day!",
            "help": "I'm here to help. Could you please specify your concern?",
            "sad": "I'm sorry to hear you're feeling sad. It might help to talk to someone who understands.",
            "anxious": "It sounds like you're feeling anxious. Try some deep breathing or a short meditation.",
            "stress": "Stress can be overwhelming. Consider taking a break, going for a walk, or doing some light stretching.",
            "overwhelmed": "Feeling overwhelmed? Break your tasks into smaller steps and take a moment to relax.",
            "depressed": "I'm truly sorry you're feeling depressed. Please consider talking to a trusted friend or professional.",
            "tired": "If you're feeling tired, perhaps a short rest or some calming music might help.",
            "default": "I'm sorry, I don't understand. Could you please rephrase?",
            
            # Telugu (romanized)
            "namaskaram": "Namaskaram! How can I help you?",
            "em chestunav": "Nothing, do you need any help?", "avunu" : "How are you feeling?",
            "bagunnanu": "I'm glad to hear you're doing well!",
            "vellosthanu": "Goodbye! Take care!",
            "sahayam cheyandi": "I'm here to help. Please tell me what you need.",
            "badhaga unnanu": "I'm sorry you're feeling sad. Sometimes talking helps.",
            "chinthaga undi": "It sounds like you're worried. Try taking deep breaths and relax.",
            
            # Hindi (romanized)
            "namaste": "Namaste! How can I help you?",
            "aap kaise ho": "I'm a chatbot, so I'm always fine!",
            "aap kaise hain": "I'm a chatbot, so I'm always fine!",
            "alvida": "Alvida! Have a great day!",
            "madad": "I'm here to help. Please specify your concern.",
            "dukhi": "I'm sorry you're feeling sad. Sometimes sharing your feelings helps.",
            "chinta": "It seems you're worried. Try some deep breathing and relaxation.",
            
            # Tamil (romanized)
            "vanakkam": "Vanakkam! How can I help you?",
            "epdi irukkeenga": "I'm a chatbot, so I'm always good!",
            "poitu varen": "Goodbye! Take care!",
            "udavi": "I'm here to help. Could you please specify your concern?",
                    }
        # Supported languages for translation/transliteration
        self.supported_languages = {
            "hi": sanscript.ITRANS,  # Hindi (romanized)
            "te": sanscript.ITRANS,  # Telugu (romanized)
            "ta": sanscript.ITRANS   # Tamil (romanized)
        }

    def detect_language(self, text):
        try:
            lang = detect(text)
            # If the detected language is one of our supported ones, return it; otherwise, return default.
            return lang if lang in self.supported_languages else self.default_language
        except Exception:
            return self.default_language

    def translate_text(self, text, dest_lang):
        return self.translator.translate(text, dest=dest_lang).text

    def transliterate_text(self, text, lang_code):
        if lang_code in self.supported_languages:
            # Choose script based on language code
            script = sanscript.DEVANAGARI if lang_code == "hi" else (
                sanscript.TELUGU if lang_code == "te" else sanscript.TAMIL
            )
            return transliterate(text, script, self.supported_languages[lang_code])
        return text

    def get_response(self, user_input, user_lang):
        user_input_lower = user_input.lower()
        response = None
        # Check for an exact match first:
        if user_input_lower in self.responses:
            response = self.responses[user_input_lower]
        else:
            # If no exact match, look for partial matches:
            for key, val in self.responses.items():
                if key in user_input_lower:
                    response = val
                    break
        if response is None:
            response = self.responses["default"]

        if user_lang != self.default_language:
            # Translate the English response to the target language
            translated_response = self.translate_text(response, user_lang)
            # Then transliterate it to a romanized script using ITRANS
            response = self.transliterate_text(translated_response, user_lang)
        return response

    def chat(self):
        print("Chatbot is running! Type 'exit' to stop.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Chatbot: Goodbye!")
                break
            user_lang = self.detect_language(user_input)
            response = self.get_response(user_input, user_lang)
            print(f"Chatbot ({user_lang}): {response}")

#############################################
# Database Helper and Initialization
#############################################
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create surveys table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            q1 TEXT,
            q2 TEXT,
            q3 TEXT,
            q4 TEXT,
            q5 TEXT,
            q6 TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Create blog posts table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()  # Initialize the database on startup

#############################################
# Survey Analysis, Recommendations, and Solutions
#############################################
def analyze_survey(answers):
    score = 0
    # Q1: Mood (Good=0, Average=1, Bad=2)
    answer = answers.get('q1', '').lower()
    if answer == 'good':
        score += 0
    elif answer == 'average':
        score += 1
    elif answer == 'bad':
        score += 2
    # Q2: Energy (High=0, Medium=1, Low=2)
    answer = answers.get('q2', '').lower()
    if answer == 'high':
        score += 0
    elif answer == 'medium':
        score += 1
    elif answer == 'low':
        score += 2
    # Q3: Sleep (Well=0, Poorly=2)
    answer = answers.get('q3', '').lower()
    if answer == 'well':
        score += 0
    elif answer == 'poorly':
        score += 2
    # Q4: Stress (Low=0, Moderate=1, High=2)
    answer = answers.get('q4', '').lower()
    if answer == 'low':
        score += 0
    elif answer == 'moderate':
        score += 1
    elif answer == 'high':
        score += 2
    # Q5: Connection (Connected=0, Neutral=1, Isolated=2)
    answer = answers.get('q5', '').lower()
    if answer == 'connected':
        score += 0
    elif answer == 'neutral':
        score += 1
    elif answer == 'isolated':
        score += 2
    # Q6: Overall Well-Being (Good=0, Average=1, Bad=2)
    answer = answers.get('q6', '').lower()
    if answer == 'good':
        score += 0
    elif answer == 'average':
        score += 1
    elif answer == 'bad':
        score += 2

    if score >= 8:
        return 'High'
    elif score >= 4:
        return 'Moderate'
    else:
        return 'Low'

def get_recommendations(risk_level):
    recommendations = {
        'Low': ['Maintain a healthy routine', 'Stay socially active'],
        'Moderate': ['Practice mindfulness', 'Consider talking to a counselor'],
        'High': ['Seek professional help', 'Engage in support groups']
    }
    return recommendations.get(risk_level, [])

detailed_solutions = {
    "High": {
        "yoga": [
            {
                "pose": "Child's Pose",
                "image": "/static/images/childs_pose.jpg",
                "description": "A great pose for relaxation and calming your mind. 🧘‍♀️"
            },
            {
                "pose": "Corpse Pose",
                "image": "/static/images/corpse_pose.jpg",
                "description": "Helps with deep relaxation. 😌"
            }
        ],
        "meditation": "Try mindfulness meditation for 10 minutes daily. 🧘‍♂️",
        "music": """
        <iframe width="560" height="315" src="https://www.youtube.com/embed/_4kHxtiuML0" 
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen></iframe>
        """,
        "joke": "Why did the scarecrow win an award? Because he was outstanding in his field! 🤣🌾",
        "quote": "Keep your face always toward the sunshine—and shadows will fall behind you. ☀ - Walt Whitman",
        "helpline": {
            "doctor_name": "Dr. John Smith 👨‍⚕️",
            "hospital": "ABC Mental Health Clinic 🏥",
            "phone": "1-800-123-4567",
            "call_link": "tel:1-800-123-4567"
        }
    },
    "Moderate": {
        "yoga": [
            {
                "pose": "Cat-Cow Pose",
                "image": "/static/images/cat_cow.jpg",
                "description": "Helps relieve tension in your back and neck. 🐱🐮"
            },
            {
                "pose": "Seated Forward Bend",
                "image": "/static/images/seated_forward_bend.jpg",
                "description": "Stretches the spine and soothes the nervous system. 🤸‍♂️"
            }
        ],
        "meditation": "Practice deep breathing exercises for 5-10 minutes daily. 🧘‍♀️",
        "music": """
        <iframe width="560" height="315" src="https://www.youtube.com/embed/_4kHxtiuML0" 
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen></iframe>
        """,
        "joke": "I tried to catch fog yesterday... I mist! 😅🌫️",
        "quote": "The best way to predict the future is to create it. 🚀 - Peter Drucker",
        "helpline": {
            "doctor_name": "Dr. Emily Davis 👩‍⚕️",
            "hospital": "XYZ Counseling Center 🏥",
            "phone": "1-800-234-5678",
            "call_link": "tel:1-800-234-5678"
        }
    },
    "Low": {
        "yoga": [
            {
                "pose": "Mountain Pose",
                "image": "/static/images/mountain_pose.jpg",
                "description": "Helps improve posture and balance. ⛰️"
            },
            {
                "pose": "Tree Pose",
                "image": "/static/images/tree_pose.jpg",
                "description": "Boosts concentration and stability. 🌳"
            }
        ],
        "meditation": "Maintain a regular meditation practice to keep stress at bay. 🧘‍♂️",
        "music": """
        <iframe width="560" height="315" src="https://www.youtube.com/embed/_4kHxtiuML0" 
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen></iframe>
        """,
        "joke": "I used to be addicted to soap, but I'm clean now! 😄🧼",
        "quote": "The only way to do great work is to love what you do. ❤ - Steve Jobs",
        "helpline": {
            "doctor_name": "Dr. Sarah Lee 👩‍⚕️",
            "hospital": "Wellness Center 🏥",
            "phone": "1-800-345-6789",
            "call_link": "tel:1-800-345-6789"
        }
    }
}



#############################################
# Routes
#############################################
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html', logged_in=True)
    return render_template('index.html', logged_in=False)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different one.', 'error')
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'user_id' not in session:
        flash('Please log in to take the survey.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        answers = {
            'q1': request.form.get('q1'),
            'q2': request.form.get('q2'),
            'q3': request.form.get('q3'),
            'q4': request.form.get('q4'),
            'q5': request.form.get('q5'),
            'q6': request.form.get('q6')
        }
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO surveys (user_id, q1, q2, q3, q4, q5, q6)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session['user_id'], answers['q1'], answers['q2'], answers['q3'], answers['q4'], answers['q5'], answers['q6']))
        conn.commit()
        conn.close()
        risk_level = analyze_survey(answers)
        recommendations = get_recommendations(risk_level)
        detailed_solution = detailed_solutions.get(risk_level, {})
        return render_template('survey_result.html', risk_level=risk_level, recommendations=recommendations, detailed_solution=detailed_solution)
    return render_template('survey.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        flash('Please log in to access chat support.', 'error')
        return redirect(url_for('login'))
    return render_template('chat.html')


@app.route('/breathing_exercise')
def breathing_exercise():
    return render_template('breathing_exercise.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get('message', '')
    lower_msg = user_message.lower()
    
    # Create an instance of the multi-language chatbot
    bot = RomanizedChatbot()
    response = bot.get_response(user_message, bot.detect_language(user_message))
    
    return jsonify({'response': response})

@app.route('/blog')
def blog():
    conn = get_db_connection()
    posts = conn.execute('''
        SELECT blog_posts.*, users.username
        FROM blog_posts
        JOIN users ON blog_posts.user_id = users.id
        ORDER BY timestamp DESC
    ''').fetchall()
    conn.close()
    return render_template('blog.html', posts=posts)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
@app.route('/mood-tracker')
def mood_tracker():
    return render_template('moodtracker.html')

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    if 'user_id' not in session:
        flash("Please log in to create a blog post.", "error")
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        conn = get_db_connection()
        conn.execute('INSERT INTO blog_posts (user_id, title, content) VALUES (?, ?, ?)',
                     (session['user_id'], title, content))
        conn.commit()
        conn.close()
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('blog'))
    return render_template('newpost.html')

if __name__ == '__main__':
    app.run(debug=True)
