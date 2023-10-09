from django import core
import openai ,os,pdf2image,io
from langchain.llms import OpenAI
from ai_tms.settings import EMBEDDING_MODEL ,OPENAI_API_KEY
from langchain.document_loaders import (UnstructuredPDFLoader ,PDFMinerLoader ,Docx2txtLoader ,
                                        WebBaseLoader ,BSHTMLLoader ,TextLoader,UnstructuredEPubLoader)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA 
from celery.decorators import task
from ai_nlp.models import PdffileUpload 
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback


openai.api_key = OPENAI_API_KEY
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


from celery.decorators import task

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
            # elif instance.file.name.endswith(".epub"):
            #     loader = UnstructuredEPubLoader(instance.file.path)
            else:
                print("pdf_processing")
                loader = PDFMinerLoader(instance.file.path)
            data = loader.load()
            text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=100,chunk_overlap=0)  
            texts = text_splitter.split_documents(data)
            embeddings = HuggingFaceEmbeddings(model_name=emb_model,cache_folder= "embedding")
            save_prest( texts, embeddings, persistent_dir)
            instance.vector_embedding_path = persistent_dir
            instance.status = "SUCCESS"
            # instance.question_threshold=20
            instance.save() 
        except:
            instance.status ="ERROR"
            instance.save()

def save_prest(texts,embeddings,persistent_dir):
    vector_db = Chroma.from_documents(documents=texts,embedding=embeddings,persist_directory=persistent_dir)
    vector_db.persist()
    print("--------",vector_db)
    vector_db = None

def thumbnail_create(path) -> core :
    img_io = io.BytesIO()
    images = pdf2image.convert_from_path(path,fmt='png',grayscale=False,size=(300,300))[0]
    images.save(img_io, format='PNG')
    img_byte_arr = img_io.getvalue()
    return core.files.File(core.files.base.ContentFile(img_byte_arr),"thumbnail.png")

def load_embedding_vector(vector_path,query)->RetrievalQA:
    llm =OpenAI()
    embeddings = HuggingFaceEmbeddings(model_name=emb_model,cache_folder= "embedding")
    # embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_db = Chroma(persist_directory=vector_path ,embedding_function=embeddings)
    # retriever = vector_db.as_retriever()
    v = vector_db.similarity_search(query=query,k=2)
    with get_openai_callback() as cb:
        chain = load_qa_chain(llm, chain_type="stuff")
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