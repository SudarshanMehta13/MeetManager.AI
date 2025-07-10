import requests
import xml.etree.ElementTree as ET
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
CDETS_API_URL = "https://cdetsng.cisco.com/wsapi/latest/api/bug/"  # Updated CDETS API URL

def fetch_cdets_bug_status(bug_id):
    """Fetch the status of a CDETS bug using its ID and a bearer token."""
    token = os.getenv("BEARER_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{CDETS_API_URL}{bug_id}", headers=headers)

    if response.status_code == 200:
        try:
            root = ET.fromstring(response.text)
            
            # Extract namespace dynamically
            namespace = {'cdets': root.tag.split('}')[0].strip('{')}
            
            fields_to_extract = [
                "Activity-when-found", "Assigned Date", "Assigner", "Attribute", "DE Priority Desc",
                "DE-manager", "DE-priority", "DTPT-manager", "Data-classification", "Description", "Doc-manager",
                "Engineer", "Feature", "Regression", "Regression-submitter",
                "Release-Ops-Manager", "Reti-bug", "Severity", "Severity-desc",
                "Solution-impacted", "Status", "Status-desc", "Submitted-on", "Submitter", "Submitter-manager",
                "Submitter-org-bug"
            ]
            
            bug_info = {}
            # Use namespace in XPath to find Field elements
            for field in root.findall('.//cdets:Field', namespaces=namespace):
                field_name = field.attrib['name']
                if field_name in fields_to_extract:
                    bug_info[field_name] = field.text
            
            # Format the output with line breaks
            formatted_string = "\n".join(f"{key}: {value}" for key, value in bug_info.items())
            return f"```\nThe status of bug {bug_id} is:\n{formatted_string}\n```"
        except ET.ParseError:
            return "Error parsing XML response"
    else:
        return f"Error fetching bug status: {response.status_code}, {response.text}"

def fetch_cdets_bug_id(s): 
    return re.findall(r'\bCSC\w{2}\d{5}\b', s)

def fetch_meet(s):
    """Return True if the input string contains the word 'meet' (case-insensitive), otherwise False."""
    return "meet" in s.lower()

def update_cdets_bug(bug_id, xml_body):
    """Update a field of a CDETS bug using its ID, field name, and new value."""
    token = os.getenv("BEARER_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/xml"
    }
    
    xml_body = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<Defect xmlns="cdetsng" xmlns:ns1="http://www.w3.org/1999/xlink" id="{bug_id}">
{xml_body}
</Defect>"""
    
    response = requests.post(f"{CDETS_API_URL}{bug_id}", headers=headers, data=xml_body)
    
    if response.status_code == 200:
        return f"Bug {bug_id} updated successfully."
    else:
        return f"Error updating bug: {response.status_code}, {response.text}"