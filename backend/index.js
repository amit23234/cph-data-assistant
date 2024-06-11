const express = require('express');
const { Client } = require("pg");
const { OpenAI } = require("openai");
const dotenv = require('dotenv');
const fs = require("fs");

dotenv.config();

const app = express();
app.use(express.json());

let databaseInformation = ""; // The information layer between GPT and the database

function readFile(filePath) {
    databaseInformation = fs.readFileSync(filePath, 'utf8');
}
readFile('informationLayer.txt');

async function executeSqlQuery(sqlQuery) {
    const client = new Client({
        host: process.env.dbHostname,
        database: process.env.dbDatabase,
        user: process.env.dbUsername,
        password: process.env.dbPassword,
        port: process.env.dbPortId,
    });
    
    await client.connect();
    const res = await client.query(sqlQuery);
    await client.end();
    return res.rows;
}

async function formatOutput(sqlResult, userInput) {
    const openai = new OpenAI(api_key=process.env.OPENAI_API_KEY);

    const completion = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
            { role: "system", content: `You are a data analyst for a pizza franchise called Curry Pizza House. You manage the database of the company which is in Postgres. Here is the database information for you ${databaseInformation}. You receive text input of what data the user wants and the sql query result for the appropriate sql query. Whenever you talk numbers, give output them in the format: xxx,xxx,xxx.xx if decimals or xxx,xxx,xxx if integers. You are supposed to output the result of the sql in plain english.` },
            { role: "assistant", content: "The output will be the answer to the question asked in user input in a sentence form." },
            { role: "user", content: `Here is the user input ${userInput} and here is the result of the sql query ${JSON.stringify(sqlResult)}. Can you output this in simple english?` }
        ],
        stop: null,
        temperature: 0
    });
    console.log("format Output : ", completion.usage)
    const content = completion.choices[0].message.content;
    return content;
}

app.post('/query', async (req, res) => {
    const openai = new OpenAI(api_key=process.env.OPENAI_API_KEY);
    const userInput = req.body.input;
    const todayDate = new Date().toISOString().split('T')[0];

    const completion = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
            { role: "system", content: `You are a data analyst for a pizza franchise called Curry Pizza House. You manage the database of the company which is in Postgres. Here is the database information for you ${databaseInformation}. You receive text input and are designed to output a sql query based on it. For relevance, today's date is ${todayDate}` },
            { role: "assistant", content: "The output will be a sql query which is ready to be run in postgres" },
            { role: "user", content: `Here is the user input ${userInput}. Can you give a sql query?` }
        ],
        stop: null,
        temperature: 0
    });

    console.log('create sql query : ', completion.usage)
    const sqlQuery = completion.choices[0].message.content.match(/```sql\n(.*?)\n```/s)[1];
    console.log("sql query : ", sqlQuery)

    const sqlResult = await executeSqlQuery(sqlQuery)
    console.log("sqlResult : ", sqlResult)
    const output = await formatOutput(sqlResult, userInput)
    console.log("output : ", output)
    res.json(output);

    // dbClient.query(sqlQuery, (err, result) => {
    // if (err) {
    //     res.status(500).json({ error: err.message });
    // } else {
    //     res.json(result.rows);
    // }
    // });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
