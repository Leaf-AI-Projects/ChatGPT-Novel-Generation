import os
import traceback
import threading

from flask import request, jsonify, send_from_directory, send_file

from models.story_pdf import StoryPDF

from features.story_creator_v0 import StoryCreator as SC0
from features.story_creator_v1 import StoryCreator as SC1
from features.story_creator_v2 import StoryCreator as SC2

progress_data = {}

def configure_routes(app):

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return send_from_directory('.', 'index.html')
        
    @app.route('/novel-gen', methods=['POST'])
    def submit_book_writer_form():
        progress_data['complete'] = False
        progress_data['fail'] = False
        progress_data['fail_message'] = ''
        progress_data['meta_text'] = ''

        data = request.json
        title = data['title']
        api_key = data['api_key']
        chatgpt_model = data['bulk_model']
        version = data['version']

        if version == 'v0':
            story_creator = SC0(progress_data=progress_data)
        elif version == 'v1':
            story_creator = SC1(progress_data=progress_data, api_key=api_key, testing=app.config.get('TESTING'))
        elif version == 'v2':
            story_creator = SC2(progress_data=progress_data, api_key=api_key, testing=app.config.get('TESTING'))
        else:
            story_creator = SC2(progress_data=progress_data, api_key=api_key, testing=app.config.get('TESTING'))

        if 'summary' in data:
            summary_data = data['summary']
            threading.Thread(target=story_creator.process_summary, args=(title, summary_data, chatgpt_model)).start()
        else:
            return jsonify({'message': 'Type of format not specified. Expected outline or summary.'}), 400

        return jsonify({'message': 'Processing started successfully'}), 200

    @app.route('/progress')
    def progress():
        temp_progress_data = progress_data.copy()

        if 'text' in temp_progress_data:
            temp_progress_data['text'] = ''

        return jsonify(progress_data)

    @app.route('/create-pdf', methods=['POST'])
    def pdf_route():
        data = request.json

        try:
            story_pdf = StoryPDF()

            pdf_full_path = story_pdf.create(title=data['title'], chapters=data['chapters'])

            if not pdf_full_path:
                raise ValueError("PDF file path is invalid or empty")

            return send_file(pdf_full_path, as_attachment=True)

        except Exception as e:
            # Log the exception with traceback
            print("An error occurred while generating the PDF.")

            # Update progress_data in case of failure (if needed)
            progress_data['fail'] = True
            progress_data['fail_message'] = traceback.format_exc()

            # Return a JSON response with error information and a 500 status code
            return jsonify({'error': 'Failed to generate PDF', 'message': str(e)}), 500