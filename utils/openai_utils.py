# encoding: utf-8

import json
import tiktoken
import backoff
import openai
import requests
import dotenv
import os
dotenv.load_dotenv(dotenv.find_dotenv())
GPT_KEY = os.getenv('GPT_KEY')
CLAUDE_KEY = os.getenv('CLAUDE_KEY')
if GPT_KEY:
    openai.api_key = GPT_KEY
import os
import sys
sys.path.append(os.getcwd())


settings = dict.fromkeys([
    'model',
    'key',
    'prompt',
    'temperature',
    'debug',
])

settings['model'] = 'gpt-3.5-turbo-16k'

EmptySettingsPropvider = type('EmptySettingsPropvider', (object,), settings)
sp = EmptySettingsPropvider()

MODEL: str = sp.model
# openai.api_key = GPT_KEY
PROMPT = sp.prompt
TEMPERATURE = sp.temperature
DEBUG = sp.debug



# GPT_TOKENS_LIMIT = 4097 * 0.85  # 4096 is limit, but we need some safe space
SAFE_SPACE_TOKEN_COEF = 0.95
GPT_TOKENS_LIMIT = {
    'gpt-4-1106-preview': 80000,
    'gpt-3.5-turbo': 4096,
    'gpt-3.5-turbo-16k': 16384,
    'gpt-4': 8192,
    'claude-instant-1': 70000,
    'claude-2': 70000,
}.get(MODEL, 4096) * SAFE_SPACE_TOKEN_COEF  # type: ignore


def list_models():
    return openai.Engine.list()


def count_tokens(text: str) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(MODEL)
    return len(encoding.encode(text))


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=5,
)
def get_response_one_message(message, debug=False, top_p=1):
    print('get_response_one_message')
    print('message: ', message)
    request = dict(
        model=MODEL,
        messages=[{
            'role': 'user',
            'content': message,
        }],
        top_p=top_p,
    )
    if debug:
        print(json.dumps(request, indent=2))
    resp = openai.ChatCompletion.create(
        **request
    )
    if debug:
        print(json.dumps(resp, indent=2))
    return resp.choices[0]['message']['content']


def get_chat(_messages, before=None, after=None):
    _messages = _messages.copy()
    if before:
        if isinstance(before, list):
            before_messages = before
        else:
            before_messages = [{
                'role': 'system',
                'content': str(before),
            }]
        _messages = before_messages + _messages

    if after:
        _messages += [{
            'role': 'system',
            'content': str(after),
        }]
    return _messages


def print_error_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print('Error in {}: {}'.format(func.__name__, e))
            print('args: ', args)
            print('kwargs: ', kwargs)

            raise e

        except KeyboardInterrupt:
            print('KeyboardInterrupt in {}'.format(func.__name__))
            sys.exit(1)

        except openai.error.InvalidRequestError as e:
            print('openai.error.InvalidRequestError in {}: {}'.format(func.__name__, e))
            print('args: ', args)
            print('kwargs: ', kwargs)

            raise e
    return wrapper


# def claude_role(role): return 'Human' if role == 'user' else 'Assistant'
def claude_role(role): return role


