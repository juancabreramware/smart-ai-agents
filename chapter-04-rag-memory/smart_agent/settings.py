from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()
@dataclass(frozen=True)
class Settings:
    provider:str=os.getenv('CH4_PROVIDER','mock')
    embeddings:str=os.getenv('CH4_EMBEDDINGS','local')
    model:str=os.getenv('OPENAI_MODEL','gpt-5.6')
    embedding_model:str=os.getenv('OPENAI_EMBEDDING_MODEL','text-embedding-3-small')
    input_per_m:float=float(os.getenv('OPENAI_INPUT_USD_PER_MILLION','4.00'))
    cached_input_per_m:float=float(os.getenv('OPENAI_CACHED_INPUT_USD_PER_MILLION','0.40'))
    output_per_m:float=float(os.getenv('OPENAI_OUTPUT_USD_PER_MILLION','20.00'))
    embedding_per_m:float=float(os.getenv('OPENAI_EMBEDDING_USD_PER_MILLION','0.02'))
    memory_threshold:float=float(os.getenv('CH4_MEMORY_SIMILARITY_THRESHOLD','0.78'))
    naive_threshold:float=float(os.getenv('CH4_NAIVE_CACHE_THRESHOLD','0.72'))
    api_key:str=os.getenv('OPENAI_API_KEY','')
