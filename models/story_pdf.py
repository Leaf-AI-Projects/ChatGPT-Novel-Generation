import os
import datetime

from werkzeug.utils import secure_filename
from fpdf import FPDF

class StoryPDF:
    def __init__(self):
        self.title = ''
        self.text = ''

        # Define constants for PDF creation
        self.MARGIN = 20  # Margin in mm
        self.PAGE_WIDTH = 170  # Standard A4 width in mm
        self.PAGE_HEIGHT = 297  # Standard A4 height in mm
        self.TITLE_FONT = 'Times'
        self.TITLE_FONT_SIZE = 24  # Font size for title
        self.BODY_FONT = 'Times'
        self.BODY_FONT_SIZE = 12  # Font size for body text
        self.INDENT = 10  # Indentation for paragraphs in mm
        self.LINE_HEIGHT = 8  # Line height for body text in mm
        self.PDF_DIR = '/tmp/transformed_books'  # Directory for saving PDFs

    def sanitizeText(self, text):
        # Replace specific non-Latin-1 characters with their Latin-1 equivalents or remove them
        replacements = {
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '--',  # Em dash
            '\u2026': '...',  # Ellipsis
            '*': '',
            '#': ''
        }
        
        for old_char, new_char in replacements.items():
            text = text.replace(old_char, new_char)
        
        return text

    def create(self, title, chapters):
        self.title = title

        pdf = PDFWithPageNumbers()

        pdf.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)
        pdf.add_page()

        # Set font for the title
        pdf.set_font(self.TITLE_FONT, 'B', self.TITLE_FONT_SIZE)
        pdf_w = self.PAGE_WIDTH
        title_w = pdf.get_string_width(self.title) + 6
        title_x = (pdf_w - title_w) / 2 + self.MARGIN
        title_y = (self.PAGE_HEIGHT - self.INDENT) / 4

        pdf.set_xy(title_x, title_y)
        pdf.cell(title_w, self.INDENT, self.title, 0, 1, 'C')

        # Add a blank page for TOC
        pdf.add_page()

        pdf.set_font(self.BODY_FONT, size=self.BODY_FONT_SIZE)

        indent = self.INDENT
        line_height = self.LINE_HEIGHT

        toc_entries = []

        for idx, chapter in enumerate(chapters):
            # Add a new page for the chapter
            pdf.add_page()

            pdf.set_font(self.BODY_FONT, 'B', self.BODY_FONT_SIZE * 2)

            text = self.sanitizeText(chapter)
            paragraphs = text.split('\n')

            # Record the chapter title and starting page number
            chapter_title = paragraphs[0].strip()
            chapter_page_no = pdf.page_no() + 1  # Since we'll add a new page
            toc_entries.append((chapter_title, chapter_page_no))

            for paragraph in paragraphs: 
                paragraph = paragraph.strip()
                if paragraph:
                    pdf.set_x(pdf.l_margin + indent)
                    pdf.multi_cell(0, line_height, paragraph)
                else:
                    pdf.ln(6)
                pdf.set_font(self.BODY_FONT, size=self.BODY_FONT_SIZE)


        last_page = pdf.page_no()

        # After processing all chapters, go back to TOC page
        pdf.page = 2  # Corrected from pdf.set_page(2)
        pdf.set_y(self.MARGIN)

        # Write TOC title
        pdf.set_font(self.TITLE_FONT, 'B', self.TITLE_FONT_SIZE)
        pdf.cell(0, self.LINE_HEIGHT, 'Table of Contents', ln=1, align='C')
        pdf.ln(10)

        # Set font for TOC entries
        pdf.set_font(self.BODY_FONT, size=self.BODY_FONT_SIZE)

        # Write TOC entries with dot leaders
        for chapter_title, page_no in toc_entries:
            page_num_str = str(page_no - 2)  # Adjust page number
            pdf.set_font(self.BODY_FONT, size=self.BODY_FONT_SIZE)
            
            # Calculate widths
            title_width = pdf.get_string_width(chapter_title) + 2  # Add some padding
            page_num_width = pdf.get_string_width(page_num_str) + 2  # Add some padding
            total_width = pdf.w - pdf.l_margin - pdf.r_margin
            dots_width = total_width - (title_width + page_num_width)
            
            # Ensure dots_width is not negative
            if dots_width < 0:
                dots_width = 0
            
            # Number of dots
            dot_char_width = pdf.get_string_width('.')
            num_dots = int(dots_width / dot_char_width)
            dots = '.' * num_dots
            
            # Write chapter title
            pdf.cell(title_width, line_height, chapter_title, ln=0)
            
            # Write dots
            pdf.cell(dots_width, line_height, dots, ln=0)
            
            # Write page number
            pdf.cell(page_num_width, line_height, page_num_str, ln=1, align='R')


        # After writing the TOC, proceed to the last page
        pdf.page = last_page  # Corrected from pdf.set_page(pdf.page_no())

        # Define a temporary directory within /tmp for PDFs
        pdf_directory = self.PDF_DIR

        # Check if the directory exists, and create it if it doesn't
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)

        # Secure the title and replace spaces with underscores
        safe_title = secure_filename(self.title).replace(' ', '_')

        # Generate a timestamp string
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Append the timestamp to the safe_title
        safe_title = f"{safe_title}_{timestamp}.pdf"

        pdf_full_path = os.path.join(pdf_directory, safe_title)

        # Save the PDF file
        pdf.output(pdf_full_path)

        return pdf_full_path

class PDFWithPageNumbers(FPDF):
    def footer(self):
        if self.page_no() > 2:  # Skip numbering on the title page and TOC page
            # Position at 15 mm from bottom
            self.set_y(-15)
            # Set font
            self.set_font('Arial', 'I', 8)
            # Page number
            page_num = f'{self.page_no() - 2}'  # Subtract 2 for title and TOC pages
            # Adjust x position to be at bottom right
            self.cell(0, 10, page_num, 0, 0, 'R')