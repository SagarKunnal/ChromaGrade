import uvicorn
import os
import sys

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))

    print("=" * 60)
    print("  ChromaGrade Pro — Color Grade Transfer Studio")
    print(f"  Running at: http://{host}:{port}")
    print("=" * 60)

    uvicorn.run("app.main:app", host=host, port=port, reload=False)
