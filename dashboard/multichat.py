# encoding: utf-8
import streamlit as st
import sys
import os
import re
import json
import datetime
import string
import random
sys.path.append(os.getcwd())
from utils.openai_utils import get_response
AVATARS = list({
    '👤',
    '👩‍🎨', '👨‍🎨', '🎭', '🎤', '🎸', '👩‍💻', '👨‍💻', '📚', '🔬',
    '🧪', '🔧', '🌍', '📊', '💼', '⚖️', '👨‍⚕️', '👩‍⚕️', '👷‍♀️', '👷‍♂️', '🎓',
    '👩‍💻', '👨‍💻', '📈', '📊', '🖥️', '💻', '📱', '🧠', '🎯'
})
MODELS = [
    'gpt-3.5-turbo-16k',
    # 'gpt-4',
    'claude-instant-1',
    'claude-2',
]

SYSTEM_PROMPT = '''{description}.\nНе сбивайся с роли, не пиши от лица других участников чата.
Ответ ожидается в виде прямой речи персонажа, без кавычек и дополнительных комментариев.
\n\nОтвет от первого лица, согласно указанной роли в чате ({role}).'''

st.set_page_config(
    page_title="MultiTalk - Chat with multiple bots",
    page_icon="💡",
    #    layout="centered",
    layout="wide",
    initial_sidebar_state="collapsed",
    # menu_items={
    # 'Get Help': 'https://www.extremelycoolapp.com/help',
    # 'Report a bug': "https://www.extremelycoolapp.com/bug",
    # 'About': "# This is a header"
    # }
)
# header:
user_data = {
    'name': 'User',
    'avatar': '👤'
}
st.markdown("# 💡 Мультичат - обсуди что угодно с несколькими ботами")
# st.markdown("This is a header. This is an *extremely* cool app!")
# st.write(settings_json)
#


def get_messages(): return [
    # {
    #     'sender': st.session_state.bots[1], 'text': 'Im a tomato',
    # },
    # {
    #     'sender': st.session_state.bots[2], 'text': 'Im a banana',
    # },
]


st.session_state['messages'] = st.session_state.get('messages', get_messages())
bots_col, chat_col = st.columns([1, 3])

if st.session_state.get('bots') is None:
    # st.session_state.bots = settings_json.dict_by_key('bots', 'id')
    st.session_state.bots = {}

if st.session_state.get('turns_limit') is None:
    st.session_state.turns_limit = 20

# if st.session_state.get('api_key') is None:
#     st.session_state.api_key = ''

if st.session_state.get('init_message') is None:
    st.session_state.init_message = ''

if st.session_state.get('system_prompt') is None:
    st.session_state.system_prompt = SYSTEM_PROMPT


def bot_id(bot):
    # hash bot by all fields except key:
    return str(hash(json.dumps({k: v for k, v in bot.items()})))


def load_content(content_dict):
    bots = content_dict.get('bots', {})
    for bot in bots:
        bot['id'] = bot_id(bot)
        if not bot.get('avatar'):
            bot['avatar'] = '👤'
        if bot['avatar'] not in AVATARS:
            AVATARS.append(bot['avatar'])
        bot['expanded'] = False

    bots = {bot['id']: bot for bot in bots}
    st.session_state.bots.update(bots)
    st.session_state.turns_limit = content_dict.get('turns_limit', 20)
    # st.session_state.api_key = st.session_state.api_key or content.get('api_key', '')

    print('uploaded bots: ', bots)
    st.experimental_rerun()


