#!/usr/bin/env python3
"""
RedSaaS — 紅隊作戰平台
啟動：python app.py
開啟：http://localhost:5001
"""
from flask import Flask, send_from_directory

from routes.scan     import bp as scan_bp
from routes.tools    import bp as tools_bp
from routes.reports  import bp as reports_bp
from routes.images   import bp as images_bp
from routes.infra    import bp as infra_bp
from routes.lab      import bp as lab_bp

app = Flask(__name__, static_folder="static", static_url_path="/static")

@app.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers.pop("ETag", None)
    resp.headers.pop("Last-Modified", None)
    return resp

app.register_blueprint(scan_bp)
app.register_blueprint(tools_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(images_bp)
app.register_blueprint(infra_bp)
app.register_blueprint(lab_bp)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
