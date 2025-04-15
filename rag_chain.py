
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama

import olefile
import pandas as pd
import tempfile
from langchain.embeddings import HuggingFaceEmbeddings

from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PyPDFLoader,TextLoader
from langchain.vectorstores import FAISS
def extrct_text_from_hwp(file_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".hwp") as f:
        f.write(file_bytes)
        hwp_path = f.name

    if not olefile.isOleFile(hwp_path):
        return "❌ 이 파일은 HWP 포맷이 아닙니다."

    ole = olefile.OleFileIO(hwp_path)
    if ole.exists("PrvText"):
        content = ole.openstream("PrvText").read()
        try:
            return content.decode("utf-16")
        except:
            return "❌ UTF-16 디코딩 실패"
    return "❌ 읽을 수 있는 텍스트가 없습니다."  
def excel_sheets_to_documents(file):
    xls = pd.ExcelFile(file)
    docs = []

    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        for _, row in df.iterrows():
            content = f"[시트: {sheet}]\n" + "\n".join([f"{col}: {row[col]}" for col in df.columns])
            docs.append(Document(page_content=content))
    
    return docs
class rag:
    def __init__(self):
        #self.model=ChatOllama(model='exaone3.5:7.8b')
        self.model=ChatOpenAI(model='gpt-4o')
#         self.embedding = HuggingFaceEmbeddings(
#     model_name="BAAI/bge-small-en"  # 또는 "sentence-transformers/all-MiniLM-L6-v2"
# )
        self.embedding=OpenAIEmbeddings()
        self.chat_history=[]
        self.vectorstore=None
    def rag_chain(self,file_name,type):
        if type=='pdf':
            loader=PyPDFLoader(file_name)
            docs=loader.load()
        elif type=='hwp':
            loader = TextLoader(file_name, encoding="utf-8")
            docs=loader.load()
        elif type == 'xlsx':
            docs = excel_sheets_to_documents(file_name)
        
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=100)
        split_document=text_splitter.split_documents(docs)
        self.vectorstore=FAISS.from_documents(
        documents=split_document,
        embedding=self.embedding
    ) 

        retriever=self.vectorstore.as_retriever()
        prompt=PromptTemplate.from_template(self.get_template())
        
        self.chain=(
        {"context":retriever,"question":RunnablePassthrough()}
        | prompt
        |self.model
        |StrOutputParser()
        )
        return self
    def ask(self,question):
        

        result=self.chain.invoke(question)
        return result
        
    def get_template(self):
        prompt="""you are helpful assistant for question-answering .
        use the following pieces of retrieved context to answer the question and source like page.
        if you don't know the answer ,just say you don't know.
        PLEASE Answer in KOREAN
        #Context:
        {context}

        #Question:
        {question}

        #Answer:       
        
        """
        return prompt

     
