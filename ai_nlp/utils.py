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
import random,re
from langchain.chat_models import ChatOpenAI
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA 
from celery.decorators import task
from ai_nlp.models import PdffileUpload ,PdfQustion
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
            save_prest( texts, embeddings, persistent_dir,instance)
            instance.vector_embedding_path = persistent_dir
            instance.status = "SUCCESS"
            instance.save()
        except:
            instance.status ="ERROR"  #####need to add if error 
            instance.save()

def save_prest(texts,embeddings,persistent_dir,instance):
    vector_db = Chroma.from_documents(documents=texts,embedding=embeddings,persist_directory=persistent_dir)
    # print("presisting.....")
    result = generate_question(vector_db)
    result = result.split("\n")
    for sentence in result:
        cleaned_sentence = remove_number_from_sentence(sentence)
        cleaned_sentence = cleaned_sentence.strip()
        PdfQustion.objects.create(pdf_file_chat=instance , question=cleaned_sentence)
        # print("-------------->>",i)
    # print("presisted.....")
    vector_db.persist()
    vector_db = None
 


def querying_llm(llm , chain_type , chain_type_kwargs,similarity_document ,query):
    # print("chain")
    chain = load_qa_chain(llm, chain_type="stuff" ,prompt=chain_type_kwargs) #,chain_type_kwargs=chain_type_kwargs

    res = chain({"input_documents":similarity_document, "question": query})

    # qa = RetrievalQA.from_chain_type(llm=llm, 
    #                              chain_type="stuff", 
    #                              retriever=similarity_document , 
    #                              chain_type_kwargs=chain_type_kwargs, 
    #                              return_source_documents=True)

    # res = qa({"query":query})['result']

    return  res['output_text'] #res["output_text"] 

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
        llm = Cohere(model="command-nightly", temperature=0) #command-nightly
        # llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        embed = CohereEmbeddings(model = "multilingual-22-12") #multilingual-22-12 embed-multilingual-v3.0

    vector_db = Chroma(persist_directory=vector_path,embedding_function=embed)
    v = vector_db.similarity_search(query=query,k=2 )
    result = querying_llm(llm = llm , chain_type="stuff" ,chain_type_kwargs=prompt_template_chatbook(),similarity_document=v,query=query)
    return result




def generate_question(document):
    from ai_openai.utils import get_prompt_chatgpt_turbo
    collections = document._collection
    print("collected_doc")
    document_list = collections.get()["documents"]
    doc_len = len(document_list)
    n = 2 if doc_len>2 else 1
    print(n)
    document = random.sample(document_list,n)
    document = " ".join(document)
    query = "Generate four questions from the above content and split all four questions with new line"
    prompt = prompt_gen_question_chatbook(document,query)
    prompt_res = get_prompt_chatgpt_turbo(prompt = prompt,n=1)
    # print(prompt_res)
    generated_text =prompt_res['choices'][0]['message']['content']
    # print(prompt_res['choices'])
    # for i in generated_text:
    #     text = i["content"]
    #     text = text.split('\n')
    #     for j in text:

    # print(generated_text)
    # result = querying_llm(llm = llm , chain_type="stuff" ,chain_type_kwargs=prompt_gen_question_chatbook(),similarity_document=doc,query=query)
    # chain = load_qa_chain(llm, chain_type="stuff",chain_type_kwargs=prompt_gen_question_chatbook())
    # res = chain({"input_documents":doc, "question": query})
    # print(query)
    # print("########################")
    # print("generated_question----->>",res)
    return generated_text




def prompt_template_chatbook(if_kwargs=False):
    prompt_template = """Text: {context}

    Question: {question}

    Answer the Question based on the text provided. If the text doesn't contain the answer, reply that the answer is not available."""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    # if if_kwargs==False:
    return PROMPT
    # else:
    # return  {"prompt": PROMPT}


def prompt_gen_question_chatbook(context,question):
    prompt_template = """Text: {}

    Question: {}

    """.format(context,question)

    return prompt_template



def remove_number_from_sentence(sentence):
    pattern = r'^\d+.'
    cleaned_sentence = re.sub(pattern, '', sentence)
    return cleaned_sentence

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
