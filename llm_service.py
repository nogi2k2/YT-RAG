from qdrant_client import QdrantClient
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.document_loaders.text import TextLoader
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_community.llms import Ollama

import os
import youtube_service as ys

llm = Ollama(model = "gemma:2b")
qdrant_url = "http://localhost:6333"
client = QdrantClient(url = qdrant_url, prefer_grpc = False)
embeddings = SentenceTransformerEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")
prompt_template = """
Given the context provided, I will consider the relevant information to formulate a detailed and 
well-explained answer to the user's question. If the answer is not within my knowledge base, 
I will clearly state that I don't know.

Context: {context}
Question: {question}

I will now process the information and provide a helpful and comprehensive answer:


"""
template = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])

def create_kb(channel_name, video_id):
    global qdrant_url, embeddings
    data_path = ys.get_data_path()
    video_text_file = os.path.join(data_path, channel_name, video_id)
    video_text_file = video_text_file + ".txt"
    loader = TextLoader(video_text_file, encoding = "utf-8")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 100)
    chunks = text_splitter.split_documents(documents)
    Qdrant.from_documents(
        chunks,
        embeddings,
        url = qdrant_url,
        prefer_grpc = False,
        collection_name = channel_name
    )

def get_response(query, COLLECTION_NAME):
    db = Qdrant(client = client, embeddings = embeddings, collection_name = COLLECTION_NAME)
    retriever = db.as_retriever(search_kwargs = {'k':5}, search_type = 'mmr')
    chain_type_kwargs = {"prompt": template}
    qa = RetrievalQA.from_chain_type(
        llm = llm,
        chain_type = "stuff",
        retriever = retriever,
        return_source_documents = True,
        chain_type_kwargs = chain_type_kwargs,
        verbose = True
    )

    response = qa(query)
    answer = response["result"]

    video_ids = []
    source_documents = []
    for source_doc in response["source_documents"]:
        source_text = source_doc.page_content
        source_file = source_doc.metadata["source"]
        video_id = ys.fetch_videoid(source_file, COLLECTION_NAME)

        video_ids.append(video_id)
        source_documents.append(source_text)

    return answer, source_documents, video_ids