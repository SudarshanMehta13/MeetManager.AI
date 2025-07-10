import os
from io import StringIO
import webvtt
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from datetime import datetime
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from TryingOutLoud_cdetsBug import fetch_cdets_bug_status, fetch_cdets_bug_id

# Load environment variables
load_dotenv()
api_version = os.getenv("api_version")
endpoint = os.getenv("endpoint")
webex_api_key = os.getenv("webex_api_key")

def load_vtt(files):
    """Load and parse VTT files, appending the date from the filename to each line."""
    text = ""
    for file in files:
        file_content = file.read().decode('utf-8')
        vtt_content = StringIO(file_content)
        date = file.name.split('.')[0]  # Extract date from filename (e.g., 2024-05-11 from 2024-05-11.vtt)
        for caption in webvtt.read_buffer(vtt_content):
            # Append the date to each line for context-based date filtering
            text += f"{date} {caption.start} --> {caption.end}\n{date} {caption.text}\n\n"
    return text

def get_text_chunks(text):
    """Split the text into chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    """Create a vector store from text chunks."""
    embeddings = AzureOpenAIEmbeddings(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=webex_api_key,
        chunk_size=500,
        show_progress_bar=True,
    )
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    """Create a conversational chain with a customized prompt template."""
    prompt_template = """
You will be provided with Webex meeting transcripts in VTT format with the naming as date.
I am appending date (in format like this - 05-11-2024) of the meet to every discussion, so if I provide mutiple VTT meeting transcripts,
I do not loose each meet specific discussion. The date is appended at the start of every discussion, this date is
when that meet hapeened and so when that discussion happened, you can utilize this date to answer date or specif 
dated meeting questions. The responses you return back, let it be very proffesional and everything related to work
Mention only relevant details. Do not tell anything about greetings and all. Just work related.

One usecase could be to summarize date wise these meetings, or tell date wise the meet attendees, etc.
 These transcripts are from software development team meetings 
that cover topics such as project updates, task assignments, blockers, and other discussions among team members. Using this 
information, generate responses to specific questions by extracting only the requested details without adding unrelated information.
 
Use the transcript to provide focused answers to questions like:
Summaries: Provide an overview of the meeting’s main points, covering key topics, project updates, and decisions made.
Tasks and Action Items: List all tasks discussed, specifying descriptions, assigned team members, and deadlines or timeframes.
Issues and Blockers: Highlight challenges such as code, design, or testing issues, along with suggested solutions or follow-ups.
Attendees and Contributions: Identify attendees, their roles (if mentioned), and key contributions, along with timestamps.
Code and Testing Discussions: Detail any code modules, features, or testing phases discussed, including dependencies or quality measures.
External Tools or Documents: Mention any tools (e.g., Git, Jira) or external documents referenced, such as links to wikis or diagrams.
Clarifications or Follow-ups: Capture requests for additional details or clarifications and note any planned follow-ups.
Team Dynamics: Summarize any team dynamics or decision-making processes, including consensus or differing opinions.
Example Questions:

“Summarize the main points of the meeting.”
“List all tasks discussed.”
“List all to-do tasks pending.”
“What are the blockers the team mentioned?”
“Who was assigned each task, and what were the deadlines?”
“Summarize any code changes or testing requirements discussed.”
“Summarize the discussions on open bugs”
“Summarize the discussions on any pending open tasks”

Also there is a usecase, where a cdets bug (bug id) may be provided, the format is CSCxxxxxxx, where x could be any value
You have to return the discussion happened in the meeting around that bug id.
Ex 174 "Arati Pradhan" (837281536)
00:32:29.372 --> 00:32:30.389
Then for this bug CSCwn10116, so did anyone checked our current sonar coverage


177 "Sudarshan Mehta" (3514603264)
00:32:56.899 --> 00:33:04.690
Hi Arati

174 "Arati Pradhan" (837281536)
00:32:29.372 --> 00:32:30.389
Hi, hi Sudarshan

177 "Sudarshan Mehta" (3514603264)
00:32:56.899 --> 00:33:04.690
Yes so for this bug - CSCwn10116, the current coverage coming from sonar included the UI files also. So Udaya has pinged in the common webex space, to remove UI files

177 "Sudarshan Mehta" (3514603264)
00:32:56.899 --> 00:33:04.690
After UI files, need to again check, will try to reach 95+ coverage.

174 "Arati Pradhan" (837281536)
00:32:29.372 --> 00:32:30.389
Yes also look for blockers in sonar report. The code quality needs to be matched.

177 "Sudarshan Mehta" (3514603264)
00:32:56.899 --> 00:33:04.690
Yes Arati

