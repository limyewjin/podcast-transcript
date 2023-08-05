# Podcast Transcript

This project utilizes OpenAI's Whisper and GPT APIs to accurately transcribe, neatly format, and concisely summarize audio files. It is specifically designed to enhance your podcast experience, providing you with both detailed transcriptions and key takeaways from each episode.

<a target="_blank" href="https://colab.research.google.com/github/limyewjin/podcast-transcript/blob/main/podcast_transcript.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

## 🚀 Features
* Transcription: Convert your audio files into written text using OpenAI's Whisper API.
* Formatting: Clean and structure the raw transcriptions into a reader-friendly format.
* Summarization: Extract the main points and themes from your transcriptions using OpenAI's GPT API.

## 📖 Getting Started
1. Click 'Open in Colab' to access the Colab notebook.
2. Follow the script inside the notebook.
3. For timestamp integrations and summarization, use:
```
$ python process.py --timestamps_file timestamps.txt podcast_transcript.json
```

See output transcript and summary in files specified by `--output_transcript_file` (default `output_transcript.txt`) and `--output_summary_file` (default `output_summary.txt`).

## 🎧 Example
Check out a sample podcast [sample_podcast.mp3](https://github.com/limyewjin/podcast-transcript/blob/main/sample_podcast.mp3) and the resulting transcript [sample_podcast.json](https://github.com/limyewjin/podcast-transcript/blob/main/sample_podcast.json). Podcast episode is from one of my auto-generated podcasts [YJ's Podcast #8](https://yjs-podcast.simplecast.com/episodes/yjs-podcast-8-aug-5-2023).

Refer to [sample_timestamps.txt](https://github.com/limyewjin/podcast-transcript/blob/main/sample_timestamps.txt) for the timestamp data, and see the final [sample_output_transcript.txt](https://github.com/limyewjin/podcast-transcript/blob/main/sample_output_transcript.txt) for a well-formatted transcript, and [sample_output_summary.txt](https://github.com/limyewjin/podcast-transcript/blob/main/sample_output_summary.txt)

### Breaking the Example down

Running the colab on the podcast produces the transcript: [sample_podcast.json](https://github.com/limyewjin/podcast-transcript/blob/main/sample_podcast.json). Sample output below:

```
[
    {
        "id": 0,
        "seek": 0,
        "start": 0.0,
        "end": 11.6,
        "text": " Hello, and welcome to YJ's podcast, Episode 8.",
        "tokens": [
            50364,
            ...
            50944
        ],
        "temperature": 0.0,
        "avg_logprob": -0.2322188290682706,
        "compression_ratio": 1.4264705882352942,
        "no_speech_prob": 0.4174022674560547
    },
```

The timestamp data is: [sample_timestamps.txt](https://github.com/limyewjin/podcast-transcript/blob/main/sample_timestamps.txt)

```
00:08 - Introduction and Episode Overview
01:28 - Exploring 'Green' and 'Brown' Programming Languages
05:28 - Revolutionary Bioelectronic Medicine for Paralysis
08:52 - Exploring Fragrance-Induced Cognitive Enhancement
13:44 - Conclusion and Encouragement to Explore
```

Sample transcript output is [sample_output_transcript.txt](https://github.com/limyewjin/podcast-transcript/blob/main/sample_output_transcript.txt)

```
 Timeline - 00:08 - Introduction and Episode Overview

[Transcript]

00:11 - I'm your host, Dave, also known as the Radio Guy. And I'm Matilda, your Radio Gal. We're here to bring you the latest from the world of technology, science, and beyond.

00:22 - We've got a lot to cover today, but before we dive in, let's set the stage. It's a beautiful Saturday morning here in the Bay Area, the perfect time to catch up on the week's most intriguing stories. Absolutely, Dave. And we've got some fascinating ones lined up for you.

...

# Timeline - 01:28 - Exploring 'Green' and 'Brown' Programming Languages

[Transcript]

01:32 - We're talking about green and brown programming languages. Now, if you're scratching your head wondering what we're talking about, don't worry. We're here to explain.

01:44 - This concept comes from a blog post by Adam Gordon-Bell, a software engineer with over 14 years of experience. He has a passion for functional programming and type systems. Currently, Adam works on static analysis of Docker containers at Tenable, but those are just his day jobs.
```

Sample summary output is [sample_output_summary.txt](https://github.com/limyewjin/podcast-transcript/blob/main/sample_output_summary.txt)

```
# Timeline - 05:28 - Revolutionary Bioelectronic Medicine for Paralysis

[Summary]

- The Feinstein Institutes have developed a revolutionary bioelectronic medicine technology, a double neural bypass, that has restored movement and sensation in a man living with quadriplegia.
- Quadriplegia, historically an irreversible condition, is paralysis from the neck down caused by damage to the spinal cord.
- The double neural bypass technology combines molecular medicine, neuroscience, and biomedical engineering. It uses brain implants, artificial intelligence, and stimulation technology.
- The process involves a microchip implanted in the brain picking up thoughts about movement. These signals are sent to a computer, which interprets them and sends signals to electrode patches over the spine and hand muscles, stimulating them.
- Sensory feedback is sent back to the brain via tiny sensors at the fingertips and palms, completing the double neural bypass.
- The first beneficiary of this technology is Keith Thomas, a 45-year-old man who was paralyzed from the chest down after a diving accident in 2020. He can now move his arms at will and feel touch.
- Keith has also started to see some natural recovery from his injuries, with his arm strength more than doubling and new sensations in his forearm and wrist.
- The technology could potentially forge new pathways at the injury site, leading to potentially permanent recovery.
- The Feinstein Institutes aim to advance new bioelectronic technologies to treat a range of diseases and injuries, including arthritis, pulmonary hypertension, Crohn's disease, and diabetes.
- The development of this technology is a testament to the power of science and technology, and offers hope for people living with paralysis.
```


# 🤝 Contribution
We welcome and appreciate any contributions or suggestions to improve the tool. If you find any issues or see potential enhancements, feel free to open an issue or submit a pull request.

# 💌 Contact
For any questions, issues, or discussions, please create an issue in this repository. We appreciate your feedback and will get back to you as soon as possible.
