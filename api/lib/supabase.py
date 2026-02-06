"""Supabase client initialization for AIDigest."""

import os
from supabase import create_client, Client

# Initialize Supabase client
# Set these in Vercel environment variables or .env file
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')


def get_supabase_client(use_service_key=False) -> Client:
    """
    Get Supabase client.

    Args:
        use_service_key: If True, use service key for admin operations (bypasses RLS).
                        If False, use anon key (respects RLS policies).
    """
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable not set")

    key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_ANON_KEY
    if not key:
        key_type = "SUPABASE_SERVICE_KEY" if use_service_key else "SUPABASE_ANON_KEY"
        raise ValueError(f"{key_type} environment variable not set")

    return create_client(SUPABASE_URL, key)


def get_admin_client() -> Client:
    """Get Supabase client with service key for admin operations."""
    return get_supabase_client(use_service_key=True)


def get_public_client() -> Client:
    """Get Supabase client with anon key for public operations."""
    return get_supabase_client(use_service_key=False)


# ============================================
# Feed Operations
# ============================================

def get_active_feeds():
    """Get all active feeds from database."""
    client = get_public_client()
    response = client.table('feeds').select('*').eq('is_active', True).execute()
    return response.data


def get_all_feeds():
    """Get all feeds (including inactive) for admin."""
    client = get_admin_client()
    response = client.table('feeds').select('*').order('category', desc=False).order('name', desc=False).execute()
    return response.data


def get_feed_by_id(feed_id: str):
    """Get a single feed by ID."""
    client = get_admin_client()
    response = client.table('feeds').select('*').eq('id', feed_id).single().execute()
    return response.data


def create_feed(feed_data: dict):
    """Create a new feed."""
    client = get_admin_client()
    response = client.table('feeds').insert(feed_data).execute()
    return response.data[0] if response.data else None


def update_feed(feed_id: str, feed_data: dict):
    """Update an existing feed."""
    client = get_admin_client()
    response = client.table('feeds').update(feed_data).eq('id', feed_id).execute()
    return response.data[0] if response.data else None


def delete_feed(feed_id: str):
    """Delete a feed."""
    client = get_admin_client()
    response = client.table('feeds').delete().eq('id', feed_id).execute()
    return response.data


def toggle_feed_active(feed_id: str, is_active: bool):
    """Toggle feed active status."""
    return update_feed(feed_id, {'is_active': is_active})


# ============================================
# Category Operations
# ============================================

def get_all_categories():
    """Get all categories."""
    client = get_public_client()
    response = client.table('categories').select('*').order('display_order', desc=False).execute()
    return response.data


def create_category(category_data: dict):
    """Create a new category."""
    client = get_admin_client()
    response = client.table('categories').insert(category_data).execute()
    return response.data[0] if response.data else None


def update_category(category_id: str, category_data: dict):
    """Update a category."""
    client = get_admin_client()
    response = client.table('categories').update(category_data).eq('id', category_id).execute()
    return response.data[0] if response.data else None


def delete_category(category_id: str):
    """Delete a category."""
    client = get_admin_client()
    response = client.table('categories').delete().eq('id', category_id).execute()
    return response.data


# ============================================
# ICP Profile Operations
# ============================================

def get_active_icp_profiles():
    """Get all active ICP profiles."""
    client = get_public_client()
    response = client.table('icp_profiles').select('*').eq('is_active', True).execute()
    return response.data


def get_all_icp_profiles():
    """Get all ICP profiles for admin."""
    client = get_admin_client()
    response = client.table('icp_profiles').select('*').order('name', desc=False).execute()
    return response.data


def get_default_icp_profile():
    """Get the default ICP profile."""
    client = get_public_client()
    response = client.table('icp_profiles').select('*').eq('is_default', True).single().execute()
    return response.data


def get_icp_profile_by_id(profile_id: str):
    """Get a single ICP profile by ID."""
    client = get_admin_client()
    response = client.table('icp_profiles').select('*').eq('id', profile_id).single().execute()
    return response.data


def create_icp_profile(profile_data: dict):
    """Create a new ICP profile."""
    client = get_admin_client()
    # If setting as default, unset other defaults first
    if profile_data.get('is_default'):
        client.table('icp_profiles').update({'is_default': False}).eq('is_default', True).execute()
    response = client.table('icp_profiles').insert(profile_data).execute()
    return response.data[0] if response.data else None


def update_icp_profile(profile_id: str, profile_data: dict):
    """Update an ICP profile."""
    client = get_admin_client()
    # If setting as default, unset other defaults first
    if profile_data.get('is_default'):
        client.table('icp_profiles').update({'is_default': False}).neq('id', profile_id).eq('is_default', True).execute()
    response = client.table('icp_profiles').update(profile_data).eq('id', profile_id).execute()
    return response.data[0] if response.data else None


def delete_icp_profile(profile_id: str):
    """Delete an ICP profile."""
    client = get_admin_client()
    response = client.table('icp_profiles').delete().eq('id', profile_id).execute()
    return response.data


def set_default_icp_profile(profile_id: str):
    """Set an ICP profile as the default."""
    client = get_admin_client()
    # Unset all defaults
    client.table('icp_profiles').update({'is_default': False}).eq('is_default', True).execute()
    # Set new default
    response = client.table('icp_profiles').update({'is_default': True}).eq('id', profile_id).execute()
    return response.data[0] if response.data else None


# ============================================
# Feed Suggestions (Discovery)
# ============================================

def get_feed_suggestions(tags: list = None, limit: int = 20):
    """Get feed suggestions, optionally filtered by tags."""
    client = get_public_client()
    query = client.table('feed_suggestions').select('*').order('popularity_score', desc=True).limit(limit)

    if tags:
        # Filter by any matching tag
        query = query.contains('relevance_tags', tags)

    response = query.execute()
    return response.data


def search_feed_suggestions(search_term: str, limit: int = 20):
    """Search feed suggestions by name or description."""
    client = get_public_client()
    response = client.table('feed_suggestions').select('*').or_(
        f"name.ilike.%{search_term}%,description.ilike.%{search_term}%"
    ).order('popularity_score', desc=True).limit(limit).execute()
    return response.data


# ============================================
# Admin Settings
# ============================================

def get_setting(key: str):
    """Get a setting value."""
    client = get_public_client()
    response = client.table('admin_settings').select('value').eq('key', key).single().execute()
    return response.data['value'] if response.data else None


def update_setting(key: str, value):
    """Update a setting value."""
    client = get_admin_client()
    response = client.table('admin_settings').upsert({
        'key': key,
        'value': value
    }).execute()
    return response.data[0] if response.data else None


def get_all_settings():
    """Get all settings as a dict."""
    client = get_public_client()
    response = client.table('admin_settings').select('*').execute()
    return {item['key']: item['value'] for item in response.data}
