from typing import List, Dict
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

class WebSearchService:
    def __init__(self):
        self.search_api_key = os.getenv('SERPER_API_KEY')
        self.search_url = "https://google.serper.dev/search"
        self.headers = {
            'X-API-KEY': self.search_api_key,
            'Content-Type': 'application/json'
        }

    async def search_job_info(
        self,
        job_title: str,
        context: str = None
    ) -> List[Dict[str, str]]:
        """Search for job information on the web"""
        search_query = f"{job_title} job description responsibilities requirements"
        if context:
            search_query += f" {context}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.search_url,
                headers=self.headers,
                json={'q': search_query}
            ) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                results = []

                # Process organic results
                if 'organic' in data:
                    for result in data['organic'][:5]:  # Limit to top 5 results
                        title = result.get('title', '')
                        link = result.get('link', '')
                        snippet = result.get('snippet', '')

                        # Extract relevant information from the snippet
                        content = self._extract_relevant_info(snippet, job_title)
                        
                        if content:
                            results.append({
                                'title': title,
                                'url': link,
                                'content': content,
                                'relevance': self._calculate_relevance(content, job_title)
                            })

                # Sort results by relevance
                results.sort(key=lambda x: x['relevance'], reverse=True)
                return results

    def _extract_relevant_info(self, text: str, job_title: str) -> str:
        """Extract relevant information from text"""
        # Remove common irrelevant phrases
        text = text.replace('...', ' ').replace('...', ' ')
        
        # Split into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Filter sentences that are likely to contain job information
        relevant_sentences = []
        for sentence in sentences:
            # Check if sentence contains job-related keywords
            if any(keyword in sentence.lower() for keyword in [
                'responsibility', 'duty', 'task', 'role', 'requirement',
                'skill', 'experience', 'qualification', 'job', 'position'
            ]):
                relevant_sentences.append(sentence)
        
        return '. '.join(relevant_sentences) if relevant_sentences else text

    def _calculate_relevance(self, content: str, job_title: str) -> float:
        """Calculate relevance score for content"""
        # Convert to lowercase for case-insensitive matching
        content_lower = content.lower()
        job_title_lower = job_title.lower()
        
        # Calculate basic relevance score
        score = 0.0
        
        # Check for exact job title match
        if job_title_lower in content_lower:
            score += 0.4
        
        # Check for job title words
        job_words = set(job_title_lower.split())
        content_words = set(content_lower.split())
        word_overlap = len(job_words.intersection(content_words)) / len(job_words)
        score += word_overlap * 0.3
        
        # Check for job-related keywords
        keywords = ['responsibility', 'duty', 'task', 'role', 'requirement',
                   'skill', 'experience', 'qualification', 'job', 'position']
        keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
        score += min(keyword_count * 0.1, 0.3)  # Cap at 0.3
        
        return min(score, 1.0)  # Cap at 1.0 