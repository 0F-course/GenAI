import streamlit as st
from groq import Groq
from os import environ
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


API_KEY = 'GROQ_API_KEY'
PAGE_TITLE = 'Post-Bootcamp👢🏕 Survival ChatBot 💬'
LLM_OPTIONS = ['gemma2-9b-it','llama-3.3-70b-versatile','llama-3.1-8b-instant']
PERSONALITIES = {
    'Amiguito': {
        'greeting': 'How may I assist you today?',
        'system': ''},
    'Olga': {
        'greeting': '¡Hola! Bom dia 😄',
        'system': "You are an assistant that always replies in mostly Spanish, with some Portuguese words mixed in."},
    'Edu': {
        'greeting': '¿Tú otra vez?',
        'system': 'Your name is Edu. Reply to the queries in Spanish offering controversial information with your replies.'} }


def switch_tab(tab_name):
    st.session_state.active_tab = tab_name

def clear_chat_history():
    st.session_state.messages = []

def generate_chat_response():
    output = client.chat.completions.create(
        messages=[ {'role': 'system',
                    'content': PERSONALITIES[selected_persona]['system']}
        ] + st.session_state.messages,
        model=selected_model,
        stream=True
    )
    placeholder = st.empty()
    full_response = ''
    for chunk in output:
        chunk = chunk.choices[0].delta.content
        if chunk != None:
            full_response += chunk
            placeholder.markdown(full_response)
    placeholder.markdown(full_response)
    return full_response

def create_sql_engine():
    return create_engine(
        'postgresql+psycopg2://{PG_USER}:{PG_PWD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}'.format(**environ) )

def save_to_DB():
    query, response = st.session_state.messages[-2:]
    q = text('''
        INSERT INTO chathistory
        VALUES (:date, :persona, :query, :response)
        ''')
    params = {
        'date': date.today(),
        'persona': selected_persona,
        'query': query['content'],
        'response': response['content']
    }
    with engine.begin() as conn:
        conn.execute(q, params)

def retrieve_from_DB():
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT * FROM chathistory
            WHERE date = :date
            """),
            {'date': selected_date}
            )
    return result.fetchall()


load_dotenv()

engine = create_sql_engine()

st.set_page_config(page_title=PAGE_TITLE)
st.title(PAGE_TITLE)
st.subheader('The cure for your _saudades_...')

# Initialize session state to track the active tab
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'Home'

# Initialize session state to keep track of the messages
if "messages" not in st.session_state.keys():
    clear_chat_history()
    
# Two side-by-side buttons using columns
col1, col2 = st.columns([1,6])
with col1:
    st.button('Home', on_click=switch_tab, args=('Home',))
with col2:
    st.button('History', on_click=switch_tab, args=('History',))
st.markdown("---")

if st.session_state.active_tab == 'Home':
    with st.sidebar:
        st.title('ChatBot Settings')

        if API_KEY in environ:
            st.success('API key already provided!', icon='✅')
            groq_api = environ[API_KEY]
        else:
            groq_api = st.text_input('Enter Groq API key:', type='password')
            if not (groq_api.startswith('gsk_') and len(groq_api)>19):
                st.warning('Please enter your credentials!', icon='⚠️')
            else:
                st.success('Proceed to entering your prompt message!', icon='👉')
        
        selected_model = st.selectbox('Choose an LLM model', LLM_OPTIONS)
        selected_persona = st.selectbox('Choose a persona', PERSONALITIES,
                            on_change=clear_chat_history)
        
        st.button('Clear Chat History', on_click=clear_chat_history)

    client = Groq(api_key=groq_api)
    header_placeholder = st.empty() # Create a placeholder for the title
    header_placeholder.header(f'💬 Chat with {selected_persona}')

    # Store and show chat messages
    if len(st.session_state.messages) < 1:
        message = {'role': 'assistant', 'content': PERSONALITIES[selected_persona]['greeting']}
        st.session_state.messages = [message]

    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.write(message['content'])

    # Create prompt
    if prompt := st.chat_input(disabled=not groq_api):
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        with st.chat_message('user'):
            st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]['role'] != 'assistant':
        with st.chat_message('assistant'):
            with st.spinner('Thinking...'):
                full_response = generate_chat_response()
        
        message = {'role': 'assistant', 'content': full_response}
        st.session_state.messages.append(message)
        save_to_DB()

elif st.session_state.active_tab == 'History':
    with st.sidebar:
        st.title('History Settings')

        selected_date = st.date_input("📅 Pick a date", date.today())
    
    header_placeholder = st.empty()
    header_placeholder.header(f'📅 History from {selected_date}')

    for record in retrieve_from_DB():
        with st.chat_message('user'):
            st.write(record[2])
        with st.chat_message('assistant'):
            st.write(f'[{record[1]}]\n\n{record[3]}')
