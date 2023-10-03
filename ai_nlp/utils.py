from django import core
import io
import pdf2image
import openai
import os
from langchain.schema import retriever
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from ai_tms.settings import EMBEDDING_MODEL ,OPENAI_API_KEY
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import Docx2txtLoader

# from tensorflow.python.platform import gfile
# import tensorflow as tf


openai.api_key = OPENAI_API_KEY

def text_splitter_create_vector(data,persistent_dir) -> Chroma:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    text_splitter = CharacterTextSplitter(separator="\n",chunk_size=2000,chunk_overlap=200,length_function = len)
    texts = text_splitter.split_documents(data)
    vector_db = Chroma.from_documents(documents=texts,embedding=embeddings,persist_directory=persistent_dir)
    return vector_db

def loader(instance) -> None:
    path_split=instance.file.path.split(".")
    persistent_dir=path_split[0]+"/"
    print(instance.file.name)
    if instance.file.name.endswith(".docx"):
        loader = Docx2txtLoader(instance.file.path)
    else:
        loader = UnstructuredPDFLoader(instance.file.path)
    # else:
    #     raise ValueError("text file not supported")
    data = loader.load()
    vector_db=text_splitter_create_vector(data=data,persistent_dir=persistent_dir)
    vector_db.persist()
    instance.vector_embedding_path = persistent_dir
    instance.save() 

def thumbnail_create(path) -> core :
    img_io = io.BytesIO()
    images = pdf2image.convert_from_path(path,fmt='png',grayscale=False,size=(300,300))[0]
    images.save(img_io, format='PNG')
    img_byte_arr = img_io.getvalue()
    return core.files.File(core.files.base.ContentFile(img_byte_arr),"thumbnail.png")


def load_embedding_vector(vector_path,query)->RetrievalQA:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_db = Chroma(persist_directory=vector_path ,embedding_function=embeddings)
    # doc = vector_db.similarity_search(query=query)
    # vector_db=Chroma.from_documents(documents=doc,embedding=embeddings )
    chain = RetrievalQA.from_chain_type(llm=OpenAI(),retriever =vector_db.as_retriever(search_type="similarity", search_kwargs={"k":1}),chain_type="stuff")
    return chain.run(query).strip()