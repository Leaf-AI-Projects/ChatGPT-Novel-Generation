import threading

from flask import request, jsonify, send_from_directory, send_file

from models.story_pdf import StoryPDF

from features.story_creator_v0 import StoryCreator as SC0
from features.story_creator_v1 import StoryCreator as SC1

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

        data = request.json
        title = data['title']
        api_key = data['api_key']
        chatgpt_model = 'gpt-4o-mini'
        version = data['version']

        if version == 'v0':
            story_creator = SC0(progress_data=progress_data)
        elif version == 'v1':
            story_creator = SC1(progress_data=progress_data)
        else:
            story_creator = SC0(progress_data=progress_data)

        # if 'outline' in data:
        #     outline_data = data['outline']
        #     tree = parse_to_tree(outline_data)
        #     endpoints = concatenate_endpoints(outline_data)
        #     threading.Thread(target=story_creator.process_outline, args=(title, outline_data, chatgpt_model, api_key)).start()
        if 'summary' in data:
            summary_data = data['summary']
            threading.Thread(target=story_creator.process_summary, args=(title, summary_data, chatgpt_model, api_key)).start()
        else:
            return jsonify({'message': 'Type of format not specified. Expected outline or summary.'}), 400

        return jsonify({'message': 'Processing started successfully'}), 200

    @app.route('/progress')
    def progress():
        print(progress_data)
        return jsonify(progress_data)

    # Flask route to create and serve PDF
    @app.route('/create-pdf', methods=['POST'])
    def pdf_route():
        data = request.json
        print(data)

        story_pdf = StoryPDF(data['text'], data['title'])
        pdf_full_path = story_pdf.create()

        # Send the PDF file directly to the client for download
        return send_file(pdf_full_path, as_attachment=True)