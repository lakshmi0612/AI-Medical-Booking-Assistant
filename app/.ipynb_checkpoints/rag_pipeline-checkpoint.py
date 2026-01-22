from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from app.config import Config
import streamlit as st
from typing import List
import tempfile
import os

class RAGPipeline:
    """RAG system for PDF question answering"""
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = None
        self.qa_chain = None
        
    def process_pdfs(self, pdf_files: List) -> bool:
        """Process uploaded PDFs and create vector store"""
        try:
            all_texts = []
            
            # Extract text from all PDFs
            for pdf_file in pdf_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(pdf_file.read())
                    tmp_path = tmp.name
                
                try:
                    reader = PdfReader(tmp_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    all_texts.append(text)
                finally:
                    os.unlink(tmp_path)
            
            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=Config.CHUNK_SIZE,
                chunk_overlap=Config.CHUNK_OVERLAP,
                length_function=len
            )
            
            chunks = []
            for text in all_texts:
                chunks.extend(text_splitter.split_text(text))
            
            if not chunks:
                st.error("No text extracted from PDFs")
                return False
            
            # Create vector store
            self.vector_store = FAISS.from_texts(
                chunks,
                self.embeddings
            )
            
            # Create QA chain
            llm = ChatGroq(
                api_key=Config.GROQ_API_KEY,
                model_name=Config.GROQ_MODEL,
                temperature=0.3
            )
            
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
                return_source_documents=False
            )
            
            return True
            
        except Exception as e:
            st.error(f"Error processing PDFs: {str(e)}")
            return False
    
    def query(self, question: str, chat_history: List = None) -> str:
        """Query the RAG system"""
        try:
            if not self.qa_chain:
                return "Please upload PDFs first to enable document search."
            
            # Build context from chat history if provided
            context = ""
            if chat_history:
                recent_msgs = chat_history[-6:]  # Last 3 exchanges
                context = "Recent conversation:\n"
                for msg in recent_msgs:
                    role = msg["role"].title()
                    context += f"{role}: {msg['content']}\n"
                context += "\n"
            
            # Create enhanced query
            enhanced_query = f"{context}Question: {question}"
            
            result = self.qa_chain.invoke({"query": enhanced_query})
            return result.get("result", "I couldn't find an answer in the documents.")
            
        except Exception as e:
            st.error(f"Error querying documents: {str(e)}")
            return "An error occurred while searching the documents."
    
    def is_ready(self) -> bool:
        """Check if RAG system is ready"""
        return self.vector_store is not None and self.qa_chain is not None