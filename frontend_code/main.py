import flet as ft
import requests
import threading
import time

# === Backend Configuration ===
BACKEND_URL = "http://127.0.0.1:5000"  # PC ip addressS

def main(page: ft.Page):
    # === Page Setup ===
    page.title = "Smart Farm Dashboard"
    page.window_width = 800
    page.window_height = 600
    page.bgcolor = ft.Colors.BLACK

    # === Background Image (Full Screen) ===
    background = ft.Image(
        src="farm.jpg",         # farm image 
        fit=ft.ImageFit.COVER,
        expand=True
    )
    # === Sensor Readings ===
    moisture_txt = ft.Text("Soil Moisture: --", size=20, color=ft.Colors.WHITE)
    rain_txt = ft.Text("Rain Status: --", size=20, color=ft.Colors.CYAN)

    # === Control Widgets ===
    pump_swi = ft.Switch(label="Water Pump", value=False)
    angle_sli = ft.Slider(min=0, max=180, divisions=18, label="{value}°", value=90)

    # === Status Card ===
    status_card = ft.Card(
        elevation=4,
        content=ft.Container(
            content=ft.Column(
                controls=[moisture_txt, rain_txt],
                spacing=10
            ),
            padding=20,
            width=350,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            border_radius=10
        )
    )

    # === Control Panel Card ===
    control_card = ft.Card(
        elevation=4,
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Controls", size=22, weight="bold", color=ft.Colors.LIGHT_GREEN),
                    ft.Text("Sprinkler Angle", size=16, color=ft.Colors.WHITE),
                    angle_sli,
                    pump_swi,
                    ft.ElevatedButton(
                        "Send",
                        icon=ft.Icons.SEND,
                        on_click=lambda _: send_controls(),
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)
                    )
                ],
                spacing=15
            ),
            padding=20,
            width=350,
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK),
            border_radius=10
        )
    )

    # === Title and Layout ===
    title = ft.Text("Smart Garden System", size=32, weight="bold", color=ft.Colors.LIGHT_GREEN)

    dashboard_layout = ft.Column(
        controls=[
            title,
            ft.Row(
                controls=[status_card, control_card],
                alignment="center"
            )
        ],
        spacing=40,
        top=40
    )

    # === Stack Everything with Background ===
    page.add(
        ft.Stack(
            controls=[
                background,
                dashboard_layout
            ]
        )
    )

    # === Fetch Sensor Data Continuously ===
    def update_sensor_data():
        while True:
            try:
                res = requests.get(f"{BACKEND_URL}/status")
                data = res.json()
                moisture = data.get("moisture", 0)
                rain = data.get("rain", 0)
                # Update UI
                moisture_txt.value = f"Soil Moisture: {moisture}/4095"
                rain_txt.value = f"Rain Status: {'Detected' if rain else 'Clear'}"
                page.update()
            except Exception as e:
                print("Sensor fetch error:", e)
            time.sleep(5)  # Fetch every 5 seconds

    # === Send Control Settings to Backend ===
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

    # === Start Sensor Update Thread ===
    threading.Thread(target=update_sensor_data, daemon=True).start()

# === Launch App ===
if __name__ == "__main__":
    ft.app(target=main)