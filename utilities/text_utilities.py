import tiktoken
import re

class TextUtilities():
    @staticmethod
    def tokenCount(string, encoding_name='cl100k_base'):
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    @staticmethod
    def segmentText(text, max_length):
        segments = []
        start_index = 0

        while start_index < len(text):
            # Determine the end index for this segment
            end_index = min(start_index + max_length, len(text))
            
            # Find the position of the last period before or at the end index
            period_index = text.rfind('.', start_index, end_index)

            # If no period is found, extend to the next period
            if period_index == -1 or period_index < start_index:
                period_index = text.find('.', end_index)
                if period_index == -1:  # If there's no more periods in the text
                    period_index = len(text) - 1

            # Extract the segment and add to the list
            segment = text[start_index:period_index + 1].strip()
            segments.append(segment)

            # Update the start index for the next segment
            start_index = period_index + 1

        return segments
    
    @staticmethod
    def splitStringsEvenlyByParagraphs(original_strings):
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
    
    @staticmethod
    def splitParagraphs(paragraphs):
        # Split the text into sentences using a regular expression that matches sentence-ending punctuation.
        sentences = re.split(r'(?<=[.!?])\s+', paragraphs.strip())
        
        # Determine the halfway point based on the number of sentences
        total_sentences = len(sentences)
        halfway_index = total_sentences // 2

        # Rebuild the first and second halves
        first_half = ' '.join(sentences[:halfway_index]).strip()
        second_half = ' '.join(sentences[halfway_index:]).strip()

        return first_half, second_half
    
    @staticmethod
    def getChapterTextUntilMarker(chapter_string):
        # Find the index of the "^^^" marker
        end_index = chapter_string.find('^^^')
        
        # If the marker is found, return all text up to that point
        if end_index != -1:
            return chapter_string[:end_index].strip()
        
        # If the marker is not found, return the whole string
        return chapter_string.strip()