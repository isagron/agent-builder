import uvicorn


def main():
    uvicorn.run(
        "app.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=False,
    )


if __name__ == "__main__":
    main()
