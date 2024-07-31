import os
from PyPDF2 import PdfReader, PdfWriter
import argparse

def split_pdf(input_pdf_path, output_folder, pages_per_split):
    # Ensure the output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Open the input PDF
    with open(input_pdf_path, 'rb') as input_pdf_file:
        pdf_reader = PdfReader(input_pdf_file)
        total_pages = len(pdf_reader.pages)
        split_start = 0
        base_name = os.path.basename(input_pdf_path)
        file_name_without_ext = os.path.splitext(base_name)[0]

        # Loop through the PDF and split it into chunks
        while split_start < total_pages:
            pdf_writer = PdfWriter()
            split_end = min(split_start + pages_per_split, total_pages)

            for page in range(split_start, split_end):
                pdf_writer.add_page(pdf_reader.pages[page])

            # Define the output PDF path
            output_pdf_path = os.path.join(output_folder, f'{file_name_without_ext}_{split_start + 1}_to_{split_end}.pdf')

            # Write the split PDF to a file
            with open(output_pdf_path, 'wb') as output_pdf_file:
                pdf_writer.write(output_pdf_file)

            print(f"Created: {output_pdf_path}")
            split_start += pages_per_split

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split a single PDF file into serval smaller PDF files.")
    parser.add_argument("input_pdf", type=str, help="the input PDF file")
    parser.add_argument("folder", type=str, help="Folder to store pdf files")
    parser.add_argument("pages", type=int, help="Number of pages per split")

    args = parser.parse_args()
    split_pdf(args.input_pdf, args.folder, args.pages)
