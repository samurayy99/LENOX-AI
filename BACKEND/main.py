import os
os.environ["USER_AGENT"] = "LenoxAI/1.0"


from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from lenox import Lenox  
from prompts import PromptEngine, PromptEngineConfig
from tool_imports import import_tools
from perplexity_research import PerplexityManager
import os
import traceback
import sys



# Load environment variables
load_dotenv()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
openai_api_key = os.getenv('OPENAI_API_KEY')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_secret_key')
app.config['UPLOAD_FOLDER'] = '/Users/lenox27/LENOX/uploaded_documents'
socketio = SocketIO(app)

# Configure structured logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

# Import tools before they are used
tools = import_tools()

# Ensure tools is a dictionary
tools_dict = {tool.name: tool for tool in tools} 


# Create instances of your components
prompt_engine_config = PromptEngineConfig(context_length=10, max_tokens=4096)
prompt_engine = PromptEngine(config=prompt_engine_config, tools=tools_dict)  # Pass tools_dict here

# Initialize PerplexityManager instead of GPTResearchManager
gpt_research_manager = PerplexityManager()


# Initialize Lenox with all necessary components
lenox = Lenox(tools=tools, prompt_engine=prompt_engine, openai_api_key=openai_api_key)  # Change this line


@app.before_request
def log_request():
    app.logger.debug(f'Incoming request: {request.method} {request.path}')
    session.setdefault('session_id', os.urandom(24).hex())

@app.after_request
def log_response(response):
    app.logger.debug(f'Outgoing response: {response.status}')
    return response

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gpt_research', methods=['POST'])
def gpt_research():
    data = request.get_json()
    query = data.get('query', '')
    report_type = data.get('report_type', 'research_report')
    report_source = data.get('report_source', 'web')
    source_urls = data.get('source_urls', None)
    
    if not query:
        return jsonify({'error': 'Empty query.'}), 400

    # Verbesserte GPT-Research Ausführung mit allen Parametern
    result = gpt_research_manager.run_gpt_research(
        query=query, 
        report_type=report_type, 
        report_source=report_source,
        source_urls=source_urls
    )
    return jsonify(result)




@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        app.logger.debug(f"🔍 Incoming payload: {data}")
        original_query = data.get('query') or data.get('message', '')

        if not original_query:
            app.logger.debug("No query provided in the request.")
            return jsonify({'error': 'Empty query.'}), 400

        app.logger.debug("Starting to process query with convchain.")
        result = lenox.convchain(original_query, session['session_id'])  # Use original query
        app.logger.debug(f"Processed query with convchain, result: {result}")

        # Handle both text and visualization responses
        if result['type'] == 'visualization':
            return jsonify({
                'type': 'visualization',
                'status': result['status'],
                'content': result['message'],
                'image': result['image']
            })
        elif result['type'] == 'text':
            return jsonify({
                'type': 'text',
                'content': result['content']
            })
        else:
            return jsonify({'error': 'Unknown response type.'}), 500

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Failed to process request.'}), 500




@socketio.on('connect')
def on_connect():
    emit('status', {'data': 'Connected to real-time updates'})

if __name__ == '__main__':
    try:
        app.logger.info("Starting Flask-SocketIO server...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        app.logger.critical(f"Failed to start server: {str(e)}")
        app.logger.critical(traceback.format_exc())
        sys.exit(1)
