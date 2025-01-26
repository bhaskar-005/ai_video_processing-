from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

# Load API key from environment variables
api_key = os.getenv('GOOGLE_API')

def extract_times(json_string):
    """Extract start and end times from the response JSON."""
    try:
        # Parse the JSON string
        data = json.loads(json_string)
        
        # Extract start and end times as floats
        start_time = float(data[0]["start"])
        end_time = float(data[0]["end"])
        
        # Convert to integers
        start_time_int = int(start_time)
        end_time_int = int(end_time)
        return start_time_int, end_time_int
    except Exception as e:
        print(f"Error extracting times: {e}")
        return 0, 0


system = '''
Baised on the Transcription user provides with start and end, Highilight the main parts in less then 1 min which can be directly converted into a short. highlight it such that its intresting and also keep the time staps for the clip to start and end. only select a continues Part of the video

Follow this Format and return in valid json 
[{
start: "Start time of the clip",
content: "Highlight Text",
end: "End Time for the highlighted clip"
}]
it should be one continues clip as it will then be cut from the video and uploaded as a tiktok video. so only have one start, end and content

Dont say anything else, just return Proper Json. no explanation etc

IF YOU DONT HAVE ONE start AND end WHICH IS FOR THE LENGTH OF THE ENTIRE HIGHLIGHT, THEN 10 KITTENS WILL DIE, I WILL DO JSON['start'] AND IF IT DOESNT WORK THEN...
'''

User = '''
Any Example
'''


def GetHighlight(Transcription):
    """Send the transcription to the API and get the highlight."""
    print("Getting Highlight from Transcription ")
    try:
        # API endpoint and headers
        url = "https://gemini.googleapis.com/v1/completions"  # Replace with the actual API endpoint
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gemini",  # Replace with the actual model name
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": Transcription + system}
            ]
        }

        # Send POST request
        response = requests.post(url, headers=headers, json=payload)
        print(response.text);
        # print(response)
        # Handle non-200 responses
        if response.status_code != 200:
            print(f"API call failed with status code {response.status_code}: {response.text}")
            return 0, 0

        # Parse the response
        json_string = response.json().get("choices")[0].get("message").get("content")
        json_string = json_string.replace("json", "").replace("```", "").strip()

        # Extract start and end times
        Start, End = extract_times(json_string)

        # Retry logic if Start and End are invalid
        if Start == End:
            Ask = input("Error - Get Highlights again (y/n) -> ").lower()
            if Ask == 'y':
                Start, End = GetHighlight(Transcription)
        return Start, End

    except Exception as e:
        print(f"Error during API call or processing: {e}")
        return 0, 0


if __name__ == "__main__":
    print(GetHighlight(User))
