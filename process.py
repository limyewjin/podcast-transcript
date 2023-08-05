import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import argparse
import json
import sys

import api

THRESHOLD = 3000

def get_timestamp(seconds):
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    return hours, minutes, seconds, milliseconds


def format_timestamp(
    seconds: float, always_include_hours: bool = False, decimal_marker: str = "."
):
    hours, minutes, seconds, milliseconds = get_timestamp(seconds)

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return (
        f"{hours_marker}{minutes:02d}:{seconds:02d}{decimal_marker}{milliseconds:03d}"
    )

def format_text(topic, text):
  messages = [
    {"role": "system", "content": "You are a helpful assistant in re-formatting text to be more readable."},
    {"role": "user", "content": f"The topic is {topic}\nNext is the transcript of a podcast for this topic:\n{text}\n--\nReformat the provided timestamped podcast transcript into logical sentences and paragraphs. The input text format should be in the format [MM:SS.MS]-[MM:SS.MS] <text>. The output format is 'MM:SS - Paragraph 1\nMM:SS - Paragraph 2\n...' Write the reformatted text."}]
  return api.generate_response(messages, model="gpt-4")

def remove_timestamp(topic, text):
  messages = [
    {"role": "system", "content": "You are a helpful assistant in re-formatting text to be more readable."},
    {"role": "user", "content": f"The topic is {topic}\nNext is the transcript of a podcast for this topic:\n{text}\n--\nReformat the provided timestamped podcast transcript to remove the timestamps and form into paragraphs. The input text format should be in the format [MM:SS.MS]-[MM:SS.MS] <text>. The output format is 'Paragraph 1\nParagraph 2\n...' Write the reformatted text."}]
  return api.generate_response(messages, model="gpt-3.5-turbo")

def write_summary(topic, text):
  messages = [
    {"role": "system", "content": "You are a helpful assistant in providing useful and insightful summaries."},
    {"role": "user", "content": f"The topic is {topic}\nNext is the transcript of a podcast for this topic:\n{text}\n--\nProvide useful and insightful summary of the text in point-form using Markdown format."}]
  return api.generate_response(messages, model="gpt-4")

def find_topics(text):
  responses = []
  rating = "bad"
  while len(responses) < 3 and rating == "bad":
    request = f"""{text}\n--\nFor the provided podcast transcript with timestamps:

1. Create topic-level summaries accompanied by their associated timelines.
2. The input timestamps are in the format `[MM:SS.MS]-[MM:SS.MS]`.
3. Each summarized topic should:
   - Last **at least 2 minutes** in duration. Avoid creating segments shorter than this.
   - Represent a significant and distinct segment of the podcast. Merge overlapping or closely related topics to eliminate redundancy.
   - Accurately encapsulate the core idea of that segment without being overly granular.
4. Format the output as: `MM:SS - Topic Description`, each on a new line. 
   Example: 
00:00 - Introduction to the podcast
02:00 - The rise of AI in modern tech
... and so on.
5. Before summarizing, thoroughly comprehend the transcript content. Identify when the topic shifts, and ensure each segment meets the minimum duration requirement. Avoid splitting closely related topics unless there's a clear thematic shift."""
    if len(responses) > 0:
      rationale, suggestions = responses[-1]
      request += f" Your last response was {topics} but was rejected due to {rationale} with the following suggestions {suggestions}."

    messages = [
      {"role": "system", "content": "You are a helpful assistant in understanding and labeling topics from timestampped text."},
      {"role": "user", "content": request}]
    topics = api.generate_response(messages, model="gpt-4")
    print(topics)

    response = api.is_good_response(topics, "Examine the provided topic-level podcast summary with its associated timelines in MM:SS timestamps. All topics are supposed to be at least 2 minutes long. Do all summarized topics last at least 2 minutes? Highlight any segments that do not meet this duration criterion. Think about it and call the `is_good_response` function to process.")
    print(response)

    rating = response.get("rating")
    rationale = response.get("rationale")
    suggestions = response.get("suggestions")
    responses.append((rationale, suggestions))

  return topics

def extract_timestamps(timestamps_text):
  messages = [{'role': 'system', 'content': f"You are a helpful AI which extracts timestamps from timestampped text."},
    {'role': 'user',
    'content': f'Below is the timestamps with topics:\n{timestamps_text}\n---\nIterate and extract the timestamps for each topic.'}]
  functions = [
        {
            "name": "extract_timestamp",
            "description": "Extract the timestamp for a topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic text",
                    },
                    "minute": {
                        "type": "integer",
                        "description": "The minute of the start of the topic",
                    },
                    "second": {
                        "type": "integer",
                        "description": "The second of the start of the topic",
                    },
                },
                "required": ["topic", "minute", "second"]
            },
        }
    ]
  response = api.get_next_step(messages, functions, model='gpt-4')
  print(response)
  topics = []
  while response.get("function_call"):
    function_args = json.loads(response["function_call"]["arguments"])
    topic = function_args.get("topic")
    minute = function_args.get("minute")
    second = function_args.get("second")
    topics.append((minute, second, topic))
    messages.append(response)
    messages.append(
            {
                "role": "function",
                "name": 'extract_timestamp',
                "content": 'true',
            }
        )
    response = api.get_next_step(messages, functions, model='gpt-4')
    print(response)
    
  return topics

def main():
  parser = argparse.ArgumentParser(description="Format podcast transcript from Whisper API.")
  parser.add_argument("file", type=str, help="Input Whisper API timestamped JSON.")
  parser.add_argument("--timestamps_file", type=str, help="Text file containing timestamps.")
  parser.add_argument("--output_transcript_file", type=str, default="output_transcript.txt", help="Output filename for transcript.")
  parser.add_argument("--output_summary_file", type=str, default="output_summary.txt", help="Output filename for summary.")
  args = parser.parse_args()

  with open(args.file, "r") as f:
    input_json_text = f.read()

  input_json = json.loads(input_json_text)
 
  timestamps_text = ""
  if args.timestamps_file:
    with open(args.timestamps_file, "r") as f:
      timestamps_text = f.read().strip()   

  if len(timestamps_text) == 0:
    formatted_texts = []
    for item in input_json:
      start_time = item["start"]
      end_time = item["end"]
      text = item["text"]
      formatted_texts.append(f"[{format_timestamp(start_time)}]-[{format_timestamp(end_time)}] {text}")

    topics = []
    start = 0
    for index in range(1, len(formatted_texts)):
      text = '\n'.join(formatted_texts[start:index])
      num_tokens = api.num_tokens_from_string(text, "gpt-4")
      if num_tokens > THRESHOLD:
        text = '\n'.join(formatted_texts[start:index-1])
        response = find_topics(text)
        print(response)
        topics.append(response)
        start = index
    text = '\n'.join(formatted_texts[start:len(formatted_texts)])
    response = find_topics(text)
    print(response)
    topics.append(response)
    timestamps_text = '\n'.join(topics)

  topics = extract_timestamps(timestamps_text)
  print("Extracted topics and timestamps")
  print("===============================")
  print(topics)
  print("===============================")

  for item in input_json:
    item["used"] = False

  def is_within_segment(start_time, minute_mark, second_mark, next_minute_mark, next_second_mark):
    start_segment_seconds = 60 * minute_mark + second_mark
    end_segment_seconds = 60 * next_minute_mark + next_second_mark if next_minute_mark is not None else float('inf')

    return start_segment_seconds <= start_time < end_segment_seconds

  topics_text = []
  for t in range(len(topics) - 1):
    minute_mark, second_mark, topic_text = topics[t]
    next_minute_mark, next_second_mark, _ = topics[t + 1]
    
    text = []
    for item in input_json:
        start_time = item["start"]
        if is_within_segment(start_time, minute_mark, second_mark, next_minute_mark, next_second_mark):
            text.append(item)
        item["used"] = True
    topics_text.append(text)
  
  # Handle the text after the last segment
  last_minute, last_second, _ = topics[-1]
  text = []
  for item in input_json:
      start_time = item["start"]
      if start_time >= 60 * last_minute + last_second:
          text.append(item)
          item["used"] = True
  topics_text.append(text)

  for item in input_json:
    if item["used"] == False: raise("did not use an item")

  print(topics_text)

  # Write transcript file
  output = []
  final_timestamp_texts = []
  for t in range(len(topics)):
    print(topics[t])
    timestamp_texts = []
    for item in topics_text[t]:
      start_time = item["start"]
      end_time = item["end"]
      text = item["text"]
      timestamp_texts.append(f"[{format_timestamp(start_time)}]-[{format_timestamp(end_time)}] {text}")

    timestamp_text = '\n'.join(timestamp_texts)
    formatted_text = format_text(topics[t][2], timestamp_text)
    final_timestamp_texts.append(formatted_text)
    print(formatted_text)
    output.append(f"# Timeline - {topics[t][0]:02}:{topics[t][1]:02} - {topics[t][2]}\n\n[Transcript]\n\n{formatted_text}")

  with open(args.output_transcript_file, "w") as f:
    f.write('\n\n\n'.join(output))

  # Write summaries
  summaries = []
  output = []
  for t in range(len(topics)):
    print(topics[t])

    no_timestamp_text = remove_timestamp(topics[t][2], final_timestamp_texts[t])
    summary = write_summary(topics[t][2], no_timestamp_text)
    print(summary)
    summaries.append(summary)
    output.append(f"# Timeline - {topics[t][0]:02}:{topics[t][1]:02} - {topics[t][2]}\n\n[Summary]\n\n{summary}")

  with open(args.output_summary_file, "w") as f:
    f.write('\n\n\n'.join(output))
  

if __name__ == "__main__":
    main()
