from django import core
import openai ,os,pdf2image,io
from langchain.llms import OpenAI
from ai_tms.settings import EMBEDDING_MODEL ,OPENAI_API_KEY 
from langchain.document_loaders import (UnstructuredPDFLoader ,PDFMinerLoader ,Docx2txtLoader ,
                                        WebBaseLoader ,BSHTMLLoader ,TextLoader,UnstructuredEPubLoader)
from langchain_community.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter ,RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings.cohere import CohereEmbeddings
import random,re,uuid 
from langchain.chat_models import ChatOpenAI

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA 
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
import spacy
import yake
import requests
from string import punctuation
from langdetect import detect
from docx import Document
from ai_openai.utils import get_prompt_chatgpt_turbo
from ai_openai.utils import mistral_chat_api
nlp = spacy.load('en_core_web_sm')
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank
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
    path_split=instance.file.path.split(".")
    try:
        persistent_dir=path_split[0]+"/"
        os.makedirs(persistent_dir,mode=0o777)
    except:
        num = str(uuid.uuid4())
        persistent_dir=path_split[0]+"_"+str(num)+"/"
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
        loader = PDFMinerLoader(instance.file.path,extract_images=False)
        # loader = PDFMinerLoader(instance.file.path)  #PyPDFLoader
    data = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0, separators=[" ", ",", "\n"])
    texts = text_splitter.split_documents(data)
    embeddings = OpenAIEmbeddings()  #model="text-embedding-3-large"
    try:
        save_prest(texts, embeddings, persistent_dir,instance)
        instance.vector_embedding_path = persistent_dir
        instance.status = "SUCCESS" 
    except:
        instance.status = "ERROR"
    instance.save()
 

 


def save_prest(texts,embeddings,persistent_dir,instance):
    vector_db = Chroma.from_documents(documents=texts,embedding=embeddings,persist_directory=persistent_dir)
    result = generate_question(vector_db)
    result = result.split("\n")
    for sentence in result:
        cleaned_sentence = remove_number_from_sentence(sentence)
        cleaned_sentence = cleaned_sentence.strip()
        PdfQustion.objects.create(pdf_file_chat=instance , question=cleaned_sentence)
    vector_db.persist()
    vector_db = None


def querying_llm(llm , chain_type , chain_type_kwargs,similarity_document ,query):
    chain = load_qa_chain(llm, chain_type=chain_type ,prompt=chain_type_kwargs) #,chain_type_kwargs=chain_type_kwargs
    res = chain({"input_documents":similarity_document, "question": query})
    return  res['output_text'] #res["output_text"] 


def load_chat_history(instance):
    # if not instance.pdf_file_chat.all():
    memory = ConversationBufferMemory(memory_key='chat_history', output_key="answer",input_key='question',return_messages=True)
    # else:
        # memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    for i in instance.pdf_file_chat.all():
        if i.question and i.answer:
            memory.save_context({"question": i.question}, {"answer": i.answer})
    print("memory-->",memory)
    return memory


def load_embedding_vector(instance,query)->RetrievalQA:
    vector_path = instance.vector_embedding_path
    llm = ChatOpenAI(model_name="gpt-3.5-turbo-1106", temperature=0)  
    embed = OpenAIEmbeddings() #model="text-embedding-3-large"        
    vector_db = Chroma(persist_directory=vector_path,embedding_function=embed)
    retriever = vector_db.as_retriever(search_kwargs={"k": 9})
    compressor = CohereRerank(user_agent="langchain")
    compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)    
    compressed_docs = compression_retriever.get_relevant_documents(query=query)
    memory = load_chat_history(instance)
    qa = ConversationalRetrievalChain.from_llm(llm=llm,memory=memory,
                                               retriever=compression_retriever, return_source_documents=True)
    
    page_numbers = []
    for i in compressed_docs:
        if 'page' in i.metadata:
            page_numbers.append(i.metadata['page']+1)
    page_numbers = list(set(page_numbers))
    # result = qa.run(query=query)
    result = qa(query) 
    print(result)
    return result['answer'] ,page_numbers


