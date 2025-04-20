# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from recommender.llm_recommender import LLMRecommender
import uvicorn

app = FastAPI(
    title="SHL Assessment Recommender API",
    description="API for recommending SHL assessments based on job requirements",
    version="1.0.0"
)

# Initialize recommender
recommender = LLMRecommender()

class RecommendationRequest(BaseModel):
    query: str
    max_duration: Optional[int] = None
    top_k: Optional[int] = 10

class HealthCheckResponse(BaseModel):
    status: str

@app.get("/health", response_model=HealthCheckResponse, tags=["Monitoring"])
async def health_check():
    """Health check endpoint"""
    return {"status": "OK"}

@app.post("/recommend", tags=["Recommendations"])
async def get_recommendations(request: RecommendationRequest):
    """Assessment recommendation endpoint"""
    try:
        # Validate input
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if request.top_k and (request.top_k < 1 or request.top_k > 10):
            raise HTTPException(status_code=400, detail="top_k must be between 1 and 10")

        # Get recommendations
        results = recommender.recommend(
            query=request.query,
            max_results=request.top_k
        )

        # Format response according to spec
        formatted_results = []
        for assessment in results:
            formatted_results.append({
                "name": assessment["name"],
                "url": assessment["url"],
                "remote_support": assessment["remote_support"],
                "adaptive_support": assessment["adaptive_support"],
                "duration": assessment["duration"] if assessment["duration"] != -1 else "N/A",
                "test_type": assessment["test_type"]
            })

        return {"recommended_assessments": formatted_results[:request.top_k]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)