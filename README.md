Agent Forge AI
===============

Quickstart
----------

1) Install deps

```
uv sync
```

or

```
pip install -e .[dev]
```

2) Prepare docs

Place `.md` or `.txt` files under `doc/`. They will be embedded on startup.

3) Run API server

```
python -m agent-forge-ai
```

This launches FastAPI at http://localhost:8000

4) Run Streamlit debug UI

```
streamlit run streamlit_app.py
```

APIs
----
- POST `/open-session`
- POST `/search-documentation`
- POST `/get-document`
- POST `/find-document`
- POST `/create-agent`
- POST `/chat`


