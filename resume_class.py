from typing import List, Optional, Dict
from pydantic import BaseModel, Field, AnyUrl, EmailStr, field_validator
import re


class Education(BaseModel):
    degree: str = Field(
        ..., description="The degree earned (e.g., 'BS Software Engineering')"
    )
    institution: str = Field(
        ...,
        description="The institution name (e.g., 'Government College University, Faisalabad')",
    )
    years: str = Field(..., description="The duration of study (e.g., '2019 – 2023')")


class Experience(BaseModel):
    job_title: str = Field(
        ..., description="The job title (e.g., 'Software Engineer (Team Lead)')"
    )
    company: str = Field(..., description="The company name (e.g., 'Netixsol')")
    duration: str = Field(
        ..., description="The duration of employment (e.g., 'Aug 2024 - July 2025')"
    )
    description: str = Field(
        ..., description="A brief description of responsibilities or achievements"
    )


class Project(BaseModel):
    title: str = Field(..., description="Project name/title")
    description: str = Field(..., description="Short description of the project")
    technologies: List[str] = Field(
        default_factory=list, description="Technologies used in the project"
    )


class SocialLinks(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    twitter: Optional[str] = None

    @field_validator("*", mode="before")
    def clean_social_urls(cls, v):
        if not v or str(v).lower() in ["null", "none", "n/a", "nan"]:
            return None
        if not re.match(r"^https?://", str(v).strip()):
            return None
        return v


class Resume(BaseModel):
    name: str = Field(..., description="Full name of the candidate")
    email: str = Field(..., description="Candidate's email address")
    phone: Optional[str] = Field(default=None, description="Candidate's phone number")
    bio: str = Field(..., description="Brief introduction or summary of the candidate")
    address: Optional[str] = Field(
        None, description="Physical location (e.g., 'Faisalabad, Pakistan')"
    )
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None

    social_links: Optional[SocialLinks]
    education: List[Education] = Field(
        default_factory=list, description="List of education entries"
    )
    experience: List[Experience] = Field(
        default_factory=list, description="List of work experience entries"
    )
    skills: Optional[List[str]] = Field(
        default_factory=list,
        description="List of skills and tools (e.g., ['JS', 'Python'])",
    )

    strengths: Optional[List[str]] = Field(default_factory=list)
    weaknesses: Optional[List[str]] = Field(default_factory=list)
    recommendations: Optional[List[str]] = Field(default_factory=list)
    resume_score: Optional[int] = Field(None, ge=0, le=100)
    ats_friendly: Optional[bool] = None
    ats_issues: Optional[List[str]] = Field(default_factory=list)
    missing_skills: Optional[List[str]] = Field(default_factory=list)
    highlights: Optional[List[str]] = Field(default_factory=list)
    suggested_roles: Optional[List[str]] = Field(default_factory=list)

    @field_validator("linkedin", mode="before")
    @classmethod
    def clean_empty(cls, v):
        if not v or v == {} or v == [] or (isinstance(v, str) and not v.strip()):
            return None
        return v

    @field_validator("social_links", mode="before")
    @classmethod
    def clean_social_links(cls, v):
        if not v or v == {}:
            return {}
        # Clean each URL in the dictionary
        return {
            key: None if (val in ("", {}, []) or not str(val).strip()) else val
            for key, val in v.items()
        }

    @field_validator("*", mode="before")
    def clean_urls(cls, v):
        if not v or str(v).lower() in ["null", "none", "n/a", "nan"]:
            return None
        return v
