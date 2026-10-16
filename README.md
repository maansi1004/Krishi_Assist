# KrishiAssist 🌾

KrishiAssist is an AI-powered agricultural support platform designed to help farmers discover relevant government schemes, understand eligibility requirements, and organize their application journey.

## Key Features

- **Scheme discovery:** Browse and search structured agricultural schemes.
- **Explainable eligibility checks:** A deterministic rule engine evaluates scheme criteria and explains results, including missing or uncertain information.
- **Farmer profiles:** Maintain farmer information to support more relevant scheme discovery and eligibility checks.
- **Saved schemes and application tracking:** Save useful schemes and track application progress.
- **Application guidance:** Review required documents, application steps, and official scheme links.
- **Agriculture assistant:** Ask agriculture- and scheme-related questions.
- **Multilingual foundations:** Support for English, Hindi, and Hinglish experiences.
- **Eligibility reports:** Generate PDF reports from the application.

## Technology Stack

- **Frontend:** React, TypeScript, Vite
- **Backend:** Python, FastAPI
- **Database:** SQLAlchemy with SQLite by default
- **Authentication:** Password hashing and JWT
- **Scheme intelligence:** Structured JSON data and a deterministic eligibility engine
- **Testing:** pytest

## How It Works

1. A farmer creates a profile and explores available schemes.
2. KrishiAssist matches the farmer's information against scheme criteria.
3. The eligibility engine returns explainable outcomes, including conditions that need further verification.
4. The farmer reviews application guidance, saves schemes, and tracks progress.
5. The agriculture assistant provides additional support.

## Core Principle

**AI understands. Rules decide. Evidence explains. Workflow guides.**

Eligibility decisions are made by the rule-based engine rather than by a language model. Scheme information can change, so farmers should verify current requirements and deadlines with official sources before applying.

## Project Status

KrishiAssist is an evolving project. Scheme coverage, localization, assistant quality, security, and deployment readiness require ongoing testing and maintenance.
