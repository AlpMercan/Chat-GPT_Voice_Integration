from openai import OpenAI
from utils import record_audio, play_audio
from fuzzywuzzy import fuzz  # for siri part
import os
import tempfile
import time

api_key = "Enter-Your_key"
client = OpenAI(api_key=api_key)
conversation_active = False
keyword_activate = "hey siri"  # The keyword to trigger the loop
initial_threshold = (
    70  # Threshold for fuzzy matching,speech recognition is not that good
)
messages = []
silence_start_time = None
silence_duration = 10  # Silence duration in seconds to deactivate the conversation
greeting_message = "."

while True:
    record_audio("test.wav")

    audio_file = open("test.wav", "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    transcription_text = transcription.text.lower().strip()
    print(transcription_text)

    if not transcription_text:
        print("Sizi duyamadım. Lütfen bir şeyler söyleyin.")
        if conversation_active:
            if silence_start_time is None:
                silence_start_time = time.time()  # Start the silence timer
            elif time.time() - silence_start_time >= silence_duration:
                print("10 seconds and no comemnt. I am ending the talk")
                conversation_active = False  # Deactivate conversation
                messages = []  # Clear messages for a fresh start next time
                silence_start_time = None  # Reset the silence timer
        continue

    silence_start_time = None  # Reset the silence timer on any input

    if (
        not conversation_active
        and fuzz.ratio(keyword_activate, transcription_text) >= initial_threshold
    ):
        conversation_active = True  # Activate conversation
        initial_message = {
            "role": "system",
            "content": "Enter the description to here",
        }
        messages = [initial_message, {"role": "user", "content": transcription_text}]

        # Play the greeting message only once
        print(greeting_message)
        response_audio = client.audio.speech.create(
            model="tts-1", voice="nova", input=greeting_message
        )
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file_path = temp_file.name
                response_audio.stream_to_file(temp_file_path)

            play_audio(temp_file_path)

            # Clean up the temporary file after playing the audio
            os.remove(temp_file_path)
        except PermissionError:
            print("Permission Denied. I can not record and play the sound file.")
        except Exception as e:
            print(f"An error occured: {e}")

        # Append the greeting message to the conversation
        messages.append({"role": "assistant", "content": greeting_message})

    elif conversation_active:
        messages.append({"role": "user", "content": transcription_text})

    if (
        conversation_active
        and transcription_text
        and not transcription_text == greeting_message.lower()
    ):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        reply_text = response.choices[0].message.content
        print(reply_text)

        response_audio = client.audio.speech.create(
            model="tts-1", voice="nova", input=reply_text
        )

        # Use a temporary file to avoid permission issues
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file_path = temp_file.name
                response_audio.stream_to_file(temp_file_path)

            play_audio(temp_file_path)

            # Clean up the temporary file after playing the audio
            os.remove(temp_file_path)
        except PermissionError:
            print("Permission Denied. I can not record and play the sound file.")
        except Exception as e:
            print(f"An error occured: {e}")

        # Add the assistant's reply to the messages to maintain context
        messages.append({"role": "assistant", "content": reply_text})
