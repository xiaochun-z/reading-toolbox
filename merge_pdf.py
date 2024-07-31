import os
from PyPDF2 import PdfReader, PdfWriter
import argparse

def merge_pdfs(folder_path, output_pdf_path):
    # Create a PdfWriter object for the output PDF
    pdf_writer = PdfWriter()

    # List all the PDF files in the specified folder
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    pdf_files.sort()  # Sort the files to maintain order

    # Loop through all PDF files and add them to the PdfWriter
    for pdf_file in pdf_files:
        pdf_reader = PdfReader(os.path.join(folder_path, pdf_file))
        for page in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page])

    # Write the merged PDF to a file
    with open(output_pdf_path, 'wb') as output_pdf_file:
        pdf_writer.write(output_pdf_file)

    print(f"Merged PDF saved as: {output_pdf_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge multiple PDF files into a single PDF file.")
    parser.add_argument("src_folder", type=str, help="Folder to contain pdf file to merge")
    parser.add_argument("output_pdf", type=str, help="the output PDF file")

    args = parser.parse_args()

    merge_pdfs(args.src_folder, args.output_pdf)
