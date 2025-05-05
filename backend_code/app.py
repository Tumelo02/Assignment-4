from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # Allow Flet or any frontend to connect

# Store latest sensor readings and control states
sensor_data = {
    "moisture": 0,
    "rain": 0,
    "timestamp": None
}

control_state = {
    "pump": 0,    # 0 = OFF, 1 = ON
    "angle": 90   # Default servo angle
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

    # For future use - allow Flet or API to update control state
    data = request.get_json()
    control_state["pump"] = data.get("pump", control_state["pump"])
    control_state["angle"] = data.get("angle", control_state["angle"])
    print(f"Updated Control State: {control_state}")
    return jsonify({"status": "updated"}), 200

@app.route("/status", methods=["GET"])
def status():
    # Allow frontend to fetch sensor readings
    return jsonify(sensor_data), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)