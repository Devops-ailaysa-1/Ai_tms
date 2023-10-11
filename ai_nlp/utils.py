from django import core
import openai ,os,pdf2image,io
from langchain.llms import OpenAI
from ai_tms.settings import EMBEDDING_MODEL ,OPENAI_API_KEY
from langchain.document_loaders import (UnstructuredPDFLoader ,PDFMinerLoader ,Docx2txtLoader ,
                                        WebBaseLoader ,BSHTMLLoader ,TextLoader,UnstructuredEPubLoader)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter ,RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA 
from celery.decorators import task
from ai_nlp.models import PdffileUpload 
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback
from bs4 import BeautifulSoup
from bs4.element import Comment
from celery.decorators import task
openai.api_key = OPENAI_API_KEY
print(openai.api_key)
# llm = ChatOpenAI(model_name='gpt-4')
emb_model = "sentence-transformers/all-MiniLM-L6-v2"

# chat_params = {
#         "model": "gpt-3.5-turbo-16k", # Bigger context window
#         "openai_api_key": OPENAI_API_KEY ,
#         "temperature": 0.5, # To avoid pure copy-pasting from docs lookup
#         "max_tokens": 8192
#     }
# llm = ChatOpenAI(**chat_params)

# def text_splitter_create_vector(data,persistent_dir) -> Chroma:
#     embeddings = HuggingFaceEmbeddings(model_name=emb_model,cache_folder= "embedding")
#     # embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
#     text_splitter = CharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
#     texts = text_splitter.split_documents(data)
#     vector_db = Chroma.from_documents(documents=texts,embedding=embeddings,persist_directory=persistent_dir)
#     print(type(embeddings))
#     return vector_db
from zipfile import ZipFile 

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(string=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def epub_processing(file_path):
    file_name= file_path.split("/")[-1].split(".")[0]
    text_str = ""
    with ZipFile(file_path) as zf:
        for i in zf.filelist:
            print(i.filename)
            if i.filename.endswith("xhtml") or i.filename.endswith("html"):
                html_content = zf.read(i)
                # print(html_content)
                text = text_from_html(html_content.decode("utf-8"))
                # with open(i.filename , 'rb') as fp:  
                text_str = text_str+text+"\n"
    # print("---->",text_str)
    return core.files.File(core.files.base.ContentFile(text_str),file_name+".txt")

 
@task(queue='default')
def loader(file_id) -> None:
    instance = PdffileUpload.objects.get(id=file_id)
    website = instance.website
    if website:
        loader = BSHTMLLoader(instance.website)
    else:
        # try:
        path_split=instance.file.path.split(".")
        persistent_dir=path_split[0]+"/"
        os.makedirs(persistent_dir,mode=0o777)
        print(persistent_dir)
        if instance.file.name.endswith(".docx"):
            loader = Docx2txtLoader(instance.file.path)
        elif instance.file.name.endswith(".txt"):
            loader = TextLoader(instance.file.path)
        elif instance.file.name.endswith(".epub"):
            text = epub_processing(instance.file.path)
            instance.text_file = text
            instance.save()
            loader = TextLoader(instance.text_file.path)
        else:
            print("pdf_processing")
            loader = PDFMinerLoader(instance.file.path)
        data = loader.load()
        print("embedding model loaded")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0, separators=[" ", ",", "\n"])
        # text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=100)   #. from_tiktoken_encoder  ,chunk_overlap=0
        texts = text_splitter.split_documents(data)
        embeddings = HuggingFaceEmbeddings(model_name=emb_model,cache_folder= "embedding")
        # embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        save_prest( texts, embeddings, persistent_dir)
        instance.vector_embedding_path = persistent_dir
        instance.status = "SUCCESS"
        # instance.question_threshold=20
        instance.save() 
        # except:
        #     instance.status ="ERROR"
        #     instance.save()

def save_prest(texts,embeddings,persistent_dir):
    vector_db = Chroma.from_documents(documents=texts,embedding=embeddings,persist_directory=persistent_dir)
    vector_db.persist()
    print("--------",vector_db)
    vector_db = None

# def thumbnail_create(path) -> core :
#     img_io = io.BytesIO()
#     images = pdf2image.convert_from_path(path,fmt='png',grayscale=False,size=(300,300))[0]
#     images.save(img_io, format='PNG')
#     img_byte_arr = img_io.getvalue()
#     return core.files.File(core.files.base.ContentFile(img_byte_arr),"thumbnail.png")
from langchain.chat_models import ChatOpenAI

def load_embedding_vector(vector_path,query)->RetrievalQA:
    # llm =OpenAI()
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0,max_tokens=300)
    embed = HuggingFaceEmbeddings(model_name=emb_model,cache_folder= "embedding")
    # embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_db = Chroma(persist_directory=vector_path ,embedding_function=embed)
    # retriever = vector_db.as_retriever()
    v = vector_db.similarity_search(query=query,k=2)
    print("docum-------------------------------------------->>>>>>>>>",v)
    with get_openai_callback() as cb:
        chain = load_qa_chain(llm, chain_type="map_reduce") #map_reduce stuff
        res = chain({"input_documents": v, "question": query})
        print(cb)
        
    # vector_db=Chroma.from_documents(documents=doc,embedding=embeddings )
    # chain = RetrievalQA.from_chain_type(llm=llm,retriever =vector_db.as_retriever(search_type="similarity", search_kwargs={"k":4}),chain_type="stuff")
  
    # qa_chain = RetrievalQA.from_chain_type(llm=OpenAI(),
    #                               chain_type="stuff",
    #                               retriever=retriever,
    #                               return_source_documents=True)
    print("-------------------")
    # print(qa_chain(query) ) #chain.run(query).strip()
    return res["output_text"] 