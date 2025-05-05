import flet as ft
import requests
import threading
import time

BACKEND_URL = "http://127.0.0.1:5000"  # Flask server IP

def main(page: ft.Page):
    page.title = "Garden Dashboard"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Components
    moisture_txt = ft.Text("Soil Moisture: --", size=20)
    rain_txt = ft.Text("Rain Status: --", size=20, color=ft.colors.BLUE)

    pump_swi = ft.Switch(label="Water Pump", value=False)
    angle_sli = ft.Slider(min=0, max=180, divisions=18, label="{value}°", value=90)

    status_cad = ft.Card(
        content=ft.Container(
            content=ft.Column([
                moisture_txt,
                rain_txt,
            ]),
            padding=20
        )
    )

    control_cad = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Sprinkler Angle", weight="bold"),
                angle_sli,
                pump_swi,
                ft.ElevatedButton("Apply Controls", on_click=lambda _: send_controls())
            ]),
            padding=20
        )
    )

    page.add(
        ft.Text("Smart Garden System", size=26, weight="bold"),
        ft.Row([status_cad, control_cad], alignment="center"),
    )

    # Update sensor readings
    def update_sensor_data():
        while True:
            try:
                res = requests.get(f"{BACKEND_URL}/status")
                data = res.json()
                moisture = data.get("moisture", 0)
                rain = data.get("rain", 0)
                moisture_txt.value = f"Soil Moisture: {moisture}/4095"
                rain_txt.value = f"Rain Status: {'Detected' if rain else 'Clear'}"
                page.update()
            except Exception as e:
                print("Sensor fetch error:", e)
            time.sleep(5)

    # Send control state to backend
    def send_controls():
        try:
            control_data = {
                "pump": int(pump_swi.value),
                "angle": int(angle_sli.value)
            }
            res = requests.post(f"{BACKEND_URL}/control", json=control_data)
            print("Control updated:", res.json())
        except Exception as e:
            print("Control send error:", e)

    # Start background sensor thread
    threading.Thread(target=update_sensor_data, daemon=True).start()

# Run the app
if __name__ == "__main__":
    ft.app(target=main)