from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import json
import aiohttp
import asyncio

load_dotenv()

class AIWorkforceAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = "gpt-4"
        self.temperature = 0.7
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
    async def analyze_team(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the impact of AI on a team and generate recommendations
        """
        # Format team information
        team_info = self._format_team_info(request["members"])
        
        # Create prompt
        prompt = self._create_prompt(
            team_info=team_info,
            industry=request["industry"],
            company_size=request["company_size"]
        )
        
        # Get analysis from OpenAI API
        analysis = await self._get_ai_analysis(prompt)
        
        # Process and structure the response
        result = self._process_response(analysis)
        result["team_name"] = request["team_name"]
        
        return result
    
    def _create_prompt(self, team_info: str, industry: str, company_size: str) -> str:
        """Create prompt for AI analysis"""
        return f"""
        Analyze the impact of generative AI on the following team and provide detailed recommendations:
        
        Team Information:
        {team_info}
        
        Industry: {industry}
        Company Size: {company_size}
        
        Please provide a comprehensive analysis including:
        1. Impact Summary: How AI will affect each role and the team as a whole
        2. Recommendations: Specific actions for AI integration and workforce adaptation
        3. Risk Assessment: Potential challenges and mitigation strategies
        4. Upskilling Opportunities: Key skills and training needed
        
        Format the response as a structured JSON with these sections.
        """
    
    async def _get_ai_analysis(self, prompt: str) -> str:
        """Get analysis from OpenAI API"""
        if not self.api_key:
            # If no API key, return a mock response
            return json.dumps({
                "Impact Summary": {"summary": "Mock impact analysis without API key"},
                "Recommendations": ["Enable AI tools for this team", "Provide AI training"],
                "Risk Assessment": {"risks": "Without API key, detailed analysis is not available"},
                "Upskilling Opportunities": ["Learn prompt engineering", "Develop data analysis skills"]
            })
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_detail = await response.text()
                        print(f"Error calling OpenAI API: {response.status} - {error_detail}")
                        return json.dumps({
                            "Impact Summary": {"summary": f"API Error {response.status}"},
                            "Recommendations": ["Please check API configuration"],
                            "Risk Assessment": {"risks": "API integration issue"},
                            "Upskilling Opportunities": ["Review system configuration"]
                        })
        except Exception as e:
            print(f"Exception calling OpenAI API: {str(e)}")
            return json.dumps({
                "Impact Summary": {"summary": "Analysis failed due to API error"},
                "Recommendations": ["Check API key and connectivity"],
                "Risk Assessment": {"risks": f"Technical error: {str(e)}"},
                "Upskilling Opportunities": ["Setup reliable API access"]
            })
    
    def _process_response(self, response: str) -> Dict[str, Any]:
        """Process the response and structure it"""
        try:
            # Try to parse as JSON
            parsed = json.loads(response)
            return {
                "impact_summary": parsed.get("Impact Summary", {}),
                "recommendations": parsed.get("Recommendations", []),
                "risk_assessment": parsed.get("Risk Assessment", {}),
                "upskilling_opportunities": parsed.get("Upskilling Opportunities", [])
            }
        except json.JSONDecodeError:
            # Fallback if not valid JSON
            return {
                "impact_summary": {"summary": "Analysis generated but couldn't be structured properly"},
                "recommendations": ["Please refer to the AI for detailed recommendations"],
                "risk_assessment": {"risks": "Analysis needs review"},
                "upskilling_opportunities": ["Please consult with HR for appropriate upskilling paths"]
            }

    def _format_team_info(self, members: List[Dict[str, Any]]) -> str:
        """Format team member information for analysis"""
        formatted_info = []
        for member in members:
            formatted_info.append(
                f"Role: {member['role']}\n"
                f"Department: {member['department']}\n"
                f"Experience Level: {member['experience_level']}\n"
                f"Key Responsibilities:\n" + 
                "\n".join(f"- {resp}" for resp in member['responsibilities'])
            )
        return "\n\n".join(formatted_info) 