import os
import openai
from pydub import AudioSegment
import math

CLIP_TEMP_FOLDER = os.path.abspath("temp_clips")
CLIP_FOLDER = os.path.abspath("curr_clips")
TEN_MINUTES = 10 * 60 * 1000
CHAR_TOKEN_RATIO = 1/4
MAX_TOKENS = 8000
TRANSCRIBED = True

#Add args to specify whether to reuse tempclips, reuse transcript etc to avoid reprocessing everyhthign
#Par

# Set up OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

total_clips = []

# Get voice clip
for clip in os.listdir(CLIP_FOLDER):
    total_clips.append(AudioSegment.from_file((os.path.join(CLIP_FOLDER,clip)), format="m4a"))


for clip in total_clips:

    curr_subclips = []

    #if > 10mins split
    curr = 0
    multiClips = False
    print(f"Current clip is {len(clip)/(1000*60)}minutes")
    if len(clip) > TEN_MINUTES:
        multiClips=True
        for x in range((len(clip)//TEN_MINUTES)):
            curr_subclips.append(clip[curr:curr+TEN_MINUTES])
            curr+=TEN_MINUTES
        remainder = len(clip)%TEN_MINUTES
        curr_subclips.append(clip[-remainder:])
    else:
        curr_subclips.append(clip)
    
    print([len(clip) for clip in curr_subclips])

    if(multiClips):
        for idx,clip in enumerate(curr_subclips):
            clip.export(os.path.join(CLIP_TEMP_FOLDER,f"clip_{idx}.mp3"), format="mp3")


    #Transcribe clips
    if not TRANSCRIBED:

        text = ""

        for clip in sorted(os.listdir(CLIP_TEMP_FOLDER)):
            if ".mp3" in clip:

                #Whisper API Call
                print(f"processing {clip}")
                audio_file= open(os.path.join(CLIP_TEMP_FOLDER,clip), "rb")
                response = openai.Audio.translate("whisper-1", audio_file)
                print(f"Current exerpt length in text : {len(response['text'])}")
                text+= response["text"]

            #delete processed clip?

        print(f"Total transcript length in chars : {len(text)}")
        print(f"Total transcript length in words : {len(text.split(' '))}")
        print(f"Total transcript length in tokens estimate : {len(text)*CHAR_TOKEN_RATIO}")
        with open("Transcript.txt", "w") as f:
            f.write(text)

    else:
        with open("Transcript.txt", "r") as f:
            text= f.readlines()[0]

    # OpenAI Summarization
    #max context = maxoutput - input tokens
    max_tokens = int(MAX_TOKENS-(len(text)*CHAR_TOKEN_RATIO))

    messages = [
        {"role": "system", "content": "You are an expert in speech transcript summarization."},
        {"role": "user", "content": f"Give a detailed summary of the primary points in the following speech transcript: {text}."}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=max_tokens
    )

    summary = response["choices"][0]["message"]["content"]

    # Save transcript to a file
    with open("Transcript_Summary.txt", "w") as f:
        f.write(summary)


