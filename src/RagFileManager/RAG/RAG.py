from ntpath import isfile
from threading import Event, Thread
import time
import os
import chromadb 
import glob
import hashlib
from dotenv import load_dotenv
from openai import OpenAI, embeddings
import pymupdf4llm as mupdf
from util import safety
from docx2md import do_convert
from english_words import get_english_words_set
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import requests

load_dotenv()

# chromadb.Client()
BLOCK_SIZE = 500

class RAGFileManager:
    eng = get_english_words_set(['web2'], lower=True).union(set(requests.get("https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt").text.split()))  # dictionary-like set
    stops = set(ENGLISH_STOP_WORDS)
    stop_event = Event()  # <- not double-underscore
    def __init__(self,db_path,file_path,collection_name,poll=1):
        self.db_path = db_path
        self.file_path = os.path.realpath(file_path)
        self.collection_name = collection_name
        self.poll = poll
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        self.OpenAI_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def get_doc_id(self,doc:str) -> str:
         return hashlib.sha256(doc.encode("utf-8")).hexdigest()

    def add_unique(self, doc: str) -> bool:
        """Add doc only if not already in collection."""
        doc_id = self.get_doc_id(doc)
        existing = self.collection.get(ids=[doc_id])

        if existing["ids"]:  # already exists
            # print("Already in DB:", doc_id)
            return False
        else:
            embeddings = self.OpenAI_client.embeddings.create(model="text-embedding-3-small",input=doc).data[0].embedding
            self.collection.add(
                documents=[doc], 
                ids=[doc_id],
                embeddings=[embeddings]
            )
            print("Inserted:", doc_id)
            return True
    def add_many_unique(self,docs):
        try:
            count = 0
            for doc in docs:
                self.add_unique(doc)
                if count>1000: break
                count += 1
        except Exception as e:
            print(e)
            return False
        else:
            return True
    @safety
    def extract_formats_to_text(self):
        for file in glob.glob(os.path.join(self.file_path, "*")):
            if not os.path.isfile(os.path.abspath(file)):
                continue
            if not file.endswith('.txt'):
                # multiplexer 
                res = False
                if file.endswith('.pdf'):
                    res = self.handle_pdf_text_extract(file)
                elif file.endswith('.docx'):
                    res = self.handle_docx_text_extract(file)
                else:
                    print("file format not supported")
                if not res:
                    print(f"cant extract from {file}")
        return 
    
    @safety
    def handle_pdf_text_extract(self,file):
        text = mupdf.to_markdown(file)
        self.out_to_text_file(file,text)
    
    @safety
    def handle_docx_text_extract(self,file):
        text = do_convert(file)
        self.out_to_text_file(file,text)

    @safety
    def out_to_text_file(self,file:str,text:str):
        filename = file[:-1*file[::-1].index('.')-1]+".txt"
        with open(filename,'w',encoding='utf-8') as f: 
            if f.writable():
                status,new_text = self.drop_words(text)
                print(len(text),len(new_text))
                f.write(new_text)
            f.close()
    
    @safety
    def drop_words(self,text:str):
        return " ".join([ i for i in text.split(" ") if i in RAGFileManager.eng and (i not in RAGFileManager.stops)])    

    def run(self) -> Thread:
        t = Thread(target=self._run, daemon=True)
        t.start()
        return t

    def _run(self):
        while not RAGFileManager.stop_event.is_set():
            self.extract_formats_to_text()
            sum_text = ""
            for file in glob.glob(os.path.join(self.file_path, "*.txt")):
                print(file)
                with open(file,'r',encoding='utf-8') as f:
                    if f.readable():
                        text = f.read()
                        text = text.replace("\n"," ")
                        if text:
                            sum_text += text 
            
            blocks = [sum_text[i:i + BLOCK_SIZE] for i in range(0,len(sum_text),BLOCK_SIZE)]
            blocks = list(filter(lambda x: x,blocks))
            self.add_many_unique(blocks)
            # interruptible sleep:
            if RAGFileManager.stop_event.wait(self.poll * 60):
                break
        print("done")

def main():
    try:
        rfm = RAGFileManager("./data/mydb","./data/","docs",poll=0.5)
        t = rfm.run()
        # RAGFileManager.stop_event.set()
        input("")
        # print(rfm.collection.get(limit=3, include=["embeddings", "documents", "metadatas"]))
    except KeyboardInterrupt as e:
        print(e)
        RAGFileManager.stop_event.set()

if __name__ == "__main__":
    main()



