import os
from flask import Flask, jsonify

app = Flask(__name__)
TENANT_NAME = os.environ.get("TENANT_NAME", "demo")

@app.route("/")
def home():
    return f"""
    <!DOCTYPE html>
    <html>
      <head><title>Tenant Application</title></head>
      <body style="font-family:Arial;text-align:center;margin-top:100px">
        <h1>Tenant: {TENANT_NAME}</h1>
        <p>Your isolated application is running successfully.</p>
      </body>
    </html>
    """

@app.route("/health")
def health():
    return jsonify(status="healthy", tenant=TENANT_NAME)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
    