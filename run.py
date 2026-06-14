import uvicorn
import webbrowser
import threading
import time

def open_browser():
    # Wait 2 seconds to give the server time to start up
    time.sleep(2)
    print("\n🌐 Opening your browser automatically to the testing page...\n")
    # Using port 8080 and localhost to bypass all previous errors
    webbrowser.open("http://localhost:8080/docs")

if __name__ == "__main__":
    # 1. Start a background thread to open the browser automatically
    threading.Thread(target=open_browser, daemon=True).start()

    # 2. Start the FastAPI server on a fresh port (8080)
    print("🚀 Starting AI Knowledge Assistant...")
    uvicorn.run("main:app", host="127.0.0.1", port=8080)