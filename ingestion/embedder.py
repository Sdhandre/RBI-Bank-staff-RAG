import os
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from dotenv import load_dotenv
load_dotenv()

def get_embedding_model():
    return NVIDIAEmbeddings(
        model="nvidia/llama-nemotron-embed-1b-v2",
        api_key=os.environ["NVIDIA_API_KEY"],
        truncate="END"
    )
