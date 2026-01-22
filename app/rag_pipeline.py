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
        try:
            # Use CPU explicitly and trust_remote_code for compatibility
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            st.error(f"Error loading embeddings model: {str(e)}")
            # Fallback: will be handled when PDFs are processed
            self.embeddings = None
        
        self.vector_store = None
        self.qa_chain = None
        self.raw_texts = []  # Store raw PDF text for direct extraction
        
    def process_pdfs(self, pdf_files: List) -> bool:
        """Process uploaded PDFs and create vector store"""
        try:
            st.write("### 🔧 RAG PROCESSING DEBUG")
            st.write("---")
            
            # Initialize embeddings if not already done
            if self.embeddings is None:
                st.write("**Initializing embeddings model...**")
                try:
                    self.embeddings = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                    st.success("✅ Embeddings model loaded")
                except Exception as e:
                    st.error(f"Failed to load embedding model: {str(e)}")
                    st.info("Try restarting the app or check your internet connection.")
                    return False
            
            all_texts = []
            self.raw_texts = []  # Clear previous texts
            
            st.write(f"**Processing {len(pdf_files)} PDF file(s)...**")
            
            # Extract text from all PDFs
            for pdf_file in pdf_files:
                st.write(f"📄 Processing: {pdf_file.name}")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(pdf_file.read())
                    tmp_path = tmp.name
                
                try:
                    reader = PdfReader(tmp_path)
                    text = ""
                    for page_num, page in enumerate(reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                            st.write(f"  - Page {page_num + 1}: {len(page_text)} chars")
                    
                    if text.strip():
                        all_texts.append(text)
                        self.raw_texts.append(text)  # Store raw text
                        
                        st.success(f"✅ Extracted {len(text)} total characters from {pdf_file.name}")
                        st.code(text[:200], language="text")  # Show first 200 chars
                    else:
                        st.warning(f"⚠️ No text extracted from {pdf_file.name}")
                        
                finally:
                    os.unlink(tmp_path)
            
            if not all_texts:
                st.error("❌ No text extracted from any PDFs")
                return False
            
            st.write("---")
            st.write(f"**📊 Extraction Summary:**")
            st.write(f"- Total texts extracted: {len(all_texts)}")
            st.write(f"- Raw texts stored: {len(self.raw_texts)}")
            st.write(f"- Total characters: {sum(len(t) for t in all_texts)}")
            
            # Split into chunks
            st.write("\n**Creating text chunks...**")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=Config.CHUNK_SIZE,
                chunk_overlap=Config.CHUNK_OVERLAP,
                length_function=len
            )
            
            chunks = []
            for text in all_texts:
                text_chunks = text_splitter.split_text(text)
                chunks.extend(text_chunks)
                st.write(f"  - Created {len(text_chunks)} chunks")
            
            if not chunks:
                st.error("❌ No text chunks created from PDFs")
                return False
            
            st.success(f"✅ Created {len(chunks)} total chunks")
            
            # Create vector store
            st.write("\n**Creating vector store...**")
            self.vector_store = FAISS.from_texts(
                chunks,
                self.embeddings
            )
            st.success("✅ Vector store created")
            
            # Create QA chain
            st.write("\n**Creating QA chain...**")
            llm = ChatGroq(
                api_key=Config.GROQ_API_KEY,
                model_name=Config.GROQ_MODEL,
                temperature=0.1  # Lower temperature for extraction
            )
            
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=False
            )
            st.success("✅ QA chain created")
            
            st.write("---")
            st.success("✅ **RAG PIPELINE READY**")
            return True
            
        except Exception as e:
            st.error(f"❌ Error processing PDFs: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return False
    
    def get_raw_text(self) -> str:
        """Get all raw text from processed PDFs"""
        st.write("### 📄 get_raw_text() CALLED")
        
        if not self.raw_texts:
            st.warning("⚠️ No raw texts stored in self.raw_texts")
            st.write(f"  - raw_texts list length: {len(self.raw_texts)}")
            return ""
        
        combined = "\n\n".join(self.raw_texts)
        
        st.write(f"**get_raw_text() Stats:**")
        st.write(f"  - Number of PDFs stored: {len(self.raw_texts)}")
        st.write(f"  - Combined text length: {len(combined)} chars")
        st.write(f"  - Preview (first 200 chars):")
        st.code(combined[:200])
        
        return combined
    
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
        is_ready = (self.vector_store is not None and 
                   self.qa_chain is not None and 
                   len(self.raw_texts) > 0)
        
        st.write("### 🔍 is_ready() CHECK")
        st.write(f"  - vector_store exists: {self.vector_store is not None}")
        st.write(f"  - qa_chain exists: {self.qa_chain is not None}")
        st.write(f"  - raw_texts count: {len(self.raw_texts)}")
        st.write(f"  - **Result: {is_ready}**")
        
        return is_ready