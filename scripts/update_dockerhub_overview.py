#!/usr/bin/env python3
"""
Update Docker Hub repository overview from README.md

Usage:
    export DOCKERHUB_USERNAME="your-username"
    export DOCKERHUB_TOKEN="your-token"
    python3 update_dockerhub_overview.py [README_PATH]

Get your Docker Hub token from: https://hub.docker.com/settings/security
"""

import os
import sys
import json
import requests
from pathlib import Path


def main():
    # Configuration
    repo_namespace = "miget"
    repo_name = "container-os"
    readme_path = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    
    # Check environment variables
    username = os.environ.get("DOCKERHUB_USERNAME")
    token = os.environ.get("DOCKERHUB_TOKEN")
    
    if not username:
        print("Error: DOCKERHUB_USERNAME environment variable is required")
        sys.exit(1)
    
    if not token:
        print("Error: DOCKERHUB_TOKEN environment variable is required")
        print("Get your token from: https://hub.docker.com/settings/security")
        sys.exit(1)
    
    # Read README
    readme_file = Path(readme_path)
    if not readme_file.exists():
        print(f"Error: README file not found at {readme_path}")
        sys.exit(1)
    
    print(f"Reading README from: {readme_path}")
    readme_content = readme_file.read_text()
    
    # Authenticate
    print("Authenticating with Docker Hub...")
    auth_url = "https://hub.docker.com/v2/users/login/"
    auth_data = {
        "username": username,
        "password": token
    }
    
    try:
        # Docker Hub blocks default python-requests User-Agent with 500 error
        auth_headers = {"User-Agent": "container-os/1.0"}
        auth_response = requests.post(auth_url, json=auth_data, headers=auth_headers)
        auth_response.raise_for_status()
        jwt_token = auth_response.json().get("token")
        
        if not jwt_token:
            print("Error: Failed to get JWT token from Docker Hub")
            sys.exit(1)
        
        print("Successfully authenticated")
    except requests.exceptions.RequestException as e:
        print(f"Error: Authentication failed - {e}")
        sys.exit(1)
    
    # First, verify we can access the repository
    print(f"Verifying access to {repo_namespace}/{repo_name}...")
    verify_url = f"https://hub.docker.com/v2/repositories/{repo_namespace}/{repo_name}/"
    headers = {
        "Authorization": f"JWT {jwt_token}",
        "Content-Type": "application/json"
    }
    
    try:
        verify_response = requests.get(verify_url, headers=headers)
        verify_response.raise_for_status()
        repo_info = verify_response.json()
        print(f"✓ Repository found: {repo_info.get('name', 'unknown')}")
        
        # Check if user has write permissions
        if repo_info.get('can_edit', False):
            print("✓ User has edit permissions")
        else:
            print("⚠ Warning: User may not have edit permissions")
            print(f"  Authenticated as: {username}")
            print(f"  Repository namespace: {repo_namespace}")
            if username != repo_namespace:
                print(f"  Note: Username '{username}' differs from namespace '{repo_namespace}'")
                print(f"  You may need organization permissions or to use a token with write access")
    except requests.exceptions.RequestException as e:
        print(f"Error: Cannot access repository - {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)
    
    # Update repository description
    print(f"Updating Docker Hub overview for {repo_namespace}/{repo_name}...")
    update_url = f"https://hub.docker.com/v2/repositories/{repo_namespace}/{repo_name}/"
    update_data = {
        "full_description": readme_content
    }
    
    try:
        update_response = requests.patch(update_url, headers=headers, json=update_data)
        update_response.raise_for_status()
        
        response_data = update_response.json()
        if "full_description" in response_data:
            print("✓ Successfully updated Docker Hub overview")
            print(f"View at: https://hub.docker.com/r/{repo_namespace}/{repo_name}")
        else:
            print("Warning: Update may have succeeded but response format unexpected")
            print(f"Response: {json.dumps(response_data, indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to update Docker Hub overview - {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
            print("\nTroubleshooting:")
            print("1. Ensure your Docker Hub token has 'Read, Write, Delete' permissions")
            print("2. If this is an organization repo, you need organization admin access")
            print("3. Generate a new token at: https://hub.docker.com/settings/security")
        sys.exit(1)


if __name__ == "__main__":
    main()
