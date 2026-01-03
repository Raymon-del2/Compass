def handler(request):
    # Simple test: always return JSON
    return {
        "status": "ok",
        "message": "Python runtime loaded",
        "path": request.path
    }
