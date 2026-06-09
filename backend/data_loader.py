import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

import csv

def load_careers_from_csv(file_path):
    career_data = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            role = row.get('Job Title', '')
            desc = row.get('Job Description', '')
            skills = row.get('Skills', '')
            #path = row.get('Recommended Learning Path', '')
            certs = row.get('Certifications', '')
            
            content = f"{role}: {desc} Required skills: {skills}. Certifications: {certs}."
            career_data.append(
                Document(
                    page_content=content,
                    metadata={"Job Title": role}
                )
            )
    return career_data

def main():
    csv_path = os.path.join(os.path.dirname(__file__), 'Top_207_IT_Job_Roles_Skills_Dataset.csv')
    career_data = load_careers_from_csv(csv_path)

    print("Loading HuggingFace embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("Creating FAISS index...")
    db = FAISS.from_documents(career_data, embeddings)
    
    db_path = os.path.join(os.path.dirname(__file__), "faiss_index")
    db.save_local(db_path)
    print(f"Index saved to {db_path} successfully!")

if __name__ == "__main__":
    main()
