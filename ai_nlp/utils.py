from django import core
import openai ,os,pdf2image,io
from langchain.llms import OpenAI
from ai_tms.settings import EMBEDDING_MODEL ,OPENAI_API_KEY 
from langchain.document_loaders import (UnstructuredPDFLoader ,PDFMinerLoader ,Docx2txtLoader ,
                                        WebBaseLoader ,BSHTMLLoader ,TextLoader,UnstructuredEPubLoader)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter ,RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings.cohere import CohereEmbeddings

from langchain.chat_models import ChatOpenAI
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA 
from celery.decorators import task
from ai_nlp.models import PdffileUpload 
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback
from bs4 import BeautifulSoup
from bs4.element import Comment
from celery.decorators import task
from langchain.llms import Cohere
from langchain.prompts import PromptTemplate
from zipfile import ZipFile 

openai.api_key = OPENAI_API_KEY
import os
# llm = ChatOpenAI(model_name='gpt-4')
emb_model = "sentence-transformers/all-MiniLM-L6-v2"
 


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

def epub_processing(file_path,text_word_count_check=False):
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
    if text_word_count_check:
        return text_str
    else:
        return core.files.File(core.files.base.ContentFile(text_str),file_name+".txt")


 
@task(queue='default')
def loader(file_id) -> None:
    instance = PdffileUpload.objects.get(id=file_id)
    website = instance.website
    if website:
        loader = BSHTMLLoader(instance.website)
    else:
        try:
            path_split=instance.file.path.split(".")
            persistent_dir=path_split[0]+"/"
            os.makedirs(persistent_dir,mode=0o777)
            print(persistent_dir)
            if instance.file.name.endswith(".docx"):
                loader = Docx2txtLoader(instance.file.path)
            elif instance.file.name.endswith(".txt"):

                loader = TextLoader(instance.file.path)
            elif instance.file.name.endswith(".epub"):
                text = epub_processing(instance.file.path,text_word_count_check=False)
                instance.text_file = text
                instance.save()
                loader = TextLoader(instance.text_file.path)
            else:
                loader = PDFMinerLoader(instance.file.path)
            data = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0, separators=[" ", ",", "\n"])
            texts = text_splitter.split_documents(data)

            # embeddings = OpenAIEmbeddings()
            embeddings = CohereEmbeddings(model="multilingual-22-12")
            save_prest( texts, embeddings, persistent_dir)
            instance.vector_embedding_path = persistent_dir
            instance.status = "SUCCESS"
            instance.save() 
        except:
            instance.status ="ERROR"  #####need to add if error 
            instance.save()

def save_prest(texts,embeddings,persistent_dir):
    vector_db = Chroma.from_documents(documents=texts,embedding=embeddings,persist_directory=persistent_dir)
    vector_db.persist()
    vector_db = None


def prompt_template():
    prompt_template = """Text: {context}

    Question: {question}

    Answer the question based on the text provided. If the text doesn't contain the answer, reply that the answer is not available."""


    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    chain_type_kwargs = {"prompt": PROMPT}

    return chain_type_kwargs


def load_embedding_vector(instance,query)->RetrievalQA:
    vector_path = instance.vector_embedding_path
    if instance.embedding_name.model_name:
        model_name = instance.embedding_name.model_name
    else:
        model_name = "openai"
    if model_name == "openai":
        print(model_name ,"openai")
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0) #,max_tokens=300
        embed = OpenAIEmbeddings()
    else: # elif model_name == "cohere":
        print(model_name,"cohere")
        
        llm = Cohere(model="command-nightly", temperature=0)
        embed = CohereEmbeddings(model = "multilingual-22-12") #multilingual-22-12 embed-multilingual-v3.0
    vector_db = Chroma(persist_directory=vector_path,embedding_function=embed)
    v = vector_db.similarity_search(query=query,k=2)
    # print(v)
    chain_type_kwargs = prompt_template()
 
    # qa = RetrievalQA.from_chain_type(llm=Cohere(model="command-nightly", temperature=0), chain_type="stuff", retriever=vector_db.as_retriever(), 
                                        #  chain_type_kwargs=chain_type_kwargs, return_source_documents=True)
    # with get_openai_callback() as cb:
    chain = load_qa_chain(llm, chain_type="stuff") #map_reduce stuff refine
    res = chain({"input_documents": v, "question": query})
    # answer = qa({"query": query})
    return res["output_text"]
    #answer['result']
    # res["output_text"] 





# def thumbnail_create(path) -> core :
#     img_io = io.BytesIO()
#     images = pdf2image.convert_from_path(path,fmt='png',grayscale=False,size=(300,300))[0]
#     images.save(img_io, format='PNG')
#     img_byte_arr = img_io.getvalue()
#     return core.files.File(core.files.base.ContentFile(img_byte_arr),"thumbnail.png")



    # vector_db=Chroma.from_documents(documents=doc,embedding=embeddings )
    # chain = RetrievalQA.from_chain_type(llm=llm,retriever =vector_db.as_retriever(search_type="similarity", search_kwargs={"k":4}),chain_type="stuff")
  
    # qa_chain = RetrievalQA.from_chain_type(llm=OpenAI(),
    #                               chain_type="stuff",
    #                               retriever=retriever,
    #                               return_source_documents=True)
    # print("-------------------")
    # print(qa_chain(query) ) #chain.run(query).strip()
