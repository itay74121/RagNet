from threading import Event, Thread
import time
import os
import chromadb 
import glob
import hashlib
from dotenv import load_dotenv
from openai import OpenAI, embeddings


load_dotenv()

# chromadb.Client()
BLOCK_SIZE = 500

class RAGFileManager:
    stop_event = Event()  # <- not double-underscore
    BLOCK_SIZE = BLOCK_SIZE
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
                if count>1000: break
                count += 1
        except Exception as e:
            print(e)
            return False
        else:
            return True
    def run(self) -> Thread:
        t = Thread(target=self._run, daemon=True)
        t.start()
        return t

    def _run(self):
        while not RAGFileManager.stop_event.is_set():
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



