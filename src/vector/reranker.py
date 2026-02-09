from langchain_community.retrievers.contextual_compression import (
    ContextualCompressionRetriever
)

from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder


def build_reranker(base_retriever):
    reranker = CrossEncoderReranker(
        model=HuggingFaceCrossEncoder(
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
        ),
        top_n=5
    )

    return ContextualCompressionRetriever(
        base_retriever=base_retriever,
        base_compressor=reranker
    )
