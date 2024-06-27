import streamlit as st
import requests
import pandas as pd
from io import StringIO, BytesIO

st.title("CPH Data Assistant")

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'formatted' not in st.session_state:
    st.session_state.formatted = False

# Text input on its own line
user_input = st.text_input("What information do you want to know? Don't forget to mention the time range :)")

# Submit and download buttons on the same line
col1, col2, col3 = st.columns([0.15, 0.3, 0.6])
with col1:
    submit_button = st.button("Search")
with col3:
    format_button = st.button("Format Text")

def generate_download_button():
    raw_data = st.session_state.result['raw_data']
    if isinstance(raw_data, list) and all(isinstance(i, dict) for i in raw_data):
        df = pd.DataFrame(raw_data)
        csv = df.to_csv(index=False) # Generate CSV
        b = BytesIO() # Convert CSV string to bytes
        b.write(csv.encode('utf-8'))
        b.seek(0)
        # Create a download button
        st.download_button(
            label="Download data as CSV",
            data=b,
            file_name='query_result.csv',
            mime='text/csv',
        )

if submit_button:
    response = requests.post('http://localhost:8080/query', json={'input': user_input})

    if response.status_code == 200:
        result = response.json()
        # st.write("Raw data received from backend:", result)  # Display raw JSON data
        st.session_state.result = result  # Store result in session state
        # st.write("stored state 1 : ", st.session_state.result)
        st.session_state.formatted = False  # Reset formatted state
    else:
        st.write("Error:", response.json().get('error'))

# Handle format button click
if format_button:
    st.session_state.formatted = not st.session_state.formatted

# Display stored result
if st.session_state.result:
    result = st.session_state.result
    output = st.session_state.result['formatted_output']
    # st.write("stored state 2 : ", st.session_state.result)
    
    # # st.write("Output:")
    # # st.write(output)
    # st.markdown(output.replace('$', '\$').replace('%', '\%'))  # Escape $ and % characters

    if st.session_state.formatted:
        st.markdown(output.replace('$', '\$').replace('%', '\%'))  # Escape $ and % characters
    else:
        st.write(output)

    #Display the download button if the result exists 
    with col2:
        generate_download_button()