class ClaudeApi:

    @staticmethod
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5,
    )
    def get_response(
        messages,
            debug=DEBUG,
            prompt=None,
            context_info=None,
            max_tokens=None,
            temperature=TEMPERATURE,
            model=MODEL,
            api_key=None,
    ):
        prompt = prompt or PROMPT

        print('get_response from claude api')
        print('messages: ', messages)
        print('prompt: ', prompt)
        print('context_info: ', context_info)
        print('temperature: ', temperature)
        print('model: ', model)

        claude_prompt = '\n\nHuman:'

        # if context_info:
        #     if isinstance(context_info, dict):
        #         context_info = json.dumps(context_info, ensure_ascii=False, indent=2)
        #     if isinstance(context_info, str):
        #         context_info = context_info.strip()
        #     if isinstance(context_info, list):  # messages
        #         for cntx_msg in context_info:
        #             claude_prompt += f'\n\n{claude_role(cntx_msg["role"])}: {cntx_msg["content"]}'
        #     else:
        #         claude_prompt += f'\n\n{context_info}'

        #     claude_prompt += '\n\nContext:' + context_info
        
        if context_info:
            claude_prompt += f'\n\n{context_info}\n\n' if context_info else ''
        
        if messages:
            claude_prompt += '\n\nPrevious messages:'
            for message in messages:
                claude_prompt += f'\n\n<{claude_role(message["role"])}>: {message["content"]}'
        if prompt:
            claude_prompt += f'\n\n{prompt}\n\n' if prompt else ''
        claude_prompt += '\n\nAssistant:'

        request_obj = {
            'prompt': claude_prompt,
            'model': model,
            'temperature': temperature,
            'max_tokens_to_sample': max_tokens or 20000,
        }
        headers = {
            'accept': 'application/json',
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
            'x-api-key': api_key,
        }

        if debug:
            print('CLAUDE API REQUEST:')
            print(json.dumps(request_obj, indent=2, ensure_ascii=False))

        resp = requests.post(
            'https://api.anthropic.com/v1/complete',
            json=request_obj,
            headers=headers,
            timeout=60,
        ).json()

        if debug:
            print('CLAUDE API RESPONSE:')
            print(json.dumps(resp, indent=2, ensure_ascii=False))
        if 'error' in resp:
            raise Exception(resp[f'{resp["type"]}: {resp["message"]}'])
        return resp['completion']


@backoff.on_exception(
    backoff.expo,
    openai.error.RateLimitError,
    max_tries=5,
)
def get_response(
    messages,
    debug=DEBUG,

    # prompting:
    prompt=None,
    context_info=None,

    # api:
    max_tokens=None,
    functions=None,
    function_call=None,
    temperature=TEMPERATURE,
    model=MODEL,
    api_key=None,
) -> str:

    print('selected model: ', model)

    if model in ['claude-instant-1', 'claude-2']:
        return ClaudeApi.get_response(
            messages,
            debug=debug,
            prompt=prompt,
            context_info=context_info,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
            api_key=api_key or CLAUDE_KEY,
        )

    # if api_key:
    openai.api_key = api_key or GPT_KEY
    print('messages')
    print(messages)
    print('prompt: ', prompt)

    _messages = messages
    prompt = prompt or PROMPT
    while 1:
        tokens = count_tokens(str(get_chat(_messages, after=prompt, before=context_info)))
        if tokens > GPT_TOKENS_LIMIT and len(_messages) > 1:
            if tokens > GPT_TOKENS_LIMIT * 1.5:
                to_remove = int(max(1, len(_messages) * 0.3))
            else:
                to_remove = 1
            print('Tokens count:', tokens, 'too much, removing {} message'.format(to_remove))
            _messages = _messages[to_remove:]
        else:
            break
    # print('messages after')
    # print(messages)

    request = dict(
        model=model,
        messages=[],
        temperature=float(temperature),
        max_tokens=max_tokens,
    )

    if function_call:
        request['function_call'] = function_call

    if functions:
        request['functions'] = functions

    for msg in get_chat(_messages, after=prompt, before=context_info):
        message = {
            'role': msg['role'],
            'content': str(msg['content'] or ' '),
        }

        request['messages'].append(message)

    if debug:
        print('OPEANAI REQUEST:')
        print(json.dumps(request, indent=2, ensure_ascii=False))
        # await log('SYSTEM', f"sending request to openai: {_messages}")

    resp = openai.ChatCompletion.create(
        **request
    )

    if debug:
        print('OPEANAI RESPONSE:')
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        # await log('SYSTEM', f"response from openai: {resp.choices[0]['message']['content']}")

    if functions:
        return resp
    return resp.choices[0]['message']['content']


async def transcribe(mp3_file):
    with open(mp3_file, "rb") as f:
        transcript = await openai.Audio.atranscribe("whisper-1", f)

    print(json.dumps(transcript, indent=2, ensure_ascii=False))
    text = transcript.get('text', '')

    return text


if __name__ == '__main__':
    print(list_models())
