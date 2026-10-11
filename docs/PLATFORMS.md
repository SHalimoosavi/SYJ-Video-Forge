# Platform notes
The static UI uses standard browser APIs and ES modules. No build or npm install is required. Python 3 provides the optional server; Node.js runs tests and has an optional server.

- Linux/macOS/Android shell: `python3 scripts/dev_server.py`
- Windows: `python scripts/dev_server.py` or `py scripts/dev_server.py`
- Node: `node scripts/dev-server.mjs`
- Tests: `node --test tests/*.test.js`
- Static check: `python3 scripts/static_check.py`

Android is one platform among equals. No Docker requirement and no model download. Inference depends on each model's OS, accelerator, memory and license requirements.
