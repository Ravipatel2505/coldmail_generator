import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import WebBaseLoader
import chromadb
import uuid
import os

# Setup
llm = ChatGroq(temperature=0, groq_api_key="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", model_name="llama3-70b-8192")

df = pd.read_csv("my_portfolio.csv")

# Setup ChromaDB
client = chromadb.PersistentClient("vectorstore")
collection = client.get_or_create_collection(name="portfolio")

if not collection.count():
    for _, row in df.iterrows():
        collection.add(documents=row["Techstack"],
                       metadatas={"links": row["Links"]},
                       ids=[str(uuid.uuid4())])

def process_job_url(url):
    # Load job page
    loader = WebBaseLoader(url)
    page_data = loader.load().pop().page_content

    # Job Extraction
    prompt_extract = PromptTemplate.from_template("""
    Extract structured information from the following job description:
    
    {page_data}
    
    Return the information in this csv format:
    {{
        "Job_Title": "...",
        "description" : "...", 
        "Company_Name": "...",
        "Location": "...",
        "Required_Skills": ["...", "..."],
        "Preferred_Qualifications": ["...", "..."],
        "Job_Type": "...",
        "Experience_Level": "...",
        "Salary": "...",
        "Company_Description": "..."
    }}
    """)
    
    chain_extract = prompt_extract | llm
    res = chain_extract.invoke(input={"page_data": page_data})
    
    json_parser = JsonOutputParser()
    job = json_parser.parse(res.content)

    # Query ChromaDB
    links = collection.query(query_texts=job["Required_Skills"], n_results=2).get('metadatas', [])
    
    # Cold Email Generation
    prompt_email = PromptTemplate.from_template("""
    ### JOB DESCRIPTION:
    {job_description}
    
 ### INSTRUCTION:
        You are Ravi, a business development executive at TCS. TCS is an AI & Software Consulting company dedicated to facilitating
        the seamless integration of business processes through automated tools. 
        Over our experience, we have empowered numerous enterprises with tailored solutions, fostering scalability, 
        process optimization, cost reduction, and heightened overall efficiency. 
        Your job is to write a cold email to the client regarding the job mentioned above describing the capability of TCS 
        in fulfilling their needs.
         Also add the most relevant ones from the following links to showcase TCS portfolio: {link_list}
        Remember you are Ravi.
        Do not provide a preamble.
        ### EMAIL (NO PREAMBLE):
        
        """
    )
    
    chain_email = prompt_email | llm
    email_response = chain_email.invoke({"job_description": str(job), "link_list": links})
    
    return email_response.content
