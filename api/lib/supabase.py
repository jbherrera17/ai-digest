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


# ============================================
# Skills Registry Operations
# ============================================

def get_all_skills(filters=None):
    """Get all skills from registry, optionally filtered."""
    client = get_public_client()
    query = client.table('skill_registry').select('*').order('department').order('name')

    if filters:
        if filters.get('department'):
            query = query.eq('department', filters['department'])
        if filters.get('type') == 'core':
            query = query.eq('is_core_skill', True)
        elif filters.get('type') == 'expert':
            query = query.eq('is_expert_skill', True)
        if filters.get('source'):
            query = query.eq('source_id', filters['source'])
        if filters.get('search'):
            term = filters['search']
            query = query.or_(f"name.ilike.%{term}%,description.ilike.%{term}%,slug.ilike.%{term}%")

    response = query.execute()
    return response.data


def get_skill_sources():
    """Get all skill sources."""
    client = get_public_client()
    response = client.table('skill_sources').select('*').order('name').execute()
    return response.data


def get_skill_matches(status=None):
    """Get skill matches, optionally filtered by review status."""
    client = get_public_client()
    query = client.table('skill_matches').select('*, expert:expert_skill_id(*)').order('confidence', desc=True)

    if status:
        query = query.eq('review_status', status)

    response = query.execute()
    return response.data


def get_unmatched_expert_skills():
    """Get expert skills that have no approved match (new skill suggestions)."""
    client = get_public_client()
    all_expert = client.table('skill_registry').select('*').eq('is_expert_skill', True).order('name').execute()
    adopted = client.table('skill_adoptions').select('expert_skill_id').execute()
    adopted_ids = {a['expert_skill_id'] for a in adopted.data}
    matched = client.table('skill_matches').select('expert_skill_id').eq('review_status', 'approved').execute()
    matched_ids = {m['expert_skill_id'] for m in matched.data}

    excluded = adopted_ids | matched_ids
    return [s for s in all_expert.data if s['id'] not in excluded]


def get_skill_stats():
    """Get dashboard stats for skills registry."""
    client = get_public_client()

    skills = client.table('skill_registry').select('is_core_skill,is_expert_skill', count='exact').execute()
    core = sum(1 for s in skills.data if s['is_core_skill'])
    expert = sum(1 for s in skills.data if s['is_expert_skill'])

    matches = client.table('skill_matches').select('review_status', count='exact').execute()
    pending = sum(1 for m in matches.data if m['review_status'] == 'pending')
    approved = sum(1 for m in matches.data if m['review_status'] == 'approved')
    rejected = sum(1 for m in matches.data if m['review_status'] == 'rejected')

    adoptions = client.table('skill_adoptions').select('id', count='exact').execute()

    return {
        'total_skills': skills.count or len(skills.data),
        'core_skills': core,
        'expert_skills': expert,
        'total_matches': matches.count or len(matches.data),
        'pending_reviews': pending,
        'approved': approved,
        'rejected': rejected,
        'adoptions': len(adoptions.data),
    }


def upsert_skill_sources(sources):
    """Upsert skill sources from registry sync."""
    client = get_admin_client()
    rows = []
    for s in sources:
        rows.append({
            'source_key': s['id'],
            'name': s['name'],
            'type': s['type'],
            'author_name': s.get('author', {}).get('name'),
            'author_email': s.get('author', {}).get('email'),
            'author_url': s.get('author', {}).get('url'),
            'license': s.get('license'),
            'repo_url': s.get('repoUrl'),
            'department': s.get('department'),
            'last_scanned_at': s.get('lastScannedAt'),
        })
    response = client.table('skill_sources').upsert(rows, on_conflict='source_key').execute()
    return len(response.data)


def upsert_skills(skills, source_map):
    """Upsert skills from registry sync. source_map: {source_key: source_uuid}."""
    client = get_admin_client()
    rows = []
    for s in skills:
        rows.append({
            'skill_id': s['id'],
            'slug': s['slug'],
            'name': s['name'],
            'description': s.get('description', ''),
            'department': s.get('department'),
            'category': s.get('category'),
            'source_id': source_map.get(s['sourceId']),
            'author_name': s.get('author', {}).get('name'),
            'license': s.get('license'),
            'original_path': s.get('originalPath'),
            'current_version': s.get('currentVersion', '1.0.0'),
            'versions': s.get('versions', []),
            'content_hash': s.get('versions', [{}])[-1].get('contentHash') if s.get('versions') else None,
            'is_expert_skill': s.get('isExpertSkill', False),
            'is_core_skill': s.get('isCoreSkill', False),
            'has_command': s.get('hasCommand', False),
            'keywords': s.get('keywords', []),
            'discovered_at': s.get('discoveredAt'),
            'last_checked_at': s.get('lastCheckedAt'),
        })
    synced = 0
    for i in range(0, len(rows), 50):
        batch = rows[i:i+50]
        response = client.table('skill_registry').upsert(batch, on_conflict='skill_id').execute()
        synced += len(response.data)
    return synced


def upsert_skill_matches(match_results, skill_id_map):
    """Upsert match results. skill_id_map: {skill_id_text: uuid}. Preserves reviewed matches."""
    client = get_admin_client()

    existing = client.table('skill_matches').select('expert_skill_id,core_skill_slug,review_status').neq('review_status', 'pending').execute()
    reviewed_pairs = {(r['expert_skill_id'], r['core_skill_slug']) for r in existing.data}

    rows = []
    for m in match_results:
        expert_uuid = skill_id_map.get(m['expertSkillId'])
        if not expert_uuid:
            continue
        core_slug = m.get('coreSkillSlug')
        if not core_slug:
            continue
        if (expert_uuid, core_slug) in reviewed_pairs:
            continue

        rows.append({
            'expert_skill_id': expert_uuid,
            'core_skill_slug': core_slug,
            'match_type': m.get('matchType'),
            'confidence': m.get('confidence', 0),
            'reasoning': m.get('reasoning', ''),
            'review_status': 'pending',
        })

    if not rows:
        return 0

    response = client.table('skill_matches').upsert(
        rows, on_conflict='expert_skill_id,core_skill_slug'
    ).execute()
    return len(response.data)


def update_match_review(match_id, data):
    """Update a match review status."""
    client = get_admin_client()
    update_data = {
        'review_status': data['review_status'],
        'reviewer_notes': data.get('reviewer_notes', ''),
        'reviewed_by': data.get('reviewed_by', 'admin'),
    }
    response = client.table('skill_matches').update(update_data).eq('id', match_id).execute()
    return response.data[0] if response.data else None


def create_skill_adoption(data):
    """Create a skill adoption record."""
    client = get_admin_client()
    response = client.table('skill_adoptions').insert({
        'expert_skill_id': data['expert_skill_id'],
        'adopted_version': data.get('adopted_version'),
        'notes': data.get('notes', ''),
    }).execute()
    return response.data[0] if response.data else None
