from google.cloud import texttospeech
import os
import re
from pydub import AudioSegment
import yaml


def clean_text(text):
    # Replace fancy quotes and other non-standard apostrophes or quotes with standard ones
    text = text.replace('“', '"').replace('”', '"').replace(
        "‘", "'").replace("’", "'").replace('—', '-')

    # Remove Unicode spaces and other non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Optionally, add any additional cleaning rules here

    return text


# Load the service account credentials from the JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "your-private-key-generated-on-google.json"

with open('data.yml', 'r', encoding='utf-8') as stream:
    data = yaml.safe_load(stream)

client = texttospeech.TextToSpeechClient()

for chapter in data['chapter']:
    chapter_index = chapter['chapter_index']
    texts = chapter['paragraphs']
    output_folder = 'temp_output'
    mp3_directory = f'{output_folder}/chapter_{chapter_index}'
    os.makedirs(mp3_directory, exist_ok=True)

    # sort text by index
    texts = sorted(texts, key=lambda x: x['index'])
    for c in texts:
        i = c['index']
        text = clean_text(c['text'])
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request, selecting a specific voice
        voice = texttospeech.VoiceSelectionParams(
            name="en-US-Journey-O",  # Use a specific voice name
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3)

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # The response's audio_content is binary.
        # save to output_{i}.mp3
        sub_file = os.path.join(mp3_directory, f"{i}.mp3")
        with open(sub_file, "wb") as out:
            out.write(response.audio_content)
        print(f"Audio content written to file '{sub_file}'")

    mp3_files = sorted([f for f in os.listdir(
        mp3_directory) if f.endswith('.mp3')])
    combined = AudioSegment.empty()
    for mp3_file in mp3_files:
        current_track = AudioSegment.from_mp3(
            os.path.join(mp3_directory, mp3_file))
        combined += current_track
    output_file_path = f'{output_folder}/chapter_{chapter_index}.mp3'
    combined.export(output_file_path, format="mp3")
    print(f"The concatenated MP3 has been saved to {output_file_path}")
