import streamlit as st
import requests

st.title("CPH Data Assistant")

user_input = st.text_input("What information do you want to know? Don't forget to mention the time range :)")

if st.button("Submit"):
    response = requests.post('http://localhost:3000/query', json={'input': user_input})

    if response.status_code == 200:
        if 'image' in response.headers.get('Content-Type'):
            st.image(response.content)
        else:
            st.write("Query Result:")
            st.write(response.json())
    else:
        st.write("Error:", response.json().get('error'))
