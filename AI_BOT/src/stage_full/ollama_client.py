from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
def full_model():

    llm = Ollama(
        model="my-model", 
        request_timeout=120.0,
        additional_kwargs={
            "temperature": 0.1,
            "repeat_penalty": 1.15,
            "num_ctx": 2048,      
            "num_predict": 512,
            "num_threads": 6
        }
    )

    Settings.llm = llm
    return llm

