"""HTTP API for the MediLens app.

    uvicorn medilens.api:app --reload

The app sends only the recognised text of a prescription, never the photo.
Nothing is stored.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from medilens import __version__
from medilens.analysis import DISCLAIMER, PrescriptionAnalyzer


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000, description="Text read from the prescription.")


class AnalyzeResponse(BaseModel):
    medicines: list[dict]
    disclaimer: str


def create_app(analyzer: PrescriptionAnalyzer | None = None) -> FastAPI:
    app = FastAPI(title="MediLens API", version=__version__)
    app.state.analyzer = analyzer

    def get_analyzer() -> PrescriptionAnalyzer:
        if app.state.analyzer is None:
            app.state.analyzer = PrescriptionAnalyzer()
        return app.state.analyzer

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/analyze", response_model=AnalyzeResponse)
    def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
        cards = get_analyzer().analyze(request.text)
        return AnalyzeResponse(medicines=[asdict(c) for c in cards], disclaimer=DISCLAIMER)

    return app


app = create_app()
