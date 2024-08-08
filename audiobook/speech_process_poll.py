from google.cloud import texttospeech
import os
import re
from pydub import AudioSegment
import yaml
import time
import json
import multiprocessing

stop = False

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


def synthesize_and_save_text(text, chapter_index, output_folder, i, mp3_directory):
    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        name="en-US-Journey-O",  # Use a specific voice name
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3)

    for attempt in range(1):
        try:
            if stop:
                break
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config

            )
            sub_file = os.path.join(mp3_directory, f"{i}.mp3")
            with open(sub_file, "wb") as out:
                out.write(response.audio_content)
            print(f"Audio content written to file '{sub_file}' (Attempt {attempt+1})")
            return
        except Exception as e:
            print(f"Error synthesizing text (Attempt {attempt+1}): {e}")
            if attempt == 0:
                raise
            time.sleep(3)


def concatenate_audio(mp3_directory, output_folder, chapter_index):
    output_file_path = f'{output_folder}/chapter_{chapter_index}.mp3'
    if os.path.exists(output_file_path):
        print(f'skip {output_file_path} because it already exists')
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
    print(f"The concatenated MP3 has been saved to {output_file_path}")


def process_text(text, chapter_index, output_folder, i, mp3_directory):
    try:
        synthesize_and_save_text(
            text, chapter_index, output_folder, i, mp3_directory)
        return chapter_index, i
    except Exception as e:
        print(f"Failed to process paragraph {i}: {e}")
        stop = True


def main():
    stop = False
    with open('data.yml', 'r', encoding='utf-8') as stream:
        data = yaml.safe_load(stream)

    output_folder = 'temp_output'
    completed_files = load_completed_files()

    for chapter in data['chapter']:
        if stop:
            break
        chapter_index = chapter['chapter_index']
        texts = chapter['paragraphs']
        mp3_directory = create_chapter_directory(chapter_index, output_folder)

        try:
            with multiprocessing.Pool(processes=3) as pool:
                results = pool.starmap(
                    process_text,
                    [(clean_text(c['text']), chapter_index, output_folder, c['index'], mp3_directory)
                        for c in texts if c['index'] not in completed_files]
                )
            for result in results:
                if result is not None:
                    completed_files[result[1]] = True
                    print(f'finished {result[0]}->{result[1]}')

            save_completed_files(completed_files)

            concatenate_audio(mp3_directory, output_folder, chapter_index)
        except KeyboardInterrupt:
            print('interrupt received. Terminating pool...')
            stop = True
            pool.terminate()
            break


if __name__ == "__main__":
    main()
