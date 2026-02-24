from pathlib import Path

app_name = "oura-streaming"
app_entrypoint = "oura_streaming.main:app"
app_slug = "oura_streaming"
api_prefix = "/api"
dist_dir = Path(__file__).parent / "__dist__"