from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import json
import os
from .web_search import WebSearchService

@dataclass
class RAGResult:
    enhanced_description: str
    web_references: List[Dict[str, str]]
    confidence_score: float
    knowledge_sources: List[str]
    article_references: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.article_references is None:
            self.article_references = []

class RAGService:
    def __init__(self, articles=None):
        # Initialize the sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize FAISS index
        self.index = None
        self.documents = articles or []
        self.web_search = WebSearchService()
        
        # Load knowledge base if no articles provided
        if not self.documents:
            self._load_knowledge_base()
        else:
            # Create embeddings and index for provided articles
            self._index_documents()

    def _load_knowledge_base(self):
        """Load and index the knowledge base"""
        knowledge_dir = "knowledge_base"
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir)
            return

        # Load all JSON files from knowledge base
        for filename in os.listdir(knowledge_dir):
            if filename.endswith('.json'):
                with open(os.path.join(knowledge_dir, filename), 'r') as f:
                    data = json.load(f)
                    self.documents.extend(data)

        if not self.documents:
            return

        # Create embeddings for all documents
        texts = [doc.get('content', '') for doc in self.documents]
        embeddings = self.model.encode(texts)
        
        # Initialize FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))

    def _index_documents(self):
        """Create embeddings and index for documents"""
        if not self.documents:
            return
            
        # Create embeddings for all documents
        texts = [doc.get('content', '') for doc in self.documents]
        if not texts:
            return
            
        embeddings = self.model.encode(texts)
        
        # Initialize FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))

    async def retrieve_relevant_info(
        self,
        query: str,
        context: Optional[str] = None
    ) -> RAGResult:
        """Retrieve relevant information using RAG"""
        # If no knowledge base, fall back to web search
        if not self.index or not self.documents:
            web_results = await self.web_search.search_job_info(query, context)
            return self._create_result_from_web(web_results)

        # Get query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Search in knowledge base
        k = min(3, len(self.documents))  # Get top 3 results
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1).astype('float32'), k
        )

        # Get relevant documents
        relevant_docs = [self.documents[i] for i in indices[0]]
        
        # Calculate confidence score
        confidence = 1 - (distances[0][0] / 2)  # Normalize distance to confidence
        confidence = max(0, min(1, confidence))

        # If confidence is low, enhance with web search
        if confidence < 0.6:
            web_results = await self.web_search.search_job_info(query, context)
            return self._combine_knowledge(relevant_docs, web_results, confidence)
        
        return self._create_result_from_docs(relevant_docs, confidence)

    async def combine_knowledge(
        self,
        rag_results: RAGResult,
        web_results: List[Dict[str, str]]
    ) -> RAGResult:
        """Combine RAG results with web search results"""
        if not web_results:
            return rag_results

        # Combine descriptions
        combined_desc = f"{rag_results.enhanced_description}\n\nAdditional Information:\n"
        for result in web_results[:2]:  # Add top 2 web results
            combined_desc += f"- {result['content']}\n"

        # Combine references
        combined_refs = rag_results.web_references + web_results[:3]

        # Recalculate confidence
        new_confidence = max(rag_results.confidence_score, 0.7)  # Boost confidence

        return RAGResult(
            enhanced_description=combined_desc,
            web_references=combined_refs,
            confidence_score=new_confidence,
            knowledge_sources=rag_results.knowledge_sources + ["web_search"]
        )

    def _create_result_from_docs(
        self,
        docs: List[Dict],
        confidence: float
    ) -> RAGResult:
        """Create RAGResult from knowledge base documents"""
        combined_desc = "\n".join(doc.get('content', '') for doc in docs)
        sources = [doc.get('source', 'knowledge_base') for doc in docs]

        return RAGResult(
            enhanced_description=combined_desc,
            web_references=[],
            confidence_score=confidence,
            knowledge_sources=sources
        )

    def _create_result_from_web(
        self,
        web_results: List[Dict[str, str]]
    ) -> RAGResult:
        """Create RAGResult from web search results"""
        if not web_results:
            return RAGResult(
                enhanced_description="No relevant information found.",
                web_references=[],
                confidence_score=0.0,
                knowledge_sources=["web_search"]
            )

        combined_desc = "\n".join(result['content'] for result in web_results[:3])
        return RAGResult(
            enhanced_description=combined_desc,
            web_references=web_results[:3],
            confidence_score=0.7,  # Default confidence for web results
            knowledge_sources=["web_search"]
        )

    def _combine_knowledge(
        self,
        docs: List[Dict],
        web_results: List[Dict[str, str]],
        confidence: float
    ) -> RAGResult:
        """Combine knowledge base and web results"""
        # Create base result from knowledge base
        base_result = self._create_result_from_docs(docs, confidence)
        
        # Add web results
        combined_desc = f"{base_result.enhanced_description}\n\nAdditional Information:\n"
        for result in web_results[:2]:
            combined_desc += f"- {result['content']}\n"

        return RAGResult(
            enhanced_description=combined_desc,
            web_references=web_results[:3],
            confidence_score=max(confidence, 0.7),
            knowledge_sources=base_result.knowledge_sources + ["web_search"]
        ) 