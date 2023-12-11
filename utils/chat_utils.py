# encoding: utf-8

import sys, os, re
# import streamlit as st
sys.path.append(os.getcwd())
from utils.openai_utils import get_response

class MultiChatStatelessProvider:
    def __init__(self, bots, messages, user_data):
        self.bots = bots
        self.messages = messages
        self.user_data = user_data

    def start_chat(self, sender, message, turns_limit=0, **kwargs):
        self.messages.append({
            'sender': sender,
            'text': message,
        })
        while True:
            for bot_id in self.bots:
                if turns_limit and len(self.messages) < turns_limit:
                    yield {
                        'text': self.get_response(bot_id, message),
                        'sender': self.bots[bot_id],
                    }
                else:
                    return

    def get_response(self, recepient_id, message):
        recepient_bot = self.bots[recepient_id]
        # _smaple_messages=smaple_messages.copy()
        # _smaple_messages[-1]['content']=_smaple_messages[-1]['content'].format(name=recepient_bot['name'])

        prompt = st.session_state.system_prompt.format(
            role=recepient_bot['name'],
            description=recepient_bot['description'],
        )

        _messages = []
        if 'gpt' in recepient_bot['model']:
            # curernt_role = 'user'
            for message in self.messages:
                # print(message['sender'])
                _messages.append(f"[{message['sender']['name']}]: {message['text']}")
                # curernt_role = 'user' if curernt_role == 'assistant' else 'assistant'
                # curernt_role = 'user' if curernt_role.lower() == 'assistant' else 'assistant'
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
            } for message in self.messages]

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
            self.messages.append({
                'sender': recepient_bot,
                'text': response
            })
            return response
