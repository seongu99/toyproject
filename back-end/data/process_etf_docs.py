import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import pandas as pd

def process_etf_documents():
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Process PDF documents
    docs = []
    pdf_dir = "data/docs"
    
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(pdf_dir, filename)
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            texts = text_splitter.split_documents(pages)
            docs.extend(texts)
    
    # Create vector store
    vectorstore = FAISS.from_documents(docs, embeddings)
    
    # Save vector store
    vectorstore.save_local("data/vector_db")
    print("Vector database created and saved to data/vector_db")

def process_etf_info():
    # Read ETF info CSV
    etf_info = pd.read_csv("data/docs/etf_info.csv")
    
    # Save as parquet for better performance
    etf_info.to_parquet("data/etf_info.parquet")
    print("ETF info processed and saved to data/etf_info.parquet")

if __name__ == "__main__":
    process_etf_documents()
    process_etf_info() 