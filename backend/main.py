import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from theme_picker import pick_theme, pick_letter

FRONTEND = Path(__file__).parent.parent / "frontend"

app = FastAPI(title="Jeu de Lettres")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValidateRequest(BaseModel):
    theme: str
    lettre: str
    answers: list[str]
    langue: str = "fr"


@app.get("/api/draw")
async def draw(langue: str = "fr", seed: int | None = None):
    return {
        "lettre": pick_letter(seed=seed),
        "theme": pick_theme(langue=langue, seed=seed),
    }


@app.post("/api/validate")
async def validate(req: ValidateRequest):
    try:
        result = await _call_claude(req.theme, req.lettre, req.answers, req.langue)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _call_claude(theme: str, lettre: str, answers: list, langue: str) -> str:
    from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

    if not answers:
        return ("Aucune réponse soumise. Score : 0 / 0."
                if langue == "fr"
                else "No answers submitted. Score: 0 / 0.")

    answers_str = ", ".join(answers)
    n = len(answers)

    if langue == "fr":
        prompt = (
            f'Jeu : le joueur devait nommer des éléments sur le thème "{theme}" '
            f"commençant par la lettre {lettre}.\n"
            f"Réponses : {answers_str}\n\n"
            f"Pour chaque réponse, écris sur une ligne : MOT — ✅ VALIDE ou ❌ INVALIDE (brève raison). "
            f"Sois indulgent pour les accents manquants et variantes orthographiques. "
            f"Conclus avec une ligne : **Score : X / {n}**"
        )
    else:
        prompt = (
            f'Game: the player had to name items related to "{theme}" '
            f"starting with the letter {lettre}.\n"
            f"Answers: {answers_str}\n\n"
            f"For each answer, write on one line: WORD — ✅ VALID or ❌ INVALID (brief reason). "
            f"Conclude with one line: **Score: X / {n}**"
        )

    result = ""
    async for msg in query(prompt=prompt, options=ClaudeAgentOptions(allowed_tools=[])):
        if isinstance(msg, ResultMessage):
            result = msg.result
    return result


# Serve frontend — defined last so API routes take priority
app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="static")
