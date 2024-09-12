# Cargar librerías necesarias
import os
import pandas as pd
import json

from llama_index.core.settings import Settings
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Response
from llama_index.core.evaluation import (
    BatchEvalRunner,
    FaithfulnessEvaluator,
    RelevancyEvaluator,
    CorrectnessEvaluator,
    DatasetGenerator,
    QueryResponseDataset,
    SemanticSimilarityEvaluator,
    RetrieverEvaluator,
    generate_question_context_pairs,
    EmbeddingQAFinetuneDataset,
)
from llama_index.core.constants import DEFAULT_TEMPERATURE
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

from app.engine.index import get_index


# Cargar variables de entorno
load_dotenv(dotenv_path='.env')

# Configuración del modelo y embeddings
llm_deployment = os.getenv("AZURE_DEPLOYMENT_NAME")
embedding_deployment = os.getenv("EMBEDDING_MODEL")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
max_tokens = os.getenv("LLM_MAX_TOKENS")

################################################################################
# Configuración de modelos
################################################################################

# Azure AD token provider
credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default").token
llm_config = {
    "engine": llm_deployment,
    "azure_endpoint": azure_openai_endpoint,
    "api_key": token,  # Usamos el token en lugar de api_key
    "temperature": float(os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)),
    "max_tokens": int(max_tokens) if max_tokens is not None else None,
}
Settings.llm = AzureOpenAI(**llm_config)

dimensions = os.getenv("EMBEDDING_DIM")
embedding_config = {
    "azure_endpoint": azure_openai_endpoint,
    "azure_deployment": embedding_deployment,
    "api_key": token,  # De nuevo, usamos el token en lugar de api_key
    "dimensions": int(dimensions) if dimensions is not None else None,
}
Settings.embed_model = AzureOpenAIEmbedding(**embedding_config)

################################################################################
# Carga de índice
################################################################################
# Definir llm y embeddings ya configurados (se usan en Settings)
# vector_index ya está definido y configurado en Settings
vector_index = get_index()
doc_store = vector_index.docstore
documents = [doc_store.get_document(doc_id) for doc_id in doc_store.docs.keys()]

# NOTA AL MARGEN: ¿Cómo obtener información de los nodos?
ref_doc_info = vector_index.ref_doc_info
# Now you have a dictionary where the keys are node_ids and the values are RefDocInfo objects
# You can create a node_dict for the RecursiveRetriever constructor like this:
node_dict = {node_id: ref_doc_info.node_ids for node_id, ref_doc_info in ref_doc_info.items()}


################################################################################
# Generar dataset de preguntas y respuestas
################################################################################


# Si el fichero no existe, guardarlo
if not os.path.exists("tmp/dataset.json"):
    print("GENERATING NEW DATASET...")
    dataset_generator = DatasetGenerator.from_documents(
        documents = documents[0:1], # Use only the first document
        num_questions_per_chunk = 1,
    )
    qas = dataset_generator.generate_dataset_from_nodes(num=2)
    qas.save_json("tmp/dataset.json")
    print("Dataset saved to tmp/dataset.json")
else:
    qas = QueryResponseDataset.from_json("tmp/dataset.json")
    print("Dataset loaded from tmp/dataset.json")



print('\n'*2, 'Q&A FROM DatasetGenerator:', '\n'*2)
for q, a in zip(qas.questions, qas.responses.values()):
    print(f"Question: {q}\nAnswer: {a}\n\n")


################################################################################
# Evaluación de preguntas y respuestas
################################################################################
faithfulness_evaluator = FaithfulnessEvaluator()
relevancy_evaluator = RelevancyEvaluator()
correctness_evaluator = CorrectnessEvaluator()
similarity_evaluator = SemanticSimilarityEvaluator()
runner = BatchEvalRunner(
    {"correctness": correctness_evaluator, 
     "relevancy": relevancy_evaluator, 
     "faithfulness": faithfulness_evaluator},
    workers=8,
)

eval_results = runner.evaluate_queries(
    vector_index.as_query_engine(),
    queries=qas.queries,
    reference=[qr[1] for qr in qas.qr_pairs],
)



def get_eval_results(qa_dataset, eval_results):

    print("Evaluating results...")

    qr_pairs = qa_dataset.qr_pairs # Question and response pairs
    evaluations_data = []
    contexts_data = []

    for metric_name, evaluations in eval_results.items():
        for evaluation in evaluations:
            evaluations_data.append({
                'metric': metric_name,
                'score': evaluation.score,
                'query': evaluation.query,
                'feedback': evaluation.feedback,
            })

            contexts_str = json.dumps(evaluation.contexts) if isinstance(evaluation.contexts, list) else evaluation.contexts
            contexts_data.append({
                'query': evaluation.query,
                'question': qa_dataset.queries[evaluation.query],
                'answer': qa_dataset.responses[evaluation.query],
                'response': evaluation.response,
                'contexts': contexts_str,
            })

    df_evaluations = pd.DataFrame(evaluations_data)
    df_contexts = pd.DataFrame(contexts_data)

    df_contexts = df_contexts.dropna(subset=['contexts']).drop_duplicates() # Responses y Contexts siempre son los mismos
    df_pivot = df_evaluations.pivot(index='query', columns='metric', values=['score', 'feedback'])
    df_pivot.columns = [f'{metric}_{col}' for col, metric in df_pivot.columns]
    df_final = pd.merge(df_contexts, df_pivot.reset_index(), on='query', how='left')
    df_final = df_final[[x for x in df_final.columns if x!='contexts'] + ['contexts']]

    return df_final

df_final = get_eval_results(qas, eval_results)

print("Saving results to tmp/eval_results.csv")
df_final.to_csv("tmp/eval_results.csv", index=False)






################################################################################
# Evaluación del retriever
################################################################################
# Crear evaluador de recuperadores
retriever = vector_index.as_retriever(similarity_top_k=2)
retriever_evaluator = RetrieverEvaluator.from_metric_names(
    ["hit_rate", "mrr", "precision", "recall", "ap", "ndcg"], retriever=retriever
)

# try it out on a sample query
sample_id, sample_query = list(qas.queries.items())[0]
sample_expected = qas.relevant_docs[sample_id]

eval_result = retriever_evaluator.evaluate(sample_query, sample_expected)
print(eval_result)

    
   

