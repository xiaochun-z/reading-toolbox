import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from fpdf import FPDF
from PIL import Image
import threading
import signal

abort_event = threading.Event()


def process_image(image_path):
    im = Image.open(image_path)  # Open the image
    im = im.convert("L")  # Convert to grayscale
    im.save(image_path)  # Save the processed image
    return image_path


def create_single_pdf(pdf_index, imagelist_chunk, folder, name, page_width, page_height, ppi):
    file_name_without_ext = os.path.splitext(name)[0]
    merged_name = f'{file_name_without_ext}_{pdf_index:02d}.pdf'
    print(f'working on {merged_name}...')
    pdf = FPDF()
    count = 1

    for image in imagelist_chunk:
        if abort_event.is_set():
            return None
        pdf.add_page()
        im = Image.open(image)
        width, height = im.size

        # Calculate aspect ratio
        aspect_ratio = width / height

        # Determine new dimensions maintaining aspect ratio
        if aspect_ratio > 1:  # Landscape
            new_width = min(page_width, width * 25.4 / ppi)
            new_height = new_width / aspect_ratio
        else:  # Portrait
            new_height = min(page_height, height * 25.4 / ppi)
            new_width = new_height * aspect_ratio

        # Calculate position to center the image
        x = (page_width - new_width) / 2
        y = (page_height - new_height) / 2

        pdf.image(image, x, y, new_width, new_height)
        # print(f"\r{count}/{len(imagelist_chunk)} -> {name}_{pdf_index:02d}.pdf", end="", flush=True)
        count += 1

    output_path = os.path.join(folder, merged_name)
    pdf.output(output_path, "F")  # Save the PDF
    print(f"{merged_name} generated successfully!")
    return output_path


def create_pdf(folder, name, max_pages=-1):
    # Collect and sort image paths
    imagelist = [os.path.join(dirpath, filename)
                 for dirpath, _, filenames in os.walk(folder)
                 for filename in filenames if filename.endswith((".jpg", ".jpeg", ".png"))]
    imagelist.sort()

    if max_pages <= 0:
        max_pages = len(imagelist)

    # Rotate and convert images in parallel
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_image, img) for img in imagelist]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"Generated an exception: {exc}")

    imagelist_len = len(imagelist)
    print(f'Found {imagelist_len} image files. Converting to PDF...', flush=True)

    # A4 size in mm
    page_width, page_height, ppi = 210, 297, 97  # A4 size in mm + ppi

    # Split imagelist into chunks
    pdf_chunks = [imagelist[i:i + max_pages]
                  for i in range(0, imagelist_len, max_pages)]

    # Create PDFs in parallel
    with ThreadPoolExecutor() as executor:
        pdf_futures = [
            executor.submit(create_single_pdf, index + 1, chunk,
                            folder, name, page_width, page_height, ppi)
            for index, chunk in enumerate(pdf_chunks)
        ]
        for future in as_completed(pdf_futures):
            try:
                future.result()
            except Exception as exc:
                print(f"PDF generation exception: {exc}")
    executor.shutdown(wait=True)


def signal_handler(sig, frame):
    print("\nCtrl+C detected! Aborting...")
    abort_event.set()


if __name__ == "__main__":
    # Register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Convert a folder of JPG images to a PDF file.")
    parser.add_argument("folder", type=str,
                        help="Folder containing JPG images")
    parser.add_argument(
        "name", type=str, help="Base name of the output PDF file")
    parser.add_argument("--max_pages", type=int, default=-1,
                        help="Maximum number of pages per PDF file")

    args = parser.parse_args()
    create_pdf(args.folder, args.name, args.max_pages)
