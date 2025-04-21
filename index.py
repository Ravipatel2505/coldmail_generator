from flask import Flask, render_template, request
from utils import process_job_url  # this function contains all your logic

app = Flask(__name__, template_folder="../templates", static_folder="../static")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        job_url = request.form.get("job_url")
        try:
            email = process_job_url(job_url)
            return render_template("result.html", email=email)
        except Exception as e:
            return f"Error occurred: {e}"
    return render_template("index.html")

# Needed for Vercel
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

if __name__ == "__main__":
    app.run()
