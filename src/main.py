"""Start DawnDispatch with uvicorn:  python -m src.main   (HOST default 127.0.0.1, PORT default 8090)."""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8090"))
    print(f"DawnDispatch: http://{host}:{port}/call  |  /dashboard  |  /live")
    uvicorn.run("src.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
