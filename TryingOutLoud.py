import streamlit as st
import os
import re
import sys
import logging
from dotenv import load_dotenv
from TryingOutLoud_genAI import get_vector_store, load_vtt, get_text_chunks, user_input, analyze_cdets_intent, extract_user_id
from TryingOutLoud_cdetsBug import fetch_cdets_bug_id, fetch_cdets_bug_status, update_cdets_bug, fetch_meet
from TryingOutLoud_bitbucket import fetch_merged_pull_requests_for_user, fetch_open_pull_requests_for_user, BITBUCKET_PR_URL_TEMPLATE
from TryingOutLoud_jenkins import trigger_jenkins_build

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.DEBUG)

def main(user_question):
    logging.debug("Entered Loading.py")
    """Process the user input and return a response string."""
    # Load the token from environment variables
    token = os.getenv("BEARER_TOKEN")
    logging.debug("token: "+token)
    # Ensure a valid token and user question
    if not user_question or not token:
        return "Invalid token or no user question provided."

    response = "No valid response generated."  # Initialize the response variable

    # Process the question for CDETS intent and VTT meet extraction logic
    bug_ids = fetch_cdets_bug_id(user_question)
    is_meet = fetch_meet(user_question)
    intent = analyze_cdets_intent(user_question)

    if intent == "trigger_jenkins_build":
        response = trigger_jenkins_build()
    elif bug_ids and not is_meet:
        if intent == "fetch_cdets":
            if "meet" in user_question.lower():
                response = user_input(user_question)
            else:
                response = fetch_cdets_bug_status(bug_ids[0])
        elif intent == "update_cdets":
            # Logic to update CDETS
            # This requires user input for field-value pairs which would have been handled in UI
            # Here, we'll need a predefined set of field-value pairs or an alternative approach
            response = "Update CDETS logic requires field-value pairs."
        elif intent == "create_cdets":
            response = "Create bug logic not implemented yet."
        elif intent == "delete_cdets":
            response = "Delete bug logic not implemented yet."
        else:
            response = "Unrecognized intent."
    elif intent in ["fetch_open_prs", "fetch_merged_prs"]:
        cdets_id = re.findall(r'\bCSC\w*\b', user_question)
        user_id = extract_user_id(user_question)
        if intent == "fetch_open_prs":
            open_prs = fetch_open_pull_requests_for_user(user_id)
            if open_prs:
                response = "Open Pull Requests:\n" + "\n".join(
                    [f"- PR ID: {pr['id']}, Title: {pr['title']}, Author: {pr['author']['user']['displayName']}, URL: {BITBUCKET_PR_URL_TEMPLATE.format(pr['id'])}" for pr in open_prs])
            else:
                response = "No open pull requests found or an error occurred."
        elif intent == "fetch_merged_prs":
            merged_prs = fetch_merged_pull_requests_for_user(user_id)
            if merged_prs:
                response = "Merged Pull Requests:\n" + "\n".join(
                    [f"- PR ID: {pr['id']}, Title: {pr['title']}, Author: {pr['author']['user']['displayName']}, URL: {BITBUCKET_PR_URL_TEMPLATE.format(pr['id'])}" for pr in merged_prs])
            else:
                response = "No merged pull requests found or an error occurred."
    else:
        response = user_input(user_question)["output_text"]

    return response









    # """Main Streamlit application."""
    # st.set_page_config(page_title="Chat with Webex Recordings")
    # st.header("Chat with Webex recordings 💬")

    # # Load the token from environment variables
    # token = os.getenv("BEARER_TOKEN")

    # #user_question = st.text_input("Ask a Question from the VTT Files")


    # # Check if a user question is provided via command-line argument
    # user_question = None
    # if len(sys.argv) > 1:
    #     user_question = sys.argv[1]

    # # If no command-line argument, use Streamlit text input
    # if not user_question:
    #     user_question = st.text_input("Ask a Question from the VTT Files")


    # # Initialize session state for dynamic fields
    # if 'field_value_pairs' not in st.session_state:
    #     st.session_state.field_value_pairs = [""]

    # if user_question and token and st.button("Ask"):
    #     with st.spinner("Analyzing..."):
    #         response = "No valid response generated."  # Initialize the response variable
    #         # Process the question for CDETS intent and VTT meet extraction logic
    #         bug_ids = fetch_cdets_bug_id(user_question)
    #         is_meet = fetch_meet(user_question)
    #         intent = analyze_cdets_intent(user_question)
    #         if intent == "trigger_jenkins_build":
    #             response = trigger_jenkins_build()
    #         elif bug_ids and not is_meet:
    #             if intent == "fetch_cdets":
    #                 if "meet" in user_question.lower():
    #                     response = user_input(user_question)
    #                 else:
    #                     response = fetch_cdets_bug_status(bug_ids[0])
    #             elif intent == "update_cdets":
    #                 # Dynamic input fields for field-value pairs
    #                 st.subheader("Enter Field-Value Pairs (format: fieldName-fieldValue)")

    #                 # Iterate through the current field-value pairs and create input boxes for each
    #                 for i, pair in enumerate(st.session_state.field_value_pairs):
    #                     st.session_state.field_value_pairs[i] = st.text_input(f"Field-Value Pair {i+1}", value=pair, key=f"field_value_pair_{i}")

    #                 # Button to add more input boxes
    #                 if st.button("Add More Field-Value Pair"):
    #                     st.session_state.field_value_pairs.append("")

    #                 # Ensure field_value_pairs is filled before processing
    #                 if st.session_state.field_value_pairs:
    #                     valid_pairs = [pair for pair in st.session_state.field_value_pairs if '-' in pair]
    #                     if valid_pairs:
    #                         fields = []
    #                         for pair in valid_pairs:
    #                             field_name, field_value = pair.split('-', 1)
    #                             fields.append(f'<Field name="{field_name.strip()}">{field_value.strip()}</Field>')
    #                         xml_body = "\n".join(fields)
    #                         response = update_cdets_bug(bug_ids[0], xml_body)
    #                         st.session_state.field_value_pairs = [""]  # Clear after submission
    #                     else:
    #                         st.error("Please provide valid field-value pairs before submitting.")
    #             elif intent == "create_cdets":
    #                     response = "Create bug logic not implemented yet."
    #             elif intent == "delete_cdets":
    #                 response = "Delete bug logic not implemented yet."
    #             else:
    #                 response = "Unrecognized intent."
    #         elif intent in ["fetch_open_prs", "fetch_merged_prs"]:
    #             cdets_id = re.findall(r'\bCSC\w*\b', user_question)
    #             user_id = extract_user_id(user_question)
    #             if intent == "fetch_open_prs":
    #                 open_prs = fetch_open_pull_requests_for_user(user_id)
    #                 if open_prs:
    #                     response = "Open Pull Requests:\n" + "\n".join(
    #                         [f"- PR ID: {pr['id']}, Title: {pr['title']}, Author: {pr['author']['user']['displayName']}, URL: {BITBUCKET_PR_URL_TEMPLATE.format(pr['id'])}" for pr in open_prs])
    #                 else:
    #                     response = "No open pull requests found or an error occurred."
    #             elif intent == "fetch_merged_prs":
    #                 merged_prs = fetch_merged_pull_requests_for_user(user_id)
    #                 if merged_prs:
    #                     response = "Merged Pull Requests:\n" + "\n".join(
    #                         [f"- PR ID: {pr['id']}, Title: {pr['title']}, Author: {pr['author']['user']['displayName']}, URL: {BITBUCKET_PR_URL_TEMPLATE.format(pr['id'])}" for pr in merged_prs])
    #                 else:
    #                     response = "No merged pull requests found or an error occurred."
    #         else:
    #             response = user_input(user_question)
    #         #added this too
    #         #print(response) 
    #         st.markdown(response, unsafe_allow_html=True)

    # with st.sidebar:
    #     st.title("Webex Transcript:")
    #     vtt_files = st.file_uploader("Choose VTT files and Click on the Submit & Process  Button", accept_multiple_files=True, type="vtt")
    #     if st.button("Submit & Process"):
    #         if vtt_files:
    #             with st.spinner("Processing..."):
    #                 raw_text = load_vtt(vtt_files)  # Load and combine all VTT files
    #                 text_chunks = get_text_chunks(raw_text)  # Split combined text into chunks
    #                 get_vector_store(text_chunks)  # Create vector store from chunks
    #                 st.success("Done")
    #         else:
    #             st.error("Please upload at least one VTT file.")

if __name__ == "__main__":
    # For Debugging
    # main()
    if len(sys.argv) > 1:
        input_message = sys.argv[1] 
        response = main(input_message)
        print(response)