st.session_state.bot_key = ''
ADD_BOT = False
UPLOAD_BOTS = True
with bots_col:
    st.markdown("### 🛠️ Боты:")
    if st.session_state.get('bots') is not None:
        for i, bot in enumerate(st.session_state.bots.values()):
            with st.expander(f"{bot['avatar']} {bot['name']}", expanded=bot.get('expanded', False)):
                if bot['avatar'] not in AVATARS:
                    AVATARS.append(bot['avatar'])
                form = st.form(key=f"bot_form_{bot['id']}")
                row = form.columns([3, 1])
                bot['name'] = row[0].text_input('Имя', value=bot['name'], key=f"{bot['id']}_name")
                bot['avatar'] = row[1].selectbox('Аватар', AVATARS, index=AVATARS.index(bot['avatar']), key=f"{bot['id']}_avatar")
                bot['description'] = form.text_area('Промпт', value=bot['description'], key=f"{bot['id']}_description")
                row2 = form.columns(2)
                bot['temperature'] = row2[0].slider('Температура', 0.0, 2.0, value=bot['temperature'], step=0.01, key=f"{bot['id']}_temperature")
                bot['model'] = row2[1].selectbox(
                    'Модель',
                    MODELS,
                    help="Убедитесь, что ключ, который вы предоставили, имеет доступ к выбранной модели",
                    index=MODELS.index(bot['model']),
                    key=f"{bot['id']}_model",
                )
                # bot['api_key'] = st.text_input('Ключ', value=bot.get('api_key', ''), type='password', key=f"{bot['id']}_key")

                row3 = form.columns([6, 1])

                if row3[0].form_submit_button('Сохранить'):
                    bot['expanded'] = True
                    st.session_state.bots[bot['id']] = {
                        'id': bot['id'],
                        **bot,
                    }
                    # reload page:
                    st.experimental_rerun()

                if row3[1].form_submit_button('❌'):
                    del st.session_state.bots[bot['id']]
                    # reload page:
                    st.experimental_rerun()

    if st.button('Добавить бота ➕'):
        new_bot = {
            'name': 'Новый бот ' + str(len(st.session_state.bots) + 1),
            'description': '',
            'temperature': 0.85,
            'model': 'gpt-3.5-turbo-16k',
            'avatar': '👤',
            'expanded': True,
            'created': datetime.datetime.utcnow().isoformat(),
            # 'api_key': '',
        }
        new_id = bot_id(new_bot)
        st.session_state.bots[new_id] = {
            'id': new_id,
            **new_bot,
        }
        # reload page:
        st.experimental_rerun()

    st.divider()

    with st.expander('Выбрать пресет ботов и настроек'):
        files = os.listdir(os.path.join('dashboard', 'presets'))
        files_by_name = {}
        for filename in files:
            with open(os.path.join('dashboard', 'presets', filename), 'r', encoding='utf-8') as f:
                file_content = f.read()
                json_content = json.loads(file_content)
                if 'title' not in json_content:
                    continue
                    # json_content['title'] = filename
                if json_content['title'] in files_by_name:
                    json_content['title'] = json_content['title'] + ' ' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                files_by_name[json_content['title']] = json_content

        preset_title = st.selectbox('Выбрать готовый:', list(files_by_name.keys()))
        load_button = st.button('Применить')
        if preset_title and load_button:

            with st.spinner('Загрузка...'):

                load_content(files_by_name[preset_title])

        if UPLOAD_BOTS:
            st.divider()
            uploaded_file = st.file_uploader("Загрузить из файла:", type="json")
            if uploaded_file is not None and st.session_state.get('bots') == {}:
                uploaded_content = uploaded_file.getvalue()
                # convert to utf-8 json
                uploaded_content = uploaded_content.decode('utf-8')
                json_uploaded_content = json.loads(uploaded_content)
                load_content(json_uploaded_content)
                uploaded_file = None

    with st.expander('Общие настройки'):
        st.session_state.turns_limit = st.number_input('Лимит сообщений', value=st.session_state.turns_limit, step=1)
        # st.session_state.api_key = st.text_input(
        #     'Общий ключ',
        #     value=st.session_state.api_key,
        #     type='password',
        #     help="Используется для всех ботов без указанного ключа. Убедитесь, что ключ, который вы предоставили, имеет доступ к выбранной модели",
        # )
        st.session_state.system_prompt = st.text_area(
            'Системные инструкции',
            value=st.session_state.system_prompt,
            help="Инструкции, которые будут заданы при каждой отправке сообщения боту. Требуемый параметры в тексте, подставляемые для каждого конкретного бота: {role}, {description}",
        )

    if st.button('Очистить историю 🗑️'):
        if st.button('Точно удалить историю чата?'):
            st.session_state.messages = []
            # reload page:
            st.experimental_rerun()

    st.download_button(
        label="Экспорт настроек 🛠️",
        data=json.dumps(
            {
                'bots': list(st.session_state.bots.values()),
                'turns_limit': st.session_state.turns_limit,
                # 'api_key': st.session_state.api_key,
                # 'init_message': st.session_state.init_message,
            },
            indent=2, ensure_ascii=False),
        file_name='settings.json',
        mime='application/json',
    )

    with st.expander('Экспорт логов чата 💾'):
        if len(st.session_state.bots) > 0:
            history = st.session_state.messages
            all_history = [f"{message['text']}" for message in history]
            st.download_button(
                label="Полный лог 📒",
                data='\n'.join(all_history),
                file_name='all_chat_history.txt',
                mime='application/txt',
                key='all_history',
            )
            # json by bot:
            for bot in st.session_state.bots.values():
                bot_history = [f"{message['text']}" for message in history if message['sender']['name'] == bot['name']]
                st.download_button(
                    label=f"Только {bot['name']} {bot['avatar']}",
                    data='\n'.join(bot_history),
                    file_name=f"{bot['name']}.txt",
                    mime='application/txt',
                    key=f"{bot['id']}_history",
                )

    empty_container = st.empty()


