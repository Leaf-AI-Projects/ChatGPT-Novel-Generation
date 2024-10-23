import os
import re
import time
import requests
import traceback
from threading import Thread, Lock

import utilities.prompt_templates as pt
from utilities.text_utilities import TextUtilities as tu

class StoryCreator:
    def __init__(self, progress_data, api_key, testing=False):
        self.progress_data = progress_data
        self.api_key = api_key
        self.testing = testing

        self.TESTING_CHAP_DELIM = "[CHAPTER_DELIM]"

    def process_chapter(self, index, chap, prompt_vars, chatgpt_model, completed_chapters_list, progress_data, lock):
        detailed_chap = self.write_text(prompt_vars, chatgpt_model, 'create_chapter', chap=chap)

        # Update progress_data['current'] in a thread-safe manner
        with lock:
            progress_data['current'] += 1

        chapter_text = ''
        last_chapter_text = ''
        chapter_index = 0

        while '^^^' not in chapter_text:
            write_chapter_type = 'write_chapter' if chapter_index != 0 else 'write_first_chapter'
            if last_chapter_text != '':
                first_half, last_chapter_text = tu.splitParagraphs(last_chapter_text)
            last_chapter_text = self.write_text(
                prompt_vars, chatgpt_model, write_chapter_type,
                det_chap=detailed_chap, prev_sec=last_chapter_text
            )
            chapter_text += last_chapter_text

            # Update progress_data['current'] in a thread-safe manner
            with lock:
                progress_data['current'] += 1

            chapter_index += 1

        chapter_text = tu.getChapterTextUntilMarker(chapter_text)

        # Store the result in completed_chapters_list in a thread-safe manner
        with lock:
            completed_chapters_list[index] = chapter_text

    def process_summary(self, title, summary, chatgpt_model):
        self.progress_data['total'] = 100
        self.progress_data['current'] = 0

        prompt_vars = {
            'title': title,
            'user_summary': summary
        }
        
        if self.testing:
            # Check if self.testing is True and if an example novel exists in the assets folder
            example_novel_path = os.path.join('assets', 'example_novel.txt')
            if os.path.exists(example_novel_path):
                # Load the existing example novel and assign progress data fields
                with open(example_novel_path, 'r') as f:
                    example_novel = f.read()

                # Split the chapters using the unique delimiter
                chapter_list = example_novel.split(self.TESTING_CHAP_DELIM)
                chapter_list = [chap for chap in chapter_list if chap.strip()]  # Remove empty chapters if any

                # Skip generation, set the example novel as the generated text
                self.progress_data['text'] = example_novel
                self.progress_data['chapters'] = chapter_list
                self.progress_data['complete'] = True
                return

        # Continue with generation if example novel is not found or not in testing mode
        create_summary_type = 'create_summary' if summary != '' else 'create_summary_from_scratch'

        prompt_vars['summary'] = self.write_text(prompt_vars, 'gpt-4o', create_summary_type)
        self.progress_data['current'] += 1

        prompt_vars['author'] = self.write_text(prompt_vars, 'gpt-4o', 'create_author')
        self.progress_data['current'] += 1

        prompt_vars['characters'] = self.write_text(prompt_vars, 'gpt-4o', 'create_characters')
        self.progress_data['current'] += 1

        prompt_vars['themes_and_conflicts'] = self.write_text(prompt_vars, 'gpt-4o', 'create_themes_and_conflicts')
        self.progress_data['current'] += 1

        retry_count = 0
        max_retries = 5
        chapter_list = []

        # Retry up to max_retries if "Chapter" is not found
        while retry_count < max_retries:
            chapters = self.write_text(prompt_vars, 'gpt-4o', 'create_chapters')

            print(f'Chapters: {chapters}')

            # Split the string at each "Chapter X"
            pattern = r'(?=Chapter \d+)'  # Lookahead for 'Chapter ' followed by one or more digits
            chapter_list = re.split(pattern, chapters)

            # Filter out any empty strings that might result from the split
            chapter_list = [chap for chap in chapter_list if chap.strip()]

            # Check if any part contains "Chapter"
            if any("Chapter" in chap for chap in chapter_list):
                if self.testing:
                    chapter_list = chapter_list[:3]
                break
            else:
                if retry_count + 1 == max_retries:
                    self.progress_data['fail_message'] = 'Unable to create chapters.'
                    self.progress_data['fail'] = True
                    raise SystemExit
                else:
                    retry_count += 1
                    time.sleep(1)

        # Update progress
        self.progress_data['total'] = self.progress_data['current'] + (len(chapter_list) * 4) + 1
        self.progress_data['current'] += 1

        # Initialize the lock
        lock = Lock()

        # Initialize the list to store completed chapters
        completed_chapters_list = [''] * len(chapter_list)
        threads = []

        # Create and start a thread for each chapter
        for index, chap in enumerate(chapter_list):
            print(f'Chapter: {chap}')
            t = Thread(
                target=self.process_chapter,
                args=(index, chap, prompt_vars, chatgpt_model, completed_chapters_list, self.progress_data, lock)
            )
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Store final text in progress
        self.progress_data['text'] = ''.join(completed_chapters_list)
        self.progress_data['chapters'] = completed_chapters_list
        self.progress_data['complete'] = True

        # If testing mode is on, store the generated novel in the assets folder
        if self.testing:
            with open(example_novel_path, 'w') as f:
                f.write(self.TESTING_CHAP_DELIM.join(completed_chapters_list))

    def write_text(self, prompt_vars, chatgpt_model, prompt_type, chap=None, det_chap=None, prev_sec=None):
        temp_prompt_vars = prompt_vars.copy()
        if chap:
            temp_prompt_vars['chapter'] = chap
        if det_chap:
            temp_prompt_vars['detailed_chapter'] = det_chap
        if prev_sec:
            temp_prompt_vars['previous_section'] = prev_sec

        instruction = pt.summary_template_v0020[prompt_type].format(**temp_prompt_vars)

        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': 'Bearer ' + self.api_key,  # Added space after 'Bearer'
            'Content-Type': 'application/json'
        }
        data = {
            'model': chatgpt_model,
            'messages': [{'role': 'user', 'content': instruction}],
            'temperature': 1.0
        }

        try:
            response = requests.post(url, headers=headers, json=data).json()
            if 'choices' in response:
                return response['choices'][0]['message']['content']
            else:
                raise Exception(f'Invalid response from ChatGPT. Response: {response}')
        except Exception as e:
            self.progress_data['fail'] = True
            self.progress_data['fail_message'] = str(traceback.format_exc())
            raise SystemExit(e)