from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the Supabase client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
