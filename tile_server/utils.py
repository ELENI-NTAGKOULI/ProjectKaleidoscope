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
    
def tile_exists(tile_bounds, cog_bounds):
    """
    Returns True if tile_bounds intersects with cog_bounds.
    Both inputs are (left, bottom, right, top).
    """
    t_left, t_bottom, t_right, t_top = tile_bounds
    c_left, c_bottom, c_right, c_top = cog_bounds

    return not (
        t_right < c_left or t_left > c_right or
        t_top < c_bottom or t_bottom > c_top
    )