class MultiChatStatelessProvider:
    def __init__(self, bots, messages, user_data):
        self.bots = bots
        self.messages = messages
        self.user_data = user_data

    def start_chat(self, sender, message, **kwargs):
        self.messages.append({
            'sender': sender,
            'text': message,
        })
        while True:
            for bot_id in self.bots:
                if len(self.messages) < st.session_state.turns_limit:
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
            curernt_role = 'user'
            for message in self.messages:
                print(message['sender'])
                _messages.append({
                    'role': curernt_role,
                    'content': message['text'],
                })
                curernt_role = 'user' if curernt_role == 'assistant' else 'assistant'
                # curernt_role = 'user' if curernt_role.lower() == 'assistant' else 'assistant'
            prompt += f"\nНачни свой ответ с имени твоего пресонажа в квадратных скобках, вот так:\n`[{recepient_bot['name']}]: <текст_ответа>`"
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


chat_provider = MultiChatStatelessProvider(
    bots=st.session_state.bots,
    messages=st.session_state.messages,
    user_data=user_data,
)
with chat_col:
    st.markdown("### 📝 Чат:")
    # max width:
    st.markdown(
        """
        <style>
        .reportview-container .main .block-container{
            max-width: 1000px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    for message in st.session_state.messages:
        with st.chat_message(name=message['sender'].get('name'), avatar=message['sender'].get('avatar')):
            st.write(f"[{message['sender'].get('name')}]: {message['text']}")


def remove_quotes(txt):  # strip it and removes quotes in the beginning and in the end of the string
    return txt.strip().strip('"').strip("'")


init_message = st.chat_input("Начните диалог, задав вопрос или поставив задачу")
if init_message:
    with chat_col.chat_message(name=user_data.get('name'), avatar=user_data.get('avatar')):
        st.markdown(f"[User]: {init_message}")
    # for msg_iteration in chat_provider.start_chat(sender=user_data, message=init_message):
    #     with chat_col.chat_message(
    #         name=msg_iteration['sender']['name'],
    #         avatar=msg_iteration['sender']['avatar']
    #     ):
    #         st.markdown(msg_iteration['text'])
    # add spinner before get response:
    iterator = chat_provider.start_chat(sender=user_data, message=init_message)
    while True:
        try:
            with st.spinner('Wait for the response...'):
                msg_iteration = next(iterator)
        except StopIteration:
            empty_container.markdown(f"## Всего сообщений: {len(st.session_state.messages)}")
            st.success("Чат завершен!")
            break
        except Exception as e:
            st.error(e)
            break
        with chat_col.chat_message(
            name=msg_iteration['sender']['name'],
            avatar=msg_iteration['sender']['avatar']
        ):
            st.markdown(f"[{msg_iteration['sender'].get('name')}]: {remove_quotes(msg_iteration['text'])}")
        empty_container.markdown(f"## Messages: {len(st.session_state.messages)}")
        # empty_container.write(st.session_state.messages)
