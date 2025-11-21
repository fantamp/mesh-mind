import os
import sys
import shutil
import tempfile
from typing import List, Dict
from loguru import logger

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_core.rag.vector_db import VectorDB
from ai_core.agents import qa

# Sample Data: Similar Emails
EMAILS = [
    {
        "text": """
Subject: Project Alpha Update - Q1
Date: 2024-01-15
From: alice@example.com
To: team@example.com

Hi Team,
Here is the Q1 update for Project Alpha.
- Budget utilized: $50,000
- Key milestone: Prototype completed.
- Next steps: User testing.
Regards, Alice
""",
        "metadata": {"source": "email_alpha_q1.txt", "date": "2024-01-15"}
    },
    {
        "text": """
Subject: Project Alpha Update - Q2
Date: 2024-04-15
From: alice@example.com
To: team@example.com

Hi Team,
Here is the Q2 update for Project Alpha.
- Budget utilized: $120,000 (Cumulative)
- Key milestone: Beta launch.
- Next steps: Marketing campaign.
Regards, Alice
""",
        "metadata": {"source": "email_alpha_q2.txt", "date": "2024-04-15"}
    },
    {
        "text": """
Subject: Secret Code for Server Access
Date: 2024-02-20
From: bob@example.com
To: devops@example.com

The secret code for the production server is: 998877.
Do not share this with anyone.
""",
        "metadata": {"source": "secret_code.txt", "date": "2024-02-20"}
    }
]

TEST_CASES = [
    {
        "query": "What was the budget utilized in Q1 for Project Alpha?",
        "expected_answer": "$50,000",
        "expected_source": "email_alpha_q1.txt"
    },
    {
        "query": "What is the key milestone for Project Alpha in Q2?",
        "expected_answer": "Beta launch",
        "expected_source": "email_alpha_q2.txt"
    },
    {
        "query": "What is the secret code for the server?",
        "expected_answer": "998877",
        "expected_source": "secret_code.txt"
    },
    {
        "query": "Who sent the Q1 update?",
        "expected_answer": "Alice",
        "expected_source": "email_alpha_q1.txt"
    }
]

def run_manual_test():
    # Create a temporary directory for the test VectorDB
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Created temporary VectorDB at {temp_dir}")

    try:
        # Initialize VectorDB in the temp directory
        vector_db = VectorDB(persist_directory=temp_dir)
        
        # Ingest emails
        logger.info("Ingesting sample emails...")
        texts = [e["text"] for e in EMAILS]
        metadatas = [e["metadata"] for e in EMAILS]
        vector_db.add_texts(texts=texts, metadatas=metadatas)
        
        # Patch the global vector store in qa module
        # This is a bit hacky but necessary for manual testing without dependency injection in the module
        original_store = qa._vector_store
        qa._vector_store = vector_db
        
        logger.info("Starting QA Test Cases...\n")
        
        for i, case in enumerate(TEST_CASES, 1):
            query = case["query"]
            expected = case["expected_answer"]
            expected_src = case["expected_source"]
            
            print(f"--- Test Case {i} ---")
            print(f"Query: {query}")
            print(f"Expected Fact: {expected}")
            print(f"Expected Source: {expected_src}")
            
            try:
                # Call the agent
                response = qa.ask_question(query, user_id="manual_tester")
                
                print(f"\nAgent Response:\n{response}\n")
                
                # Basic verification
                if expected.lower() in response.lower():
                    print("✅ Answer contains expected fact.")
                else:
                    print("❌ Answer MISSING expected fact.")
                    
                if expected_src in response:
                    print("✅ Source correctly cited.")
                else:
                    print("❌ Source citation MISSING or INCORRECT.")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n" + "="*50 + "\n")
            
        # Restore original store (though script ends here)
        qa._vector_store = original_store

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        logger.info(f"Removed temporary directory {temp_dir}")

if __name__ == "__main__":
    run_manual_test()
