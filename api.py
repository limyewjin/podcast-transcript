import openai
import json
import time
from retrying import retry
from dotenv import load_dotenv
import os
import tiktoken

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

def num_tokens_from_string(string: str, model: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def text_to_chunks(text: str, token_limit: int, overlap: int, model: str = "gpt-3.5-turbo"):
    if overlap >= token_limit:
        raise ValueError("Overlap should be less than the token limit.")

    text_tokens = num_tokens_from_string(text, model)

    if text_tokens <= token_limit:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + token_limit
        if end >= len(text):
            chunks.append(text[start:])
            break

        chunk = text[start:end].strip()
        overlap_start = max(0, end - overlap)
        while num_tokens_from_string(text[overlap_start:end], model) > overlap:
            overlap_start -= 1

        chunks.append(chunk)
        start = overlap_start

    return chunks


@retry(stop_max_attempt_number=3, wait_exponential_multiplier=100, wait_exponential_max=1000)
def get_next_step(messages, functions, function_call='auto', model='gpt-3.5-turbo-0613'):
    # Step 1: send the conversation and available functions to GPT
    #messages = [{"role": "user", "content": "What should I do next?"}]
    #functions = [
    #    {
    #        "name": "turing_action",
    #        "description": "Call out what to do next in AI chat game",
    #        "parameters": {
    #            "type": "object",
    #            "properties": {
    #                "action": {
    #                    "type": "string",
    #                    "description": "The next action to take",
    #                    "enum": ["talk", "pause"],
    #                },
    #                "text": {
    #                    "type": "string",
    #                    "description": "What to say, present when talking",
    #                },
    #                "wait_in_s": {
    #                    "type": "string",
    #                    "description": "How long to wait, in seconds",
    #                },
    #            },
    #            "required": ["action"],
    #        },
    #    }
    #]
    # function_call = {'name': 'turing_action'}
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        return response["choices"][0]["message"]
    except openai.error.RateLimitError as ratelimit_error:
        print(f"RatelimitError: {ratelimit_error}")
        raise

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def is_correct(original, answer, question, model='gpt-3.5-turbo-0613'):
    # use this if you can fit source content in it
    # original: source content
    # answer: answer received
    # question: for LLM to answer
    messages = [{"role": "system", "content": "You are a helpful AI in assessing the quality of answers."},
      {"role": "user", "content": f"The source content is:\n{original}\n--\nThe answer generated was:\n{answer}\n--\n{question}"}]
    functions = [
        {
            "name": "is_correct",
            "description": "Assesses the quality and correctness of the answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "correct": {
                        "type": "string",
                        "description": "Is the answer generated correctly?",
                        "enum": ["true", "false"],
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Rationale for whether or not the answer was generated correctly",
                    },
                },
                "required": ["correct", "rationale"],
            },
        }
    ]
    function_call = {'name': 'is_correct'}
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        response_message = response["choices"][0]["message"]
        function_args = json.loads(response_message['function_call']['arguments'])
        return function_args
    except openai.error.RateLimitError as ratelimit_error:
        print(f"RatelimitError: {ratelimit_error}")
        raise

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def is_good_response(response, question, model='gpt-4'):
    # response = answer from LLM
    # question = "Evaluate if the response received has useful articles and links to the articles in it."
    messages = [{'role': 'system',
      'content': f"You are a helpful AI which helps to assess responses."},
      {'role': 'user',
      'content': f'Here\'s the text we received:\n{response}\n---\n{question}'}]
    functions = [
          {
              "name": "is_good_response",
              "description": "Function call to whether or not the response extracted useful articles and links.",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "rating": {
                          "type": "string",
                          "description": "Was the response good or bad",
                          "enum": ["good", "bad"],
                      },
                      "rationale": {
                          "type": "string",
                          "description": "rationale for the rating given",
                      },
                      "suggestions": {
                          "type": "string",
                          "description": "suggestions to improve response",
                      },

                  },
                  "required": ["rating", "rationale", "suggestions"],
              },
          }
      ]
    function_call = {'name': 'is_good_response'}
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        response_message = response["choices"][0]["message"]
        function_args = json.loads(response_message['function_call']['arguments'])
        return function_args
    except openai.error.RateLimitError as ratelimit_error:
        print(f"RatelimitError: {ratelimit_error}")
        raise

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


# Define a decorator to handle retrying on specific exceptions
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=100, wait_exponential_max=1000)
def generate_response(messages, temperature=0.0, top_p=1, frequency_penalty=0.0, model="gpt-3.5-turbo"):
    """
    Generate a response using OpenAI API's ChatCompletion feature.

    Args:
        messages (list): List of chat messages in the conversation. Each item is a dict with `role` (system, assistant, user) and `content`.
        temperature (float, optional): Controls the randomness of the response. Defaults to 0.5.
        top_p (float, optional): Controls the nucleus sampling. Defaults to 1.
        max_tokens (int, optional): Maximum tokens in the response. Defaults to 1024.

    Returns:
        str: The generated response from the chat model.

    Example messages = [
            {"role": "system", "content": "You are a helpful assistant in re-formatting text."},
            {"role": "user", "content": f"{chunk}\n--\nThe text above is a scrape from explainxkcd - it has line breaks in-between sentences and improper formatting. Clean up the text to have proper sentences and structure. Keep the original text intact - just clean text formatting (e.g., capitalization) and do not remove words."}]
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=0
        )

        message = json.loads(str(response.choices[0].message))
        return message["content"].strip()

    except openai.error.RateLimitError as ratelimit_error:
        print(f"RatelimitError: {ratelimit_error}")
        raise

    except TimeoutError as timeout_error:
        print(f"TimeoutError: {timeout_error}")
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

