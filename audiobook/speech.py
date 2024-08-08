from google.cloud import texttospeech
import os
import re
from pydub import AudioSegment
import yaml
import time
import json
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler("speech.log"), logging.StreamHandler(sys.stdout)], level=logging.INFO)


def load_completed_files():
    try:
        with open('completed_chapters.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_completed_files(completed_files):
    with open('completed_chapters.json', 'w') as f:
        json.dump(completed_files, f)


def clean_text(text):
    # Replace fancy quotes and other non-standard apostrophes or quotes with standard ones
    text = text.replace('“', '"').replace('”', '"').replace(
        "‘", "'").replace("’", "'").replace('—', '-')

    # Remove Unicode spaces and other non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    return text


# Load the service account credentials from the JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "your-private-key-generated-on-google.json"


def create_chapter_directory(chapter_index, output_folder):
    mp3_directory = f'{output_folder}/chapter_{chapter_index}'
    os.makedirs(mp3_directory, exist_ok=True)
    return mp3_directory


def get_completed_files(mp3_directory):
    return sorted([f for f in os.listdir(mp3_directory) if f.endswith('.mp3')])


def synthesize_and_save_text(text, chapter_index, output_folder, i, mp3):
    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        name="en-US-Journey-O",  # Use a specific voice name
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3)

    for attempt in range(5):
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config

            )
            with open(mp3, "wb") as out:
                out.write(response.audio_content)
            logger.info(f"OK '{
                mp3}' (Attempt {attempt+1})")
            return
        except Exception as e:
            logger.error(f"Error synthesizing text (Attempt {attempt+1}): {e}")
            time.sleep(3)
            if attempt == 4:
                raise  # Re-raise on the last attempt


def concatenate_audio(mp3_directory, output_folder, chapter_index):
    output_file_path = f'{output_folder}/chapter_{chapter_index}.mp3'
    if os.path.exists(output_file_path):
        logger.debug(f'skip {output_file_path} because it already exists')
        return
    mp3_files = get_completed_files(mp3_directory)
    if len(mp3_files) == 0:
        return
    combined = AudioSegment.empty()
    for mp3_file in mp3_files:
        current_track = AudioSegment.from_mp3(
            os.path.join(mp3_directory, mp3_file))
        combined += current_track
    combined.export(output_file_path, format="mp3")
    logger.info(f"Merged {output_file_path}")


def main():
    with open('data.yml', 'r', encoding='utf-8') as stream:
        data = yaml.safe_load(stream)

    output_folder = 'temp_output'
    completed_files = load_completed_files()

    # while True:
    for chapter in data['chapter']:
        chapter_index = chapter['chapter_index']
        texts = chapter['paragraphs']
        mp3_directory = create_chapter_directory(
            chapter_index, output_folder)

        succeeded = True
        # sort text by index
        i = ''
        texts = sorted(texts, key=lambda x: x['index'])
        for c in texts:
            i = c['index']
            # Check if chapter already completed based on files
            mp3 = os.path.join(mp3_directory, f"{i}.mp3")
            if i in completed_files and os.path.exists(mp3):
                logger.debug(
                    f"paragraph {i} already completed, skipping...")
                continue
            text = clean_text(c['text'])
            try:
                synthesize_and_save_text(
                    text, chapter_index, output_folder, i, mp3)
                completed_files[i] = True
                save_completed_files(completed_files)
            except Exception as e:
                logger.error(f"Failed to process paragraph {i}: {e}")
                succeeded = False
                break  # Break out of the inner loop for this chapter

        if not succeeded:
            logger.error(f'failed at chapter_{chapter_index}->paragraph_{i}')
            break
        concatenate_audio(mp3_directory, output_folder, chapter_index)

        # time.sleep(60)  # Sleep for 60 seconds before checking again


if __name__ == "__main__":
    logger.info('start')
    main()
