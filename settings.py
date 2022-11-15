from dotenv import dotenv_values

values = dotenv_values()

token = values.get("DISCORD_TOKEN")
base_url = values.get("BASE_URL", "http://127.0.0.1:7860")


