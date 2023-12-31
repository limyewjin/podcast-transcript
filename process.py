import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import argparse
import json
import math
import sys

import api

THRESHOLD = 3600
USE_HOUR = True
MIN_DURATION_IN_MIN = 2

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
  hour_text = "HH:" if USE_HOUR else ""
  messages = [
    {"role": "system", "content": "You are a helpful assistant in re-formatting text to be more readable."},
    {"role": "user", "content": f"The topic is {topic}\nNext is the transcript of a podcast for this topic:\n{text}\n--\nReformat the provided timestamped podcast transcript into logical sentences and paragraphs. The input text format should be in the format [{hour_text}MM:SS.MS]-[{hour_text}MM:SS.MS] <text>. The output format is '{hour_text}MM:SS - Paragraph 1\nMM:SS - Paragraph 2\n...' Write the reformatted text."}]
  return api.generate_response(messages, model="gpt-4")

def remove_timestamp(topic, text):
  hour_text = "HH:" if USE_HOUR else ""
  messages = [
    {"role": "system", "content": "You are a helpful assistant in re-formatting text to be more readable."},
    {"role": "user", "content": f"The topic is {topic}\nNext is the transcript of a podcast for this topic:\n{text}\n--\nReformat the provided timestamped podcast transcript to remove the timestamps and form into paragraphs. The input text format should be in the format [{hour_text}MM:SS.MS]-[{hour_text}MM:SS.MS] <text>. The output format is 'Paragraph 1\nParagraph 2\n...' Write the reformatted text."}]
  return api.generate_response(messages, model="gpt-3.5-turbo")

def write_summary(topic, text):
  messages = [
    {"role": "system", "content": "You are a helpful assistant in providing useful and insightful summaries."},
    {"role": "user", "content": f"The topic is {topic}\nNext is the transcript of a podcast for this topic:\n{text}\n--\nProvide useful and insightful summary of the text in point-form of up to 3 top points using Markdown format."}]
  return api.generate_response(messages, model="gpt-4")

def find_topics(text):
  hour_text = "HH:" if USE_HOUR else ""
  hour_example = "00:" if USE_HOUR else ""
  responses = []
  rating = "bad"
  print("============ find_topics START==============")
  print(text)
  print("============ find_topics END ==============")
  
  request = f"""{text}\n--\nFor the provided podcast transcript with timestamps:

1. Create up to 3 topics for this section accompanied by their associated timelines.
2. The input timestamps are in the format `[{hour_text}MM:SS.MS]-[{hour_text}MM:SS.MS]`.
3. Each topic has the requirements:
   - Be 1-5 word topic text
   - Represent a significant and distinct segment of the podcast. Merge overlapping or closely related topics to eliminate redundancy.
   - Accurately encapsulate the core idea of that segment without being overly granular.
4. Format the output as: `{hour_text}MM:SS - Topic Description`, each on a new line. 
   Example: 
{hour_example}00:00 - Introduction to the podcast
{hour_example}{MIN_DURATION_IN_MIN:02}:00 - The rise of AI in modern tech
... and so on.
5. Before summarizing, thoroughly comprehend the transcript content. Identify when the topic shifts, and ensure each segment meets the minimum duration requirement. Avoid splitting closely related topics unless there's a clear thematic shift."""
  messages = [
    {"role": "system", "content": "You are a helpful assistant in understanding and labeling topics from timestampped text."},
    {"role": "user", "content": request}]
  responses = []
  while len(responses) < 3:
    topics = api.generate_response(messages, model="gpt-4")
    num_newlines = topics.count("\n")
    print(topics)
    print(f"num_newlines: {num_newlines}")
    print()
    if num_newlines <= 2: break
    responses.append(topics)
    messages.append({"role": "assistant", "content": topics})
    messages.append({"role": "user", "content": f"Your response has {num_newlines} lines, which means you created more than 3 topics. Please create at most 3 topics and output `{hour_text}MM:SS - Topic Description`, each on a new line. Do not apologize, just respond with the timeline and topics."})

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
                    "hour": {
                        "type": "integer",
                        "description": "The hour of the start of the topic",
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
                "required": ["topic", "hour", "minute", "second"]
            },
        }
    ]
  response = api.get_next_step(messages, functions, model='gpt-4')
  print(response)
  topics = []
  while response.get("function_call"):
    function_args = json.loads(response["function_call"]["arguments"])
    topic = function_args.get("topic")
    hour = function_args.get("hour")
    minute = function_args.get("minute")
    second = function_args.get("second")
    topics.append((hour, minute, second, topic))
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

  last_item = input_json[-1]
  last_end_time = last_item["end"]
  last_hour, last_minute, last_second, last_milisecond = get_timestamp(last_end_time)
  print(f"Last timestamp: {format_timestamp(last_end_time)}")
  global MIN_DURATION_IN_MIN
  num_minutes = last_hour * 60 + last_minute
  # want at most 10 topics.
  MIN_DURATION_IN_MIN = int(math.ceil(float(num_minutes) / 10))
  print(f"MIN_DURATION_IN_MIN: {MIN_DURATION_IN_MIN}")
 
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
      formatted_texts.append(f"[{format_timestamp(start_time, USE_HOUR)}]-[{format_timestamp(end_time, USE_HOUR)}] {text}")

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

  def is_within_segment(start_time, hour_mark, minute_mark, second_mark, next_hour_mark, next_minute_mark, next_second_mark):
    start_segment_seconds = 3600 * hour_mark + 60 * minute_mark + second_mark
    end_segment_seconds = 3600 * next_hour_mark + 60 * next_minute_mark + next_second_mark

    return start_segment_seconds <= start_time < end_segment_seconds

  topics_text = []
  for t in range(len(topics) - 1):
    hour_mark, minute_mark, second_mark, topic_text = topics[t]
    next_hour_mark, next_minute_mark, next_second_mark, _ = topics[t + 1]
    
    text = []
    for item in input_json:
        start_time = item["start"]
        if is_within_segment(start_time, hour_mark, minute_mark, second_mark, next_hour_mark, next_minute_mark, next_second_mark):
            text.append(item)
        item["used"] = True
    topics_text.append(text)
  
  # Handle the text after the last segment
  last_hour, last_minute, last_second, _ = topics[-1]
  text = []
  for item in input_json:
      start_time = item["start"]
      if start_time >= 3600 * last_hour + 60 * last_minute + last_second:
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
      timestamp_texts.append(f"[{format_timestamp(start_time, USE_HOUR)}]-[{format_timestamp(end_time, USE_HOUR)}] {text}")

    timestamp_text = '\n'.join(timestamp_texts)
    formatted_text = format_text(topics[t][3], timestamp_text)
    final_timestamp_texts.append(formatted_text)
    print(formatted_text)
    output.append(f"# Timeline - {topics[t][0]:02}:{topics[t][1]:02}:{topics[t][2]:02} - {topics[t][3]}\n\n[Transcript]\n\n{formatted_text}")

  with open(args.output_transcript_file, "w") as f:
    f.write('\n\n\n'.join(output))

  # Write summaries
  summaries = []
  output = []
  for t in range(len(topics)):
    print(topics[t])

    no_timestamp_text = remove_timestamp(topics[t][3], final_timestamp_texts[t])
    summary = write_summary(topics[t][3], no_timestamp_text)
    print(summary)
    summaries.append(summary)
    output.append(f"# Timeline - {topics[t][0]:02}:{topics[t][1]:02}:{topics[t][2]:02} - {topics[t][3]}\n\n[Summary]\n\n{summary}")

  with open(args.output_summary_file, "w") as f:
    f.write('\n\n\n'.join(output))
  

if __name__ == "__main__":
    main()