def prompt_temp_context_question(context,question):
    prompt_template = """Text: {context}

        Question: {question}

        Answer the Question based on the text provided . If the text doesn't contain the answer, reply that the answer is not available. """.format(context=context,question=question) #If the context doesn't contain the answer, reply that the answer is not available.
    return prompt_template


def gen_text_context_question(vectors_list,question):
    context = ""
    for i in vectors_list:
        context +=i.page_content
    prompt_template = prompt_temp_context_question(context,question)
    # print(prompt_template)
    prompt_res = get_prompt_chatgpt_turbo(prompt = prompt_template,n=1) ##chatgpt
    generated_text =prompt_res['choices'][0]['message']['content']  ##chatgpt
    # generated_text = cohere_endpoint(prompt_template)
    return generated_text


def generate_question(document):
    collections = document._collection
    document_list = collections.get()["documents"]
    doc_len = len(document_list)
    n = 2 if doc_len>2 else 1
    document = random.sample(document_list,n)
    document = " ".join(document)
    query = "Generate four questions from the above content and split all four questions with new line and questions should be translate in English language"
    prompt = prompt_gen_question_chatbook(document,query)
    prompt_res = get_prompt_chatgpt_turbo(prompt = prompt,n=1)
    generated_text =prompt_res['choices'][0]['message']['content']
    return generated_text


def prompt_template_chatbook(prompt_string=False):
    prompt_template = """Text: {context}

    Question: {question}

    Answer the Question based on the text provided . If the text doesn't contain the answer, reply that the answer is not available."""

    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    if prompt_string==False:
        return PROMPT
    else:
        return  {"prompt": prompt_template}


def prompt_gen_question_chatbook(context,question):
    prompt_template = """Text: {}

    Question: {}

    """.format(context,question)

    return prompt_template


def remove_number_from_sentence(sentence):
    pattern = r'^\d+.'
    cleaned_sentence = re.sub(pattern, '', sentence)
    return cleaned_sentence

 
def keyword_extract(text):
    language = "en"
    max_ngram_size = 3
    deduplication_thresold = 0.5
    deduplication_algo = 'seqm'
    windowSize = 1
    numOfKeywords = 20
    custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size,
                                                dedupLim=deduplication_thresold, 
                                                dedupFunc=deduplication_algo, windowsSize=windowSize, top=numOfKeywords, features=None)
    keywords = custom_kw_extractor.extract_keywords(text)
    return [kw[0] for kw in keywords]


entity = {'CARDINAL':'cardinal',
 'DATE':'data',
 'EVENT':'event',
 'FAC':'Buildings, airports, highways, bridges',
 'GPE':'Countries, cities, states.',
 'LANGUAGE':'language',
 'LAW':'law',
 'LOC':'location',
 'MONEY':'money',
 'NORP':'Nationalities or religious or political groups',
 'ORDINAL':'first,second etc',
 'ORG':'Organization',
 'PERCENT':'Percent',
 'PERSON':'Person',
 'PRODUCT':'Product',
 'QUANTITY':'Quantity',
 'TIME':'Time',
 'WORK_OF_ART':'Word_of_Art'}


 

def extract_entities(sentence):
    doc = nlp(sentence)
    # ner_dict = {ent.text: get_entity_description(ent.label_) for ent in doc.ents}
    ner_dict = {}
    for ent in doc.ents: 
        if ent.label_ in entity.keys():
            
            if entity[ent.label_] in  ner_dict.keys():
                
                ner_dict[entity[ent.label_]].append(ent.text)
            else:
    
                ner_dict[entity[ent.label_]] = [ent.text]
    return ner_dict


def lang_det_word_choice(text):
    if len(text) > 500:
        text = text[:450]
    lang_code = detect(text)
    return lang_code


def check_file_language(list_of_file_path):
    file_paths = []
    extracted_text_list = []
    for file_path in list_of_file_path:
        if file_path.endswith('.txt'):
            with open(file_path,'r',encoding='utf-8') as fp:
                text = fp.read()
                lang_code = lang_det_word_choice(text)
                if lang_code == "en":
                    file_paths.append(file_path)
                    extracted_text_list.append(text)

        if file_path.endswith('.docx'):
            document = Document(file_path)
            extracted_text = ""
            for p in document.paragraphs:
                extracted_text = extracted_text+" "+p.text
            
            lang_code = lang_det_word_choice(extracted_text)
            if lang_code == "en":
                file_paths.append(file_path)
                extracted_text_list.append(extracted_text)
    print("extracted_text_list",extracted_text_list)
    return file_paths ,extracted_text_list


def prompt_to_extract_ner_terms(terms):
    
    prompt = """context_list : {} 
    
    
    Extract only list of named entity and terminology from the above list of context result should be in comma separated""".format(",".join(terms))
    result = get_prompt_chatgpt_turbo(prompt=prompt,n=1) # Note: Remove stop words ,pronoun,verbs,adverb
    generated_text =result['choices'][0]['message']['content']
    if generated_text:
        generated_text = generated_text.split(",")
        print("generated_text",generated_text)
        return generated_text
    else:
        return None

# def ner_terminology_finder(file_paths):
#     file_paths = check_file_language(file_paths)
#     if not file_paths:
#         raise  'please upload English language files' 
#     url = "https://transbuilderstaging.ailaysa.com/dataset/ner-upload/"

#     payload = {}
#     headers = {}
#     files = []
#     for file_path in file_paths:
#         file_name = os.path.basename(file_path)
#         files.append(('file',(file_name,open(file_path,'rb'),'text/plain')))
    
#     response = requests.request("POST", url, headers=headers, data=payload, files=files)

#  #   project_instance --> list of job --> get_lang_code --> translation --> {"s_term":"", "t_term":"","lang_code":,"job":""}
    

#     if response.status_code in [200,201]:
#         terminology = []
#         pos = []
#         tem_list = []
#         duplicate_list = []
 
#         for i in response.json():
#             terminology.extend(i['ner'].split(","))
#             terminology.extend(i['terminology'].split(","))
#             pos.extend(i['pos_user'])

#         terminology = list(set([i.translate(str.maketrans("","", punctuation+"”“•")).strip().capitalize() for i in terminology if len(i)>1]))
#         terminology = prompt_to_extract_ner_terms(terminology)
        
#         for i in terminology:
#             if i.lower() not in duplicate_list:
#                 duplicate_list.append(i.lower())
#                 tem_list.append({'term':i,'pos':'Noun'})
#         duplicate_list = []
#         for i in pos:
#             if i['term'].lower() not in duplicate_list:
#                 duplicate_list.append(i['term'].lower())
#                 tem_list.append(i) #{'term':i,'pos':'Noun'}

#         return {'terminology':tem_list} 
#     else:
#         return None



 
prompt = """Context: {} 


Extract key phrases and Named Entity Recognition (NER) from the given context give only Person, Nationalities or Religious or Political Groups (NORP), Facilities, Organizations, Geopolitical Entities (GPE), Locations, Products, Works of Art, and Laws for NER and 
give only the word and don't include NER names in results and the output should be in the format of {"key": key pharas list , "ner": list of ners } and eliminate the repeated words 
"""

import json

def ner_terminology_finder(file_paths):
    file_paths ,extracted_text_list = check_file_language(file_paths)
    if not file_paths:
        raise  'please upload English language files' 
    terms = []
    for extracted_text in extracted_text_list:
        prompt = prompt.format(extracted_text)
        result = mistral_chat_api(prompt)
        try:
            result ="" #json.loads(chat_response.choices[0].message.content)
        except Exception as e:
            print("ERROR in JSON DECODE-------->",e)
    print("terms",terms)
    if terms:
         return {'terminology':terms} 
    else:
        return None



        
    
