from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # Allow frontend to connect

# === Global State ===
sensor_data = {
    "moisture": 0,
    "rain": 0,
    "timestamp": None
}

control_state = {
    "pump": 0,       # Manual override (1 = force ON, 0 = allow auto)
    "angle": 90      # Sprinkler angle
}

@app.route("/data", methods=["POST"])
def receive_data():
    data = request.get_json()
    sensor_data["moisture"] = data.get("moisture", 0)
    sensor_data["rain"] = data.get("rain", 0)
    sensor_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"Received Sensor Data: {sensor_data}")
    return jsonify({"status": "success"}), 200

@app.route("/control", methods=["GET", "POST"])
def control():
    if request.method == "GET":
        return jsonify(control_state), 200

    # Update control state (manual pump override and angle)
    data = request.get_json()
    control_state["pump"] = data.get("pump", control_state["pump"])
    control_state["angle"] = data.get("angle", control_state["angle"])

    print(f"Updated Control State: {control_state}")
    return jsonify({"status": "updated"}), 200

@app.route("/status", methods=["GET"])
def status():
    # Auto control logic
    moisture = sensor_data.get("moisture", 0)
    manual_override = control_state["pump"]

    if manual_override == 1:
        pump_status = 1
        mode = "manual"
    else:
        # Auto mode logic
        if moisture < 1000:
            pump_status = 1
        else:
            pump_status = 0
        mode = "auto"

    response = {
        "moisture": sensor_data["moisture"],
        "rain": sensor_data["rain"],
        "timestamp": sensor_data["timestamp"],
        "pump_status": pump_status,
        "mode": mode,
        "angle": control_state["angle"]
    }

    return jsonify(response), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)