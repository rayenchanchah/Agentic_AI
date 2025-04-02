from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class AIWorkforceAnalyzer:
    def __init__(self):
        self.llm = OpenAI(
            temperature=0.7,
            model_name="gpt-4",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.impact_prompt = PromptTemplate(
            input_variables=["team_info", "industry", "company_size"],
            template="""
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
        )
        
        self.impact_chain = LLMChain(llm=self.llm, prompt=self.impact_prompt)

    async def analyze_team(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the impact of AI on a team and generate recommendations
        """
        # Format team information
        team_info = self._format_team_info(request["members"])
        
        # Generate analysis
        analysis = await self.impact_chain.arun(
            team_info=team_info,
            industry=request["industry"],
            company_size=request["company_size"]
        )
        
        # Process and structure the response
        return {
            "team_name": request["team_name"],
            "impact_summary": self._extract_impact_summary(analysis),
            "recommendations": self._extract_recommendations(analysis),
            "risk_assessment": self._extract_risk_assessment(analysis),
            "upskilling_opportunities": self._extract_upskilling_opportunities(analysis)
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

    def _extract_impact_summary(self, analysis: str) -> Dict[str, Any]:
        """Extract impact summary from analysis"""
        # Implementation would parse the analysis string to extract impact summary
        # This is a placeholder - actual implementation would use proper JSON parsing
        return {"summary": "Impact summary placeholder"}

    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommendations from analysis"""
        # Implementation would parse the analysis string to extract recommendations
        return ["Recommendation placeholder"]

    def _extract_risk_assessment(self, analysis: str) -> Dict[str, Any]:
        """Extract risk assessment from analysis"""
        # Implementation would parse the analysis string to extract risk assessment
        return {"risks": "Risk assessment placeholder"}

    def _extract_upskilling_opportunities(self, analysis: str) -> List[str]:
        """Extract upskilling opportunities from analysis"""
        # Implementation would parse the analysis string to extract upskilling opportunities
        return ["Upskilling opportunity placeholder"] 