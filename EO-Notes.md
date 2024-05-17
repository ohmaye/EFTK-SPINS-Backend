# EFTK-SPINS-Backend

## Starting a separate backend for EFTK Surveys
- 2024.05.13 Vercel now supports Python 3.12 (only 3.9 before)
- pyenv installed 3.12.1
- pyenv shell 3.12.1
- poetry new eftk-spins-backend
- poetry env use 3.12.1 (it creates a .venv directory)
- poetry shell (to active env)
## FastAPI
- Changed
  - run using "fastapi dev main.py" for dev
  - use "fastapi run" for production
  - Add "fastapi run" to main.py to run it in vercel
## Vercel
- Had problems with deploying to Vercel with python 3.12
- Seems different from 3.9
- Didn't use uvicorn. Vercel installs the "app" (FastAPI) as a serverless function
- It then serves using its own http server connection
- vercel.json becomes very simple. Don't know about performance yet.