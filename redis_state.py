import redis
import json
import os

class RedisState:
    def __init__(self, session_id="hackathon_demo", host='localhost', port=6379):
        # Connect to Redis
        try:
            self.r = redis.Redis(host=host, port=port, decode_responses=True)
            self.r.ping() # Check connection
            print(f"Connected to Redis Brain! (Session: {session_id})")
        except redis.ConnectionError as e:
            print(f"Redis not found! Falling back to local memory (Logic will be brittle). {e}")
            self.r = None
            self.local_store = {}

        self.session_id = session_id

    def _get_key(self, key):
        return f"droidrun:{self.session_id}:{key}"

    def set(self, key, value):
        """Saves data. Handles Dicts/Lists automatically."""
        full_key = self._get_key(key)
        
        # Serialize complex objects to JSON
        if isinstance(value, (dict, list)):
            payload = json.dumps(value)
        else:
            payload = str(value)
            
        if self.r:
            self.r.set(full_key, payload)
        else:
            self.local_store[key] = payload

    def get(self, key, default=None):
        """Retrieves data. Auto-decodes JSON."""
        full_key = self._get_key(key)
        
        if self.r:
            val = self.r.get(full_key)
        else:
            val = self.local_store.get(key)
            
        if val is None:
            return default
            
        # Try to parse JSON, otherwise return raw string
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            # It's a simple string/float
            try:
                # Try converting to float/int if possible
                if '.' in val: return float(val)
                return int(val)
            except ValueError:
                return val

    def clear(self):
        """Wipes memory for this session"""
        if self.r:
            keys = self.r.keys(f"droidrun:{self.session_id}:*")
            if keys:
                self.r.delete(*keys)
        else:
            self.local_store.clear()

# Create a singleton instance for your app
# You can import 'global_state' in any file now
global_state = RedisState()