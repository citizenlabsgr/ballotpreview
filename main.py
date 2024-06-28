"""
Quart development server with automatic restarts.
"""

import time
import traceback
import log


def run():
    log.init()
    log.silence("asyncio", "quart.serving")
    while True:
        try:
            from app.views import app  # pylint: disable=import-outside-toplevel
        except Exception:
            traceback.print_exc()
            print()
            time.sleep(3)
        else:
            app.run(debug=True)
            break


if __name__ == "__main__":
    run()
