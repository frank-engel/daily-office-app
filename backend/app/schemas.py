"""Pydantic response models shared across API routes."""
from __future__ import annotations

from pydantic import BaseModel, Field


class VerseResponse(BaseModel):
    book: str = Field(description="SBL book abbreviation, e.g. 'Isa'")
    chapter: int
    verse: int
    text: str


class PsalmVerseResponse(BaseModel):
    psalm: int = Field(description="Psalm number (1–150)")
    verse: int
    text: str


class PsalmEntry(BaseModel):
    psalm: int = Field(description="Psalm number")
    verses: list[PsalmVerseResponse]


class LessonEntry(BaseModel):
    reference: str | None = Field(
        description="Raw lectionary reference string, e.g. 'Isa 1:1–9'"
    )
    verses: list[VerseResponse]


class PsalmGroup(BaseModel):
    morning: list[PsalmEntry]
    evening: list[PsalmEntry]


class OfficeResponse(BaseModel):
    date: str = Field(description="ISO date, e.g. '2026-05-24'")
    title: str | None = Field(description="Feast or Sunday title, if any")
    season: str = Field(description="Liturgical season, e.g. 'Easter'")
    week: str = Field(description="Week name as used in the lectionary, e.g. 'Week of 7 Easter'")
    cycle: int = Field(description="Lectionary year cycle: 1 (Year One) or 2 (Year Two)")
    psalms: PsalmGroup
    morning_lessons: dict[str, LessonEntry] = Field(
        description="Morning lessons keyed by slot: 'first', 'second', 'gospel'"
    )
    evening_lessons: dict[str, LessonEntry] = Field(
        description="Evening lessons keyed by slot: 'first', 'second'"
    )
    reflection: None = Field(
        default=None,
        description="Reserved for post-MVP AI reflection (always null in MVP)"
    )


class BibleResponse(BaseModel):
    reference: str = Field(description="The reference string as requested")
    verses: list[VerseResponse]
