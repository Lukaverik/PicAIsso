from dotenv import dotenv_values

values = dotenv_values()

token = values.get("DISCORD_TOKEN")
base_url = values.get("BASE_URL", "http://127.0.0.1:7860")
base_neg_prompt = "blurry, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, bad eyes"

