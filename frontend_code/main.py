import flet as ft
import requests
import threading
import time

# === Backend Configuration ===
BACKEND_URL = "http://127.0.0.1:5000"  # Update this if accessing over a network

def main(page: ft.Page):
    # === Page Setup ===
    page.title = "Smart Garden Dashboard"
    page.window_width = 800
    page.window_height = 600
    page.bgcolor = ft.Colors.BLACK

    # === Background Image (Full Screen) ===
    background = ft.Image(
        src="farm.jpg",  # image 
        fit=ft.ImageFit.COVER,
        expand=True
    )

    # === UI Display Elements ===
    moisture_txt = ft.Text("Soil Moisture: --", size=20, color=ft.Colors.WHITE)
    moisture_percent_txt = ft.Text("Moisture %: --%", size=18, color=ft.Colors.LIGHT_BLUE)
    moisture_bar = ft.ProgressBar(value=0.0, width=300, color=ft.Colors.LIGHT_GREEN)

    rain_txt = ft.Text("Rain Status: --", size=20, color=ft.Colors.CYAN)
    pump_status_txt = ft.Text("Pump Status: --", size=20, color=ft.Colors.YELLOW)

    # === Control Widgets ===
    pump_swi = ft.Switch(label="Water Pump (Manual ON)", value=False)
    angle_sli = ft.Slider(min=0, max=180, divisions=18, label="{value}°", value=90)

    # === Sensor + Status Display Panel ===
    status_card = ft.Card(
        elevation=4,
        content=ft.Container(
            content=ft.Column(
                controls=[
                    moisture_txt,
                    moisture_percent_txt,
                    moisture_bar,
                    rain_txt,
                    pump_status_txt
                ],
                spacing=10
            ),
            padding=20,
            width=350,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            border_radius=10
        )
    )

    # === Manual Control Panel Card ===
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

    # === Title and Dashboard Layout ===
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

    # === Stack Layers UI over Background ===
    page.add(
        ft.Stack(
            controls=[background, dashboard_layout]
        )
    )

    # === Live Sensor Data Polling (every 5 seconds) ===
    def update_sensor_data():
        while True:
            try:
                # Request status from backend
                res = requests.get(f"{BACKEND_URL}/status")
                data = res.json()

                # Extract sensor and control data
                moisture = data.get("moisture", 0)
                moisture_percent = data.get("moisture_percent", 0)
                rain = data.get("rain", 0)
                pump_is_on = data.get("pump_status", 0)
                mode = data.get("mode", "auto")

                # Update moisture display
                moisture_txt.value = f"Soil Moisture: {moisture}/4095"
                moisture_percent_txt.value = f"Moisture %: {moisture_percent}%"
                moisture_bar.value = moisture_percent / 100  # Normalize to 0.0–1.0 for bar

                # Update rain status
                rain_txt.value = f"Rain Status: {'Detected' if rain else 'Clear'}"

                # Update pump status
                if pump_is_on:
                    pump_status_txt.value = f"Pump Status: ON ({'Manual' if mode == 'manual' else 'Auto'})"
                    pump_status_txt.color = ft.Colors.LIGHT_GREEN
                else:
                    pump_status_txt.value = f"Pump Status: OFF"
                    pump_status_txt.color = ft.Colors.RED

                page.update()

            except Exception as e:
                print("Sensor fetch error:", e)

            time.sleep(5)

    # === Send Manual Control Settings to Backend ===
    def send_controls():
        try:
            payload = {
                "pump": 1 if pump_swi.value else 0,
                "angle": angle_sli.value,
                "mode": "manual" if pump_swi.value else "auto"  
            }
            requests.post(f"{BACKEND_URL}/control", json=payload)
        except Exception as e:
            print("Send error:", e)


    # === Start Background Thread for Live Sensor Polling ===
    threading.Thread(target=update_sensor_data, daemon=True).start()

# === Launch the App ===
if __name__ == "__main__":
    ft.app(target=main)