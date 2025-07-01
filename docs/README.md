# TaskForge Documentation

## Overview
TaskForge is a full-stack Django web-application that automates the journey from **meeting recording ➜ transcript ➜ action-items ➜ human approval ➜ Monday.com**.

The project originated as an n8n workflow and has been rewritten as a maintainable Django app that works on SQLite for local development and **PostgreSQL on Railway**—with `DEBUG=True` everywhere per design.

---

## Contents
| File | Description |
|------|-------------|
| `architecture.md` | High-level diagram of apps, models, and data-flow |
| `api.md` | REST + HTML endpoints documented with request / response examples |
| `setup.md` | Local development & environment configuration |
| `deployment.md` | Railway deployment guide |
| `contributing.md` | Conventional commits, linting, tests & PR process |

> All docs live in this folder so GitHub Pages (or MkDocs) can easily render them.

---

## Quick links
* Public task list – [`/tasks/`](../templates/public_tasks.html)
* Admin – [`/admin/`](../taskforge/urls.py)
* Health probe – [`/health/`](../tasks/health.py)

---

## Next Steps
1. Generate Mermaid diagrams for data-model and request lifecycle.
2. Add screenshots / GIFs to illustrate the animated home page.
3. Publish these docs via **GitHub Pages** so non-technical stakeholders can explore the workflow. 