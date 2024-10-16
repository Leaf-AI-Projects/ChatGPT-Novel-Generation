import re
import time
import requests
import traceback
import threading
from threading import Thread, Lock

from utilities.text_utilities import TextUtilities
from utilities.outline_node import OutlineNode
import utilities.prompt_templates as pt


class StoryCreator:
    def __init__(self, progress_data, api_key):
        self.progress_data = progress_data
        self.api_key = api_key

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
                first_half, last_chapter_text = self.split_paragraphs(last_chapter_text)
            last_chapter_text = self.write_text(
                prompt_vars, chatgpt_model, write_chapter_type,
                det_chap=detailed_chap, prev_sec=last_chapter_text
            )
            chapter_text += last_chapter_text

            # Update progress_data['current'] in a thread-safe manner
            with lock:
                progress_data['current'] += 1

            chapter_index += 1

        chapter_text = self.get_chapter_text_until_marker(chapter_text)

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

        create_summary_type = 'create_summary' if summary != '' else 'create_summary_from_scratch'

        prompt_vars['summary'] = self.write_text(prompt_vars, 'gpt-4o', create_summary_type)
        self.progress_data['current'] += 1

        # # Store final text in progress
        # self.progress_data['text'] = ''.join(prompt_vars['summary'])
        # self.progress_data['complete'] = True

        # return 1

        prompt_vars['characters'] = self.write_text(prompt_vars, 'gpt-4o', 'create_characters')
        self.progress_data['current'] += 1

        prompt_vars['themes_and_conflicts'] = self.write_text(prompt_vars, 'gpt-4o', 'create_themes_and_conflicts')
        self.progress_data['current'] += 1

        retry_count = 0
        max_retries = 5
        chapter_list = []
        
        # Retry up to max_retries if "Chapter" is not found
        while retry_count < max_retries:
            # Call the text generation method
            chapters = self.write_text(prompt_vars, 'gpt-4o', 'create_chapters')

            # Split the string at each "Chapter X"
            pattern = r'(?=Chapter \d+)'  # Lookahead for 'Chapter ' followed by one or more digits
            chapter_list = re.split(pattern, chapters)

            # Filter out any empty strings that might result from the split
            chapter_list = [chap for chap in chapter_list if chap.strip()]

            # Check if any part contains "Chapter"
            if any("Chapter" in chap for chap in chapter_list):
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
        with open("example.txt", "w", encoding='utf-8') as file:
            file.write(self.progress_data['text'])
        self.progress_data['complete'] = True

    def write_text(self, prompt_vars, chatgpt_model, prompt_type, chap=None, det_chap=None, prev_sec=None):
        temp_prompt_vars = prompt_vars.copy()
        if chap:
            temp_prompt_vars['chapter'] = chap
        if det_chap:
            temp_prompt_vars['detailed_chapter'] = det_chap
        if prev_sec:
            temp_prompt_vars['previous_section'] = prev_sec

        instruction = pt.summary_template_v0010[prompt_type].format(**temp_prompt_vars)

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
        
    def split_strings_evenly_by_paragraphs(self, original_strings):
        new_list = []

        for s in original_strings:
            # Split the string into paragraphs
            paragraphs = s.split('\n\n')
            
            # Find the split point
            split_point = len(paragraphs) // 2 + len(paragraphs) % 2  # Ensure first half is equal or larger
            
            # Split the paragraphs into two halves
            first_half = '\n\n'.join(paragraphs[:split_point])
            second_half = '\n\n'.join(paragraphs[split_point:])
            
            # Add the halves to the new list
            new_list.extend([first_half, second_half])

        return new_list
    
    def split_paragraphs(self, paragraphs):
        # Split the text into sentences using a regular expression that matches sentence-ending punctuation.
        sentences = re.split(r'(?<=[.!?])\s+', paragraphs.strip())
        
        # Determine the halfway point based on the number of sentences
        total_sentences = len(sentences)
        halfway_index = total_sentences // 2

        # Rebuild the first and second halves
        first_half = ' '.join(sentences[:halfway_index]).strip()
        second_half = ' '.join(sentences[halfway_index:]).strip()

        return first_half, second_half
    
    def get_chapter_text_until_marker(self, chapter_string):
        # Find the index of the "^^^" marker
        end_index = chapter_string.find('^^^')
        
        # If the marker is found, return all text up to that point
        if end_index != -1:
            return chapter_string[:end_index].strip()
        
        # If the marker is not found, return the whole string
        return chapter_string.strip()