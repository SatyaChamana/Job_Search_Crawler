from supabase import create_client, Client

from backend.config import settings

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
