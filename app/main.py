import time
import traceback

if __name__ == "__main__":
    while True:
        try:
            from app.views import app
        except Exception:
            traceback.print_exc()
            print()
            time.sleep(3)
        else:
            app.run(debug=True)

