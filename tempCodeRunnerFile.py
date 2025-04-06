
    """Render the About page."""
    return render_template("about.html")

@app.route("/process", methods=["POST"])
def process():
    """Process text input and return Gemini's response."""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "No query provided"}), 400

        user_input = data["query"]
        response = ask_gemini(user_input)
        speak(response)  # Optional: Speak the response
        return jsonify({"response": response})
    except Exception as e: