import os
os.environ["USER_AGENT"] = "LenoxAI/1.0"


from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from documents.documents import ChartAnalyzer
from lenox import Lenox  # Ensure this imports the updated lenox.py
from prompts import PromptEngine, PromptEngineConfig
from tool_imports import import_tools
import whisper
from dashboards.dashboard import create_dashboard
from code_interpreter import generate_visualization_response_sync
from gpt_research_tools import GPTResearchManager
import base64
import os
from lenox_opinion import generate_lenox_opinion





# Load environment variables
load_dotenv()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
whisper_model = whisper.load_model("tiny")
openai_api_key = os.getenv('OPENAI_API_KEY')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_secret_key')
app.config['UPLOAD_FOLDER'] = '/Users/lenox27/LENOX/uploaded_documents'
socketio = SocketIO(app)

# Pass the `app` object to `create_dashboard` to integrate Dash
app = create_dashboard(app)

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

# Initialize GPTResearchManager
gpt_research_manager = GPTResearchManager()

chart_analyzer = ChartAnalyzer()



# Initialize Lenox with all necessary components
lenox = Lenox(tools=tools, chart_analyzer=chart_analyzer, prompt_engine=prompt_engine, openai_api_key=openai_api_key)  # Change this line

# Add this function
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/dashboard')
def dashboard_page():
    return redirect('/dashboard/')

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
    
    if not query:
        return jsonify({'error': 'Empty query.'}), 400

    # Corrected call to handle_gpt_research
    result = lenox.intent_detector.handle_gpt_research(user_query=query, report_type=report_type, report_source=report_source)
    return jsonify(result)



@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    audio_file = request.files.get('file')
    if not audio_file:
        return jsonify({'error': 'No file provided'}), 400

    try:
        # Save the file temporarily
        temp_filename = 'temp_audio.webm'
        audio_file.save(temp_filename)
        
        # Use whisper to transcribe
        result = whisper_model.transcribe(temp_filename)
        text = result['text']
        
        # Remove the temporary file
        os.remove(temp_filename)
        
        return jsonify({
            'transcription': text,
            'language': 'en'
        })
    except Exception as e:
        app.logger.error(f"Error processing audio: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500



@app.route('/upload', methods=['POST'])
def upload_document():
    data = request.get_json()
    if 'file_content' not in data:
        return jsonify({'error': 'No file content in the request'}), 400

    file_content = data['file_content']
    additional_input = data.get('additional_input', '')

    try:
        # Decode the file content
        decoded_content = base64.b64decode(file_content)
        
        # Perform chart analysis
        analysis = chart_analyzer.analyze_chart(decoded_content)
        
        # Generate Lenox opinion
        lenox_opinion_result = generate_lenox_opinion(analysis, additional_input, lenox)
        
        # Return the combined opinion and recommendation
        return jsonify({
            'message': 'Chart successfully analyzed.',
            'analysis': analysis,
            'lenox_opinion': lenox_opinion_result['lenox_opinion'],
            'hold_or_sell': lenox_opinion_result['hold_or_sell'],
            'buy_or_wait': lenox_opinion_result['buy_or_wait']
        }), 200
    except Exception as e:
        app.logger.error(f"Error processing file: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500







@app.route('/synthesize', methods=['POST'])
def synthesize_speech():
    data = request.get_json()
    input_text = data.get('input')
    voice = data.get('voice', 'onyx')
    tts_model = data.get('model', 'tts-1-hd')  # Avoid shadowing `model`

    if not input_text:
        return jsonify({'error': 'Input text is missing'}), 400

    try:
        audio_path = lenox.synthesize_text(tts_model, input_text, voice)
        if audio_path:
            directory = os.path.dirname(audio_path)
            filename = os.path.basename(audio_path)
            return send_from_directory(directory=directory, path=filename, as_attachment=True)
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        query = data.get('query', '').lower()

        if not query:
            app.logger.debug("No query provided in the request.")
            return jsonify({'error': 'Empty query.'}), 400

        app.logger.debug("Starting to process query with convchain.")
        result = lenox.convchain(query, session['session_id'])
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


@app.route('/feedback', methods=['POST'])
def handle_feedback():
    feedback_data = request.get_json()
    if 'query' not in feedback_data or 'feedback' not in feedback_data:
        return jsonify({'error': 'Missing necessary feedback data.'}), 400

    query = feedback_data['query']
    feedback = feedback_data['feedback']
    session_id = session.get('session_id', 'default_session')

    try:
        # Store feedback in database
        lenox.teach_from_feedback(query, feedback, session_id)
        
        # Process feedback in real-time (if implemented)
        response = lenox.process_feedback(feedback, query, session_id)  # Add query here
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback processed successfully.',
            'response': response,
            'feedbackType': feedback
        })
    except Exception as e:
        app.logger.error(f"Error processing feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/create_visualization', methods=['POST'])
def create_visualization():
    data = request.get_json()
    query = data.get('query', '').strip()

    if not query:
        app.logger.error("No query provided for visualization.")
        return jsonify({"status": "error", "error": "No query provided."}), 400

    try:
        app.logger.debug(f"Received query for visualization: {query}")
        result = generate_visualization_response_sync(query)
        app.logger.debug(f"Generated visualization result: {result}")
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"status": "error", "error": "An unexpected error occurred."}), 500




@socketio.on('connect')
def on_connect():
    emit('status', {'data': 'Connected to real-time updates'})

@socketio.on('send_feedback')
def on_feedback(data):
    query = data.get('query', '')  # Add this line to get the query
    feedback = data['feedback']
    session_id = session['session_id']
    response = lenox.process_feedback(feedback, query, session_id)  # Add query and session_id
    emit('feedback_response', {'message': 'Feedback processed', 'data': response})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=bool(os.getenv('FLASK_DEBUG')))