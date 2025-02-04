import os
from langchain_voyageai import VoyageAIEmbeddings
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain_core.documents import Document
from dotenv import load_dotenv
import datetime
load_dotenv()


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


class SimpleGuidedRag:
    QDRANT_CLOUD_URL = os.environ["QDRANT_CLOUD_URL"]
    QDRANT_CLOUD_API_KEY = os.environ["QDRANT_CLOUD_API_KEY"]
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    VOYAGE_LEGALAID_API_KEY = os.getenv("VOYAGE_LEGALAID_API_KEY")

    def __init__(self):
        self.embeddings = VoyageAIEmbeddings(model="voyage-law-2",
                                             api_key=SimpleGuidedRag.VOYAGE_LEGALAID_API_KEY)

        self.client = QdrantClient(url=SimpleGuidedRag.QDRANT_CLOUD_URL,
                                   api_key=SimpleGuidedRag.QDRANT_CLOUD_API_KEY)

        self.vector_store = QdrantVectorStore(client=self.client,
                                              embedding=self.embeddings,
                                              collection_name="legal_docs_voyage")

        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=SimpleGuidedRag.OPENAI_API_KEY)

        self.system_prompt = ("You are a legal assistant of a lawyer." 
                              "Use only the following pieces of retrieved context to answer the question." 
                              "Be as detailed as possible. And cite sources if possible." 
                              "If you don't know the answer, just say that you don't know. ")

        self.prompt = ChatPromptTemplate([("human",
                                           self.system_prompt + "\nquestion:{question}\n context:{context}\n")])

    def retrieve(self):
        def retrieve(state: State):
            retrieved_docs = self.vector_store.similarity_search(state["question"], k=50)
            print(f"retrieved {len(retrieved_docs)} documents")
            print("****")
            return {"context": retrieved_docs}
        return retrieve

    def generate(self):
        def get_source(doc: Document) -> str:
            src = doc.metadata["source"]
            src_arr = src.split("/")
            filename = src_arr[-1].split('.')[0:-1]
            doc_name = ".".join([e for e in filename])
            month = src_arr[-2]
            year = src_arr[-3]
            source_str = f"{doc_name} {month} {year}"
            return source_str

        def generate(state: State):
            # state now is dict of {"question": "...", "context": [doc]}
            docs_content = "\n\n".join(f"{doc.page_content} Source:{get_source(doc)}" for doc in state["context"])
            # docs_content is now a long string of the various contents of the context list.

            messages = self.prompt.invoke({"question": state["question"], "context": docs_content})
            # messages is now a ChatPromptValue.
            print(f"invoking llm at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            response0 = self.llm.invoke(messages)
            print(f"finished invocation at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return {"answer": response0.content}
        return generate

    def chat(self, prompt_text: str) -> str:
        graph_builder = StateGraph(State).add_sequence([self.retrieve(), self.generate()])
        graph_builder.add_edge(START, "retrieve")
        graph = graph_builder.compile()

        # prompt_text = """What are the things to be considered in invoking and proving psychological incapacity?"""
        print(f"Question: {prompt_text}\n\n\n")
        response = graph.invoke({"question": prompt_text})
        # invoke is the entry point of the graph passing a dict.
        return response["answer"]
