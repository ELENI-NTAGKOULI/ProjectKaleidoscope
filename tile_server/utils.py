import os
from supabase import create_client


def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Missing Supabase credentials")
    return create_client(url, key)

def get_latest_coordinates():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    table = os.environ.get("SUPABASE_TABLE", "projects")

    if not url or not key:
        raise ValueError("Missing Supabase credentials")

    client = create_client(url, key)
    response = client.table(table).select("lat, lng").order("created_at", desc=True).limit(1).execute()

    if response.data and len(response.data) > 0:
        coords = response.data[0]
        return float(coords['lng']), float(coords['lat'])
    else:
        raise ValueError("No coordinates found in Supabase table")
