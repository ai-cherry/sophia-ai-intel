# Agno Agentic Service

This service is the central hub for all Agno AI agentic capabilities within the Sophia AI ecosystem. It provides a unified interface for managing and coordinating "swarms" of AI agents to perform complex tasks.

## Overview

The Agno Agentic Service is a Python application built with FastAPI. It is designed to be a scalable and extensible platform for developing and deploying agent-based systems. The service integrates with the broader Sophia AI infrastructure, including our data stores, and CI/CD pipelines.

## Key Features

- **Unified Agent Management:** A single point of control for all Agno agents and swarms.
- **Swarm Coordination:** Manages the execution of complex tasks by coordinating the efforts of multiple agents.
- **Extensible Tooling:** Agents can be equipped with a variety of tools to perform a wide range of tasks.
- **Scalable Architecture:** Built on a modern, asynchronous Python stack to handle a high volume of requests.

## Getting Started

1.  **Install dependencies:**
    ```bash
    pip install -e .[dev]
    ```
2.  **Run the service:**
    ```bash
    uvicorn src.main:app --reload
    ```

## Development

This service follows the standard development practices of the `sophia-ai-intel` monorepo. Please refer to the root `README.md` for more information on our development workflow.