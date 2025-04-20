import json
import google.generativeai as genai
from typing import List, Dict
import time
from difflib import SequenceMatcher
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

class LLMRecommender:
    def __init__(self, data_path: str = "data/shl_assessments_full.json"):
        try:
            with open(Path(__file__).parent.parent / data_path) as f:
                self.assessments = json.load(f)
            self.name_mapping = {a['name'].lower(): a for a in self.assessments}
            self.descriptions = [self._format_assessment(a) for a in self.assessments]
        except FileNotFoundError:
            raise RuntimeError(f"Data file {data_path} not found")

    def _format_assessment(self, assessment: Dict) -> str:
        """Enhanced formatting for better LLM understanding"""
        return (
            f"Assessment: {assessment['name']}\n"
            f"Types: {', '.join(assessment['test_type'])}\n"
            f"Duration: {assessment['duration']} mins\n"
            f"Remote: {assessment['remote_support']}\n"
            f"Adaptive: {assessment['adaptive_support']}\n"
            f"Description: {assessment['description']}"
        )

    def _find_closest_match(self, name: str) -> str:
        """Fuzzy match for assessment names"""
        name_lower = name.lower()
        return max(
            self.name_mapping.keys(),
            key=lambda x: SequenceMatcher(None, x, name_lower).ratio()
        )

    def recommend(self, query: str, max_results: int = 5) -> List[Dict]:
        """Get recommendations with error handling and fuzzy matching"""
        try:
            response = model.generate_content(
                f"""Analyze this job requirement and match to SHL assessments:
                Job Requirement: {query}
                Available Assessments:\n{"-"*30}\n{'\n'.join(self.descriptions)}
                Return ONLY comma-separated list of {max_results} most relevant assessment names.
                Consider duration, test types, and description.
                Format: "Name1, Name2, ..."
                """
            )
            
            # Clean and validate response
            cleaned_names = [
                name.strip() 
                for name in response.text.split(",") 
                if name.strip()
            ]
            
            # Fuzzy match to handle minor name discrepancies
            results = []
            for name in cleaned_names[:max_results]:
                try:
                    match = self._find_closest_match(name)
                    results.append(self.name_mapping[match])
                except KeyError:
                    continue

            return results

        except Exception as e:
            print(f"⚠️ Recommendation error: {str(e)}")
            return []

if __name__ == "__main__":
    try:
        recommender = LLMRecommender()
        print("🌟 SHL Assessment Recommender 🌟")
        print("Type 'exit' to quit\n")
        
        while True:
            # Get user input
            query = input("Enter job requirements (or 'exit'): ")
            if query.lower() in ['exit', 'quit']:
                break
                
            if not query.strip():
                print("⚠️ Please enter a valid query\n")
                continue
                
            # Get recommendations
            results = recommender.recommend(query)
            
            # Display results
            print("\n🔍 Results for:", query)
            for i, res in enumerate(results, 1):
                print(f"{i}. {res['name']}")
                print(f"   URL: {res['url']}")
                print(f"   Duration: {res['duration']} mins")
                print(f"   Types: {', '.join(res['test_type'])}")
                print(f"   Description: {res['description'][:100]}...\n")
            
            print("―" * 50 + "\n")
            
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"🔥 Error: {str(e)}")