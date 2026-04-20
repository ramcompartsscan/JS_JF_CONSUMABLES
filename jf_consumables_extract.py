#!/usr/bin/env python3
"""
JotForm Consumables Extractor
Fetches form fields, conditions and table data from JotForm API
"""
import json
import csv
import pandas as pd
from pathlib import Path
from jotform import JotformAPIClient
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration from Instruction7.md
API_KEY = '5f4e3bc0a32c6c059d87badc84e26842'
FORM_ID = '260621145322041'
FIELDS_OUTPUT_FILE = Path('jf_fields_conditions.md')
TABLE_OUTPUT_FILE = Path('jf_consumables_table.csv')

def fetch_form_properties(client, form_id: str) -> dict:
    """Fetch form properties including fields and conditions"""
    try:
        form_props = client.get_form(form_id)
        return form_props
    except Exception as e:
        logger.error(f"Error fetching form properties: {e}")
        return {}

def fetch_form_questions(client, form_id: str) -> dict:
    """Fetch form questions/fields"""
    try:
        questions = client.get_form_questions(form_id)
        return questions
    except Exception as e:
        logger.error(f"Error fetching form questions: {e}")
        return {}

def fetch_table_data(client, form_id: str) -> list:
    """Fetch table data from JotForm Tables"""
    try:
        # Fetch submissions which contain the table data
        submissions = client.get_form_submissions(form_id)
        if isinstance(submissions, dict) and 'content' in submissions:
            return submissions['content']
        return submissions if isinstance(submissions, list) else []
    except Exception as e:
        logger.error(f"Error fetching table data: {e}")
        return []

def extract_fields_and_conditions(form_props: dict, questions: dict) -> str:
    """Extract fields and conditions information and format as markdown"""
    md_content = "# JotForm Fields and Conditions\n\n"

    # Add form properties
    md_content += "## Form Properties\n\n"
    if form_props:
        md_content += f"- **Form ID**: {form_props.get('id', 'N/A')}\n"
        md_content += f"- **Form Title**: {form_props.get('title', 'N/A')}\n"
        md_content += f"- **Created At**: {form_props.get('created_at', 'N/A')}\n"
        md_content += f"- **Status**: {form_props.get('status', 'N/A')}\n\n"

    # Add fields information
    md_content += "## Form Fields\n\n"
    if questions:
        for qid, question in questions.items():
            md_content += f"### Field ID: {qid}\n"
            md_content += f"- **Type**: {question.get('type', 'N/A')}\n"
            md_content += f"- **Text**: {question.get('text', 'N/A')}\n"
            md_content += f"- **Name**: {question.get('name', 'N/A')}\n"
            md_content += f"- **Order**: {question.get('order', 'N/A')}\n"

            # Add validation if exists
            if 'validation' in question:
                md_content += f"- **Validation**: {question['validation']}\n"

            # Add required status
            md_content += f"- **Required**: {question.get('required', 'No')}\n\n"
    else:
        md_content += "No fields found.\n\n"

    # Add conditions information
    md_content += "## Form Conditions\n\n"
    if form_props and 'properties' in form_props:
        properties = form_props['properties']
        if 'conditions' in properties:
            conditions = properties['conditions']
            for i, condition in enumerate(conditions):
                md_content += f"### Condition {i+1}\n"
                md_content += f"- **Type**: {condition.get('type', 'N/A')}\n"
                md_content += f"- **Action**: {condition.get('action', 'N/A')}\n"
                md_content += f"- **Details**: {json.dumps(condition, indent=2)}\n\n"
        else:
            md_content += "No conditions found.\n\n"
    else:
        md_content += "No conditions data available.\n\n"

    return md_content

def extract_table_data(submissions: list) -> pd.DataFrame:
    """Extract table data from submissions"""
    if not submissions:
        logger.warning("No submissions to extract.")
        return pd.DataFrame()

    # Flatten the submission data
    data = []
    for sub in submissions:
        row = {
            'submission_id': sub.get('id', 'Unknown'),
            'created_at': sub.get('created_at', 'Unknown'),
        }

        # Extract answers
        answers = sub.get('answers', {})
        for qid, answer_data in answers.items():
            if isinstance(answer_data, dict) and 'answer' in answer_data:
                answer = answer_data['answer']
                # Handle different answer formats
                if isinstance(answer, dict):
                    # For date fields or other structured data
                    row[f'field_{qid}'] = json.dumps(answer)
                else:
                    row[f'field_{qid}'] = str(answer)
            else:
                row[f'field_{qid}'] = str(answer_data)

        data.append(row)

    df = pd.DataFrame(data)
    return df

def main():
    """Main extraction function"""
    logger.info("=" * 60)
    logger.info("JotForm Consumables Extractor")
    logger.info("=" * 60)

    try:
        # Connect to JotForm
        client = JotformAPIClient(API_KEY)
        logger.info(f"🔌 Connected to JotForm API")

        # Fetch form properties and questions
        logger.info(f"📥 Fetching form properties for {FORM_ID}...")
        form_props = fetch_form_properties(client, FORM_ID)

        logger.info(f"📥 Fetching form questions for {FORM_ID}...")
        questions = fetch_form_questions(client, FORM_ID)

        # Extract fields and conditions to markdown
        logger.info("🔄 Extracting fields and conditions...")
        md_content = extract_fields_and_conditions(form_props, questions)

        # Save fields and conditions to markdown file
        logger.info(f"💾 Saving fields and conditions to {FIELDS_OUTPUT_FILE}...")
        with open(FIELDS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"✅ Fields and conditions saved to {FIELDS_OUTPUT_FILE}")

        # Fetch table data
        logger.info(f"📥 Fetching table data from form {FORM_ID}...")
        submissions = fetch_table_data(client, FORM_ID)

        if not submissions:
            logger.warning("No table data retrieved from API")
        else:
            logger.info(f"✅ Retrieved {len(submissions)} submissions")

            # Extract table data
            logger.info("🔄 Extracting table data...")
            df = extract_table_data(submissions)

            if not df.empty:
                logger.info(f"✅ Extracted {len(df)} records")

                # Save to CSV
                logger.info(f"💾 Saving table data to {TABLE_OUTPUT_FILE}...")
                df.to_csv(TABLE_OUTPUT_FILE, index=False, encoding='utf-8')
                logger.info(f"✅ Table data saved to {TABLE_OUTPUT_FILE}")
            else:
                logger.warning("No table data extracted")
                # Create empty CSV file
                TABLE_OUTPUT_FILE.touch()
                logger.info(f"✅ Created empty table file {TABLE_OUTPUT_FILE}")

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("EXTRACTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Fields and Conditions File: {FIELDS_OUTPUT_FILE}")
        logger.info(f"Table Data File: {TABLE_OUTPUT_FILE}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)