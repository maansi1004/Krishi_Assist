from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class SchemeDocument(BaseModel):
    name: str
    requiredType: Literal["required", "conditional", "verification"]
    purpose: str | None = None
    verificationNote: str | None = None


class SchemeActionStep(BaseModel):
    step: int
    title: str
    description: str
    responsibleParty: str | None = None
    mode: Literal["online", "offline", "either"] | None = None
    dependency: str | None = None
    source: str | None = None


class SchemeSource(BaseModel):
    title: str
    sourceType: Literal["official", "reference", "verification_required"]
    url: str | None = None
    note: str | None = None


class SchemeTranslation(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None


class Scheme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemeCode: str
    name: str
    shortName: str | None = None
    level: Literal["central", "state", "district", "local"]
    state: str
    implementingDepartment: str
    category: str
    description: str
    eligibility: dict[str, Any]
    exclusions: dict[str, Any] | None = None
    verificationConditions: list[dict[str, Any]] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    benefitLimits: list[dict[str, Any]] = Field(default_factory=list)
    coverageConditions: list[str] = Field(default_factory=list)
    documents: list[SchemeDocument] = Field(default_factory=list)
    actionSteps: list[SchemeActionStep] = Field(default_factory=list)
    applicationChannels: list[str] = Field(default_factory=list)
    officialPortals: list[str] = Field(default_factory=list)
    sources: list[SchemeSource] = Field(default_factory=list)
    targetingNotes: list[str] = Field(default_factory=list)
    allocationPolicy: list[str] = Field(default_factory=list)
    geographicTargeting: list[str] = Field(default_factory=list)
    procurementConditions: list[str] = Field(default_factory=list)
    rawSourceText: list[str] = Field(default_factory=list)
    lastVerifiedAt: str | None = None
    status: Literal["active", "inactive", "verification_required"] = "active"
    translations: dict[str, SchemeTranslation] = Field(default_factory=dict)
