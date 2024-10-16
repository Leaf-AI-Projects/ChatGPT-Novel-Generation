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
        self.PAGE_WIDTH = 210 - 2 * self.MARGIN  # A4 width in mm (210mm - margins)
        self.PAGE_HEIGHT = 297  # A4 height in mm
        self.TITLE_FONT = 'Times'  # Use a built-in font like Times
        self.TITLE_FONT_SIZE = 24  # Font size for title
        self.BODY_FONT = 'Times'  # Use the same font for body text
        self.BODY_FONT_SIZE = 12  # Font size for body text
        self.INDENT = 10  # Indentation for paragraphs in mm
        self.LINE_HEIGHT = 8  # Line height for body text in mm
        self.PDF_DIR = '/tmp/transformed_books'  # Directory for saving PDFs

    def sanitizeText(self, text):
        """
        Remove any characters that are not part of the Latin-1 character set.
        """
        return text.encode('latin-1', 'ignore').decode('latin-1')

    def create(self, title, text):
        self.title = title
        self.text = self.sanitizeText(text)

        pdf = FPDF()

        # Use built-in fonts (no need for external font files)
        pdf.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)
        pdf.add_page()

        # Set font for the title
        pdf.set_font(self.TITLE_FONT, 'B', self.TITLE_FONT_SIZE)  # Use built-in Times font
        title_w = pdf.get_string_width(self.title) + 6
        title_x = (self.PAGE_WIDTH - title_w) / 2 + self.MARGIN
        title_y = (self.PAGE_HEIGHT - self.INDENT) / 4

        pdf.set_xy(title_x, title_y)
        pdf.cell(title_w, self.INDENT, self.title, 0, 1, 'C')

        pdf.add_page()
        pdf.set_font(self.BODY_FONT, '', self.BODY_FONT_SIZE)

        # Process each paragraph for indentation
        indent = self.INDENT
        line_height = self.LINE_HEIGHT
        paragraphs = self.text.split('\n')

        for paragraph in paragraphs:
            if paragraph.strip():
                pdf.set_x(pdf.l_margin + indent)
                pdf.multi_cell(0, line_height, paragraph)
            else:
                pdf.ln(line_height)  # Add a blank line for paragraph spacing

        # Define a directory for PDFs
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
