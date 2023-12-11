import streamlit as st
import sys
import os
import re
import json
import datetime
import string
import traceback
import random
sys.path.append(os.getcwd())
from utils.chat_utils import MultiChatStatelessProvider
from utils.common_utils import remove_quotes
from utils.openai_utils import get_response
from audiorecorder import audiorecorder




bots = [{
    "name": "Claude",
    "description": "",
    "temperature": 1,
    "model": "claude-2",
    "avatar": "🦖",
}]

def get_messages(): return []
st.session_state['messages'] = st.session_state.get('messages', get_messages())
user_data = {
    'name': 'User',
    'avatar': '👤'
}

# chat_provider = MultiChatStatelessProvider(
#     bots=bots,
#     messages=st.session_state.messages,
#     user_data=user_data,
# )
def get_single_response(messages, recepient_bot):
    prompt = recepient_bot['description']
    _messages = []
    if 'gpt' in recepient_bot['model']:
        # curernt_role = 'user'
        for message in messages:
            _messages.append(f"[{message['sender']['name']}]: {message['text']}")
        prompt += f"\nНачни свой ответ с имени твоего пресонажа в квадратных скобках, вот так:\n`[{recepient_bot['name']}]: <текст_ответа>`"
        _messages = [
            {
                'role': 'user',
                'content': '\n'.join(_messages),
            }
        ]

    elif 'claude' in recepient_bot['model']:
        _messages = [{
            'role': message['sender']['name'],
            'content': message['text'],
        } for message in messages]

    for _ in range(10):
        response = get_response(
            # context_info=_smaple_messages,
            messages=_messages,
            prompt=prompt,
            debug=True,
            temperature=recepient_bot['temperature'],
            model=recepient_bot['model'],
            # api_key=recepient_bot.get('api_key') or st.session_state.api_key or DEFAULT_KEY,
        )
        # response regex must match this string:'[BOT NAME]: "RESPONSE"'
        # if not re.match(rf'\[{recepient_bot["name"]}\]:\s*".*"', response):
        if not re.match(rf'\[{recepient_bot["name"]}\]:.*', response):
            print('response regex must match this string:' + rf'\[{recepient_bot["name"]}\]:\s*".*"')
            print('response:', response)

            if recepient_bot['model'] in ['claude-instant-1', 'claude-2']:
                response = f'{response}'
            else:
                continue
        else:
            response = re.sub(rf'\[{recepient_bot["name"]}\]:\s*', '', response)
        return response

# st.title("Echo Bot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun

# st.write(st.session_state.messages)

for message in st.session_state.messages:
    with st.chat_message(
        name=message['sender']['name'],
        avatar=message['sender']['avatar'],
    ):
        st.markdown(message["text"])
    
        
            
if user_message := st.chat_input("What is up?"):
    
    with st.chat_message(
            name=user_data['name'],
            avatar=user_data['avatar'],
        ):
        st.markdown(user_message)
    
    st.session_state.messages.append({
        "sender": user_data,
        "text": user_message,
    })
    
    
    # response = f"Echo: {prompt}"
    response = get_single_response(st.session_state.messages, bots[0])
    st.session_state.messages.append(
        {
            "sender": {
                "name": "assistant",
                "avatar": "🤖",
            },
            "text": response,
        }
    )
    
    # Display assistant response in chat message container
    with st.chat_message(
        **{          "name": "assistant",
                "avatar": "🤖",}
    ):
        st.markdown(response)


empty_container = st.empty()    
audio = audiorecorder("Click to record", "Recording...")

if len(audio) > 0:
    # To play audio in frontend:
    st.audio(audio.tobytes())
    
    # To save audio to a file:
    wav_file = open("audio.mp3", "wb")
    wav_file.write(audio.tobytes())

# init_message = st.chat_input("Начните диалог, задав вопрос или поставив задачу")
# if init_message:
#     with st.chat_message(name=user_data.get('name'), avatar=user_data.get('avatar')):
#         st.markdown(f"[User]: {init_message}")
#     iterator = chat_provider.start_chat(sender=user_data, message=init_message)
#     while True:
#         try:
#             with st.spinner('Wait for the response...'):
#                 msg_iteration = next(iterator)
                
#         except StopIteration:
#             # empty_container.markdown(f"## Всего сообщений: {len(st.session_state.messages)}")
#             # st.success("Чат завершен!")
#             break
#         except Exception as e:
#             print(e)
#             print(traceback.format_exc())
#             st.error(e)
#             break
#         with st.chat_message(
#             name=msg_iteration['sender']['name'],
#             avatar=msg_iteration['sender']['avatar']
#         ):
#             st.markdown(f"[{msg_iteration['sender'].get('name')}]: {remove_quotes(msg_iteration['text'])}")
#         # empty_container.markdown(f"## Messages: {len(st.session_state.messages)}")
#         # empty_container.write(st.session_state.messages)
