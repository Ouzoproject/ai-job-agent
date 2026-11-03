from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.agent.agent import run_agent
from app.services.cv_parser import CVParsingError, extract_text

MAX_CV_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_MESSAGE_LENGTH = 2_000

app = FastAPI(
    title="AI Job Agent",
    description="AI-powered job agent using MCP",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search")
async def search(
    message: str = Form(
        default="Find jobs that match my CV.",
        description="Extra instructions, e.g. desired role or location.",
    ),
        cv: UploadFile | None = File(
        default=None,
        description="Optional CV file (.pdf, .docx, .txt, .md).",
        ),
    ):
    """
    Run the job-search agent. If a CV is attached, its text is extracted
    and given to the agent.
    """

    message = message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )   

    if len(message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Message is too long. Maximum length is {MAX_MESSAGE_LENGTH} characters.",
        )
    
    cv_text = None

    if cv is not None:
        file_bytes = await cv.read(MAX_CV_SIZE + 1)

        if len(file_bytes) > MAX_CV_SIZE:
            raise HTTPException(
                status_code=413,
                detail="CV file is too large. Maximum allowed size is 5 MB.",
            )

        try:
            cv_text = extract_text(file_bytes, cv.filename or "cv")
        except CVParsingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = await run_agent(user_message=message, cv_text=cv_text)

    return {"response": result}