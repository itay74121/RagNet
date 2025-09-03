from chromadb import PersistentClient
from openai import OpenAI
import os


class RagQuery:
    def __init__(self, db_path: str = "./data/mydb", collection_name: str = "docs"):
        self.client = PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def query(self, query_text: str, top_k: int = 5) -> dict:
        # Build embedding for the query and fetch top_k similar documents
        embedding = self.openai.embeddings.create(model="text-embedding-3-small", input=query_text).data[0].embedding
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include_embeddings=True,
            include_documents=True,
            include_metadatas=True
        )
        return {
            "documents": results.get("documents"),
            "metadatas": results.get("metadatas"),
        }




async def query_chroma():
    pass


