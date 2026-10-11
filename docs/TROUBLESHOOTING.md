# Troubleshooting
**Backend not configured:** Phase 1 ships no backend. `127.0.0.1` from a Pages visitor means that visitor's device, not your workstation.

**CORS:** the backend must allow the exact origin, methods and headers needed. Avoid wildcard origins with credentials. **Private Network Access:** browser preflight may require `Access-Control-Allow-Private-Network: true` alongside normal CORS headers; browser behavior varies. **Mixed content:** HTTPS Pages may block HTTP API calls to local/private endpoints. Safari may restrict HTTPS pages calling HTTP localhost. Do not assume these routes work.

**Fallback setup procedure:** run `python scripts/dev_server.py` and open `http://127.0.0.1:8000/` locally instead of Pages. This is a documented fallback procedure, not a claim that browser-specific PNA behavior was tested. If the API is on another port, configure CORS correctly. Do not expose a future backend without authentication and request limits.

Image checks in the UI are not a substitute for backend-side validation. Model unavailable is expected until a compatible backend reports model capabilities.
