import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import cProfile
import pstats
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = Flask(__name__)

database_information = ""  # The information layer between GPT and the database
with open('informationLayer.txt', 'r') as file:
    database_information = file.read()

# def profile(func):
#     def wrapper(*args, **kwargs):
#         pr = cProfile.Profile()
#         pr.enable()
#         result = func(*args, **kwargs)
#         pr.disable()
#         s = io.StringIO()
#         ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
#         ps.print_stats(10)  # Print top 10 time-consuming functions
#         logger.info(f"Profile for {func.__name__}:\n{s.getvalue()}")
#         return result
#     return wrapper

# @profile
def execute_sql_query(sql_query):
    conn = psycopg2.connect(
        host=os.getenv('dbHostname'),
        database=os.getenv('dbDatabase'),
        user=os.getenv('dbUsername'),
        password=os.getenv('dbPassword'),
        port=os.getenv('dbPortId')
    )
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql_query)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

# @profile
def format_output(sql_result, user_input):
    client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"You are a data analyst for a pizza franchise called Curry Pizza House. You manage the database of the company which is in Postgres. Here is the database information for you {database_information}. You receive text input of what data the user wants and the sql query result for the appropriate sql query. Whenever you talk numbers, give output them in the format: xxx,xxx,xxx.xx if decimals or xxx,xxx,xxx if integers. You are supposed to output the result of the sql in plain english."},
            {"role": "assistant", "content": "The output will be the answer to the question asked in user input in a sentence form."},
            {"role": "user", "content": f"Here is the user input {user_input} and here is the result of the sql query {sql_result}. Can you output this in simple english?"}
        ],
        temperature=0
    )
    
    print("format Output : ", completion.usage)
    content = completion.choices[0].message.content
    return content

@app.route('/query', methods=['POST'])
# @profile
def query():
    client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    user_input = request.json['input']
    today_date = datetime.now().strftime("%Y-%m-%d")

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"You are a data analyst for a pizza franchise called Curry Pizza House. You manage the database of the company which is in Postgres. Here is the database information for you {database_information}. You receive text input and are designed to output a sql query based on it. For relevance, today's date is {today_date}"},
            {"role": "assistant", "content": "The output will be a sql query which is ready to be run in postgres"},
            {"role": "user", "content": f"Here is the user input {user_input}. Can you give a sql query?"}
        ],
        temperature=0
    )

    print('create sql query : ', completion.usage)
    print()
    sql_query = completion.choices[0].message.content.split('```sql\n')[1].split('\n```')[0]
    print("sql query : ", sql_query)

    sql_result = execute_sql_query(sql_query)
    print("sqlResult : ", sql_result)
    output = format_output(sql_result, user_input)
    print("output : ", output)
    return jsonify({
            "formatted_output": output,
            "raw_data": sql_result
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)