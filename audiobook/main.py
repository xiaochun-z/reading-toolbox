from google.cloud import texttospeech
import os
import re
from pydub import AudioSegment


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
ssml_text = '''
<speak>
  <voice name="en-US-Standard-A">
    <prosody rate="x-slow" pitch="high">
CHAPTER SEVEN
    </prosody>
    <prosody rate="medium" pitch="medium">
That's a great question! The Google Cloud Speech-to-Text API has limits on the amount of text you can pass in a single request. Here's the breakdown.
    </prosody>
  </voice>
</speak>
'''
texts = ['''
For Text-to-Speech (Synthesizing Speech):
''',
         '''
Studio Voices: As of October 24, 2023, Studio voices (high-quality, expressive voices) support up to 5,000 bytes of text or SSML input per synthesis request. This is roughly equivalent to a few paragraphs of text.
''',
         '''
For Speech-to-Text (Transcribing Audio):
Synchronous Requests: For synchronous requests (where you get the transcribed text immediately), the limit is 10 MB or 1 minute of audio duration , whichever is reached first.
Streaming Requests: For streaming requests (where you send audio in real-time), each request in the stream is limited to 25 KB of audio. A stream can remain open for up to 5 minutes .
'''
         ]

client = texttospeech.TextToSpeechClient()

for i, text in enumerate(texts):
    text = clean_text(text)
    # Set the text input to be synthesized
    # synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
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
    with open(f"output_{i}.mp3", "wb") as out:
        out.write(response.audio_content)
    print(f"Audio content written to file 'output_{i}.mp3'")

mp3_directory = '.'
mp3_files = sorted([f for f in os.listdir(
    mp3_directory) if f.endswith('.mp3')])
combined = AudioSegment.empty()
for mp3_file in mp3_files:
    current_track = AudioSegment.from_mp3(
        os.path.join(mp3_directory, mp3_file))
    combined += current_track
output_file_path = 'output.mp3'
combined.export(output_file_path, format="mp3")
print(f"The concatenated MP3 has been saved to {output_file_path}")
