import streamlit as st
import rag_chain


import tempfile

from tavily import TavilyClient
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]  # 또는 os.getenv("TAVILY_API_KEY")
client = TavilyClient(api_key=TAVILY_API_KEY)
def show_history():
    for q,a in st.session_state.chat_history:
            with st.expander(f'{q}'):
                st.markdown(f'{st.session_state.uploaded_file}')
                st.markdown(f"**Q:** {q}")
                st.markdown(f"**A:** {a}")
        
st.title('Q&A PDF')

if 'chat_history' not in st.session_state:
    st.session_state.chat_history=[]
if 'chain' not in st.session_state:
    st.session_state.chain = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file=None
if 'web_search' not in st.session_state:
    st.session_state.web_search=None
def clear():
    st.session_state.chat_history = []
    st.session_state.uploaded_file=None
    st.session_state.chain = None

def clear_input():
    query = st.session_state["search_query"]
    if query:
        results = client.search(query=query, max_results=3)
        st.session_state["search_results"] = results
        st.session_state["search_query"] = ""
with st.sidebar:
    uploaded_file=st.file_uploader('uploading the file',type=['pdf','hwp','xlsx'])
    
    if uploaded_file and st.button('📥 Upload and Process'):
        
        if uploaded_file.name.lower().endswith('.pdf'):
            type='pdf'
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
               
        elif uploaded_file.name.lower().endswith('.hwp'):
            type='hwp'
            hwp_text = rag_chain.extrct_text_from_hwp(uploaded_file.read())
            with tempfile.NamedTemporaryFile(delete=False,suffix='.txt', mode="w", encoding="utf-8") as tmp_file:
                tmp_file.write(hwp_text)
        elif uploaded_file.name.lower().endswith('.xlsx'):
            type='xlsx'
            
            with tempfile.NamedTemporaryFile(delete=False,suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.read())
        

                
                
        else:
            st.error("지원하지 않는 파일 형식입니다.")
            tmp_path = None
        st.session_state.uploaded_file = uploaded_file.name
        st.success('pdf processed')
        tmp_path = tmp_file.name 
        chain_obj=rag_chain.rag().rag_chain(tmp_path,type)
        st.session_state.chain = chain_obj 
  
    search_query = st.text_input("🔍 검색", key="search_query")
    
    search=st.button('search',on_click=clear_input)
    
        
if "search_results" in st.session_state:
    with st.expander("검색 결과"):
        for r in st.session_state["search_results"]["results"]:
            st.markdown(f"**[{r['title']}]({r['url']})**  \n{r['content'][:150]}...")   
                
if st.session_state.chain:
    question=st.chat_input('type the question?')
    st.header(f'{st.session_state.uploaded_file}')
    
    if question:
        # 🔥 이전 대화 context 정리
        chat_context = "\n".join([f"Q: {q}\nA: {a}" for q, a in st.session_state.chat_history])
        full_question = f"{chat_context}\nQ: {question}" if chat_context else question
        with st.spinner("🧠 답변 생성 중..."):
            result = st.session_state.chain.ask(full_question)
            st.session_state.chat_history.append((question,result))
            
show_history()     

if st.button("🧹 clear file"):
    clear()
     
   
    


   