174 "Arati Pradhan" (837281536)
00:32:29.372 --> 00:32:30.389
Yes also post that mark it to R, if code quality and coverage is all good. Close on this one.
The above entire discussion happened on a cdets bug. If user inputs this specific bug in question, briefly tell about
the discussion. Similarly it could ask for any other bug (the bug id format will be CSCxxxxxxx),
look in trancsript what was the discussion around that and response back. Be specific to only that 
particular cdets bug discussion.



Also there is another use case:
    observe this line from VTT transcript - 123 "Sudarshan Mehta" (856851200)
00:13:17.663 --> 00:13:21.991
Right. So, in my ideas, so I do. What this is useful is to figure out who said this in the meet. In the above text pattern
the person is Sudarshan Mehta. Based on this pattern you would may have to figure out who raised a particular point 
in the meet. Similarly based on the transcripts line, You also need to check different team members name, 
present similarly under double quates and in a similar pattern. You may list down all such names in a single 
line with comma separation so to get list of all attendees/ members of the meet. 
You may be asked questions on these names and their relevant conversation or discussion point.

There is another use case. Once you are able to figure out the team meeting attendees from looking for them in 
each line being discussed, as they would have spoken that discussion, and also figure out topics/ points 
raisedby each one of them, you may be capable to summarize the topics discussed by each team member, by 
listing down name wise the team member and the discussion done by them.

In the response do not mention anything about transcripts. 
Given the provided VTT context, answer questions with detailed information and also in bullet points.
When responding, include relevant names and any actionable insights available, focusing solely on the question's intent.
Do not provide additional not needed information.
If the answer is not within the scope of the transcript then reply back "Not discussed in the meet!!"
Context:
{context}

Question: 
{question}
    """
    llm = AzureChatOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=webex_api_key,
        temperature=0.4,
        model="gpt-4o",
        verbose=True,
    )
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
    return chain


def extract_date_from_question(question):
    """Extracts a date from the question if mentioned in a recognizable format."""
    date_formats = ["%d-%m-%Y", "%Y-%m-%d"]  # Add more formats if needed
    words = question.split()
    for word in words:
        for date_format in date_formats:
            try:
                return datetime.strptime(word, date_format).date()
            except ValueError:
                continue
    return None

def user_input(user_question):
    """Process user input and return responses based on the VTT transcript."""
    try:
        embeddings = AzureOpenAIEmbeddings(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=webex_api_key,
            chunk_size=500,
            show_progress_bar=True,
        )
        new_db = FAISS.load_local("../faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)
        chain = get_conversational_chain()
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    except Exception as e:
        response = f"Error processing the request: {str(e)}"
    return response

def analyze_cdets_intent(question):
    """Analyze the user question to determine the intent related to a CDETS bug ID using Azure OpenAI."""
    intent_template = """
You will be provided with a user question that may involve a CDETS bug ID or a username which involves PR operations
Your task is to determine the intent behind the question.
The possible intents are:
- fetch_cdets: The user wants to fetch or find the discussion on the CDETS bug, summarize the CDETS bug, 
    get the CDETS bug status, or know the status of a CDETS bug. Ensure there is no mention of discussion 
    around the bug in the meeting or anything related to a meeting.
- update_cdets: The user wants to update a CDETS bug by changing some fields.
- create_cdets: The user wants to create a new CDETS bug.
- delete_cdets: The user wants to delete or junk a CDETS bug.
- fetch_open_prs: The user wants to fetch open Bitbucket pull requests for a specific user.
- fetch_merged_prs: The user wants to fetch merged Bitbucket pull requests for a specific user.
- trigger_jenkins_build: The user wants to trigger a Jenkins build.
- unknown: The intent is not clear or is unrelated to CDETS bugs. If the user question includes a 
    request for a discussion on <CDETS bug ID> in the context of a meeting, classify it as 'fetch'.

Question:
{question}

Respond with the intent only.
"""
    llm = AzureChatOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=webex_api_key,
        temperature=0.4,
        model="gpt-4o",
        verbose=True,
    )
    prompt = PromptTemplate(template=intent_template, input_variables=["question"])
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    response = llm_chain.run(question)
    return response.strip()

def extract_user_id(question):
    """Extract user ID from the question using Azure OpenAI."""
    user_id_template = """
You will be provided with a user question that may involve asking for Bitbucket pull requests.
Your task is to extract the user ID mentioned in the question.

Question:
{question}

Respond with the user ID only.
"""
    llm = AzureChatOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=webex_api_key,
        temperature=0.4,
        model="gpt-4o",
        verbose=True,
    )
    prompt = PromptTemplate(template=user_id_template, input_variables=["question"])
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    response = llm_chain.run(question)
    return response.strip()