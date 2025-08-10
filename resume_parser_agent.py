import os, mimetypes, pdfplumber
from dotenv import load_dotenv
from fastapi import FastAPI
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    AsyncOpenAI,
    RunContextWrapper,
    set_tracing_disabled,
    Runner,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from docx import Document
from io import BytesIO
from pdf2image import convert_from_bytes
import pytesseract
from resume_class import Resume
from datetime import datetime

load_dotenv()

# Disabling tracing
# set_tracing_disabled(True)

# Color codes for terminal output styling
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"

google_key = os.getenv("GOOGLE_API_KEY")
base_url = os.getenv("base_url")

# Setting the OpenAI client
client: AsyncOpenAI = AsyncOpenAI(
    api_key=google_key,
    base_url=base_url,
)

# setting the LLM model using OpenAIChatCompletionsModel
llm: OpenAIChatCompletionsModel = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash", openai_client=client
)


def dynamic_instructions(wrapper: RunContextWrapper, agent: Agent) -> str:
    current_datetime = datetime.now()
    print("Current date and time:", current_datetime)
    return f"""
You are a resume analysis agent named {agent.name} and current time and date is {current_datetime}.
You will receive raw text extracted from a resume (may contain broken formatting, OCR errors, or noisy text).
Your task is to parse and analyze it to produce a structured JSON object matching the `Resume` model provided by the system.

## Core Parsing Rules
- Extract all factual resume details into the correct fields (name, contact, education, experience, skills, projects, links, etc.).
- Handle missing or malformed data gracefully by returning `null` or empty lists.
- Normalize text formatting (remove extra spaces, fix capitalization, standardize date formats where possible).

## Advanced Analysis Rules
In addition to structured resume fields, you must:
1. **Strengths** → List the strongest aspects of the resume (e.g., technical expertise, leadership, diverse experience, measurable achievements).
2. **Weaknesses** → List areas that could be improved (e.g., missing metrics, vague job descriptions, formatting issues).
3. **Recommendations** → Actionable steps to improve the resume (e.g., "Add quantified achievements", "Include a project section").
4. **Resume Score** → Give a score (0–100) based on completeness, clarity, ATS-friendliness, and role relevance.
5. **ATS Friendliness Check**
    - `ats_friendly`: true/false
    - `ats_issues`: List issues that might cause ATS rejection (e.g., images, non-standard fonts, missing keywords).
6. **Missing Skills** → Skills relevant to the candidate’s domain that are not present in the resume.
7. **Highlights** → The top 3–5 notable achievements or facts from the resume.
8. **Suggested Roles** → Job titles the candidate appears qualified for based on skills and experience.

## Output Requirements
- Return a valid JSON object matching the `Resume` model.
- All URLs must be valid or `null`. if a url You think is not valid for an item(github, linkedin, website etc), return `null` for that.
- Dates must remain as strings in their original format.
- If a section is not found, return an empty list or `null` for that field according to `Resume` model.
- Be concise but accurate in descriptions.

Focus on accurate extraction, normalization, and meaningful analysis.
"""


resume_parser_agent = Agent(
    name="Resume Parser Agent",
    instructions=dynamic_instructions,
    model=llm,
    output_type=Resume,
)

origins = [
    os.getenv("FRONTEND_URL"),
    "http://localhost:5173",
]

app = FastAPI(
    title="Resume Parser Agent",
    description="A resume parse agent that extracts information from resumes from various formats.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/system-health")
async def system_health():
    """Endpoint to check the health of the system"""

    return {"status": "System is online"}


@app.post("/parse-resume", tags=["Resume Parsing"])
async def parse_resume(file: UploadFile = File(...)):
    """Endpoint to run the agent and parse the resume"""

    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]

    # Get file MIME type
    file_type = mimetypes.guess_type(file.filename)[0]

    if not file_type or file_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF and DOCX files are allowed.",
        )

    # Validate file size (e.g max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size allowed is {max_size/1024/1024}MB.",
        )
    parsed_content = {"text": "", "file_type": file_type, "filename": file.filename}

    try:
        if file_type == "application/pdf":
            print("Processing PDF file")
            with pdfplumber.open(BytesIO(content)) as pdf:
                print("am in pdf loop")
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            parsed_content["text"] = text.strip()
            # print("parsed", parsed_content["text"])
            if not parsed_content["text"]:
                raise HTTPException(
                    status_code=400,
                    detail="No extractable text found in PDF. It might be a scanned or blank document.",
                )

        else:  # DOCX
            doc = Document(BytesIO(content))
            parsed_content["text"] = "\n".join([para.text for para in doc.paragraphs])
            # print("processing docx", parsed_content["text"])

        #  call the agent to parse the resume
        if parsed_content["text"].strip() != "":
            # Run the resume parser agent
            result: Runner = await Runner.run(
                starting_agent=resume_parser_agent, input=parsed_content["text"]
            )
            return {
                "status": "Resume parsed",
                "content": {
                    "file_type": parsed_content["file_type"],
                    "filename": parsed_content["filename"],
                    "structured": result.final_output,
                },
            }
        else:
            raise HTTPException(
                status_code=400, detail="No text could be extracted from the resume."
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")
