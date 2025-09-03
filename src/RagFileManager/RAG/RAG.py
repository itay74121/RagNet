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
BLOCK_SIZE = 1000

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
        # ChromDB collection to track processed files and their hashes
        self._processed_collection = self.client.get_or_create_collection(name="processed_files")

    def get_doc_id(self,doc:str) -> str:
         return hashlib.sha256(doc.encode("utf-8")).hexdigest()
    @safety
    def add_unique(self, doc: str) -> bool:
        """Add doc only if not already in collection."""
        doc_id = self.get_doc_id(doc)
        existing = self.collection.get(ids=[doc_id])

        if existing["ids"]:  # already exists
            print("Already in DB:", doc_id)
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
                count += 1
                print(f"done {100*(count/len(docs))}")
        except Exception as e:
            print(e)
            return False
        else:
            return True
    def _hash_file(self, file_path: str) -> str:
        h = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    h.update(chunk)
        except Exception:
            return ""
        return h.hexdigest()

    def _embed_from_hash(self, hash_str: str, dim: int = 128):
        # Deterministic embedding derived from hash to satisfy ChromDB embeddings requirement
        b = hash_str.encode('utf-8')
        vec = []
        i = 0
        while len(vec) < dim:
            vec.append((b[i % len(b)] & 0xFF) / 255.0)
            i += 1
        return vec

    def _record_processed_file(self, file_path: str, file_hash: str) -> None:
        doc_id = hashlib.sha256(file_path.encode('utf-8')).hexdigest()
        embedding = self._embed_from_hash(file_hash)
        try:
            self._processed_collection.delete(ids=[doc_id])
        except Exception:
            pass
        self._processed_collection.add(
            documents=[file_path],
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[{"path": file_path, "hash": file_hash}]
        )

    def has_file_changed(self, file_path: str) -> bool:
        """Return True if the file is new or its content hash has changed since last processed."""
        if not os.path.isabs(file_path):
            file_path = os.path.realpath(file_path)
        doc_id = hashlib.sha256(file_path.encode('utf-8')).hexdigest()
        current_hash = self._hash_file(file_path)
        try:
            existing = self._processed_collection.get(ids=[doc_id])
        except Exception:
            existing = {"ids": []}
        if not existing.get("ids"):
            # Not processed before
            self._record_processed_file(file_path, current_hash)
            return True
        metadatas = existing.get("metadatas") or []
        existing_hash = None
        if metadatas:
            existing_hash = metadatas[0].get("hash")
        if existing_hash != current_hash:
            self._record_processed_file(file_path, current_hash)
            return True
        return False
    @safety
    def extract_formats_to_text(self):
        for file in glob.glob(os.path.join(self.file_path, "*")):
            if not os.path.isfile(os.path.abspath(file)):
                continue
            if file.endswith('.txt'):
                continue
            # Only process files that changed since last processing
            try:
                changed = self.has_file_changed(file)
            except Exception:
                changed = True
            if not changed:
                continue
            # multiplexer: extract to text when changed
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
            for file in glob.glob(os.path.join(self.file_path, "*.txt")):
                print(file)
                with open(file,'r',encoding='utf-8') as f:
                    if f.readable():
                        text = f.read()
                        text = text.replace("\n"," ")
                        text = self.drop_words(text)[1]
                blocks = [text[i:i + BLOCK_SIZE] for i in range(0,len(text),BLOCK_SIZE)]
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



