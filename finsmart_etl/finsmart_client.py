"""
HTTP client for Finsmart-style API.

Handles authentication and data retrieval from the external financial data source.
"""

import requests
from typing import Optional


class FinsmartClientError(Exception):
    """Custom exception for Finsmart API errors."""
    pass


class FinsmartClient:
    """
    HTTP client for Finsmart API.
    
    Usage:
        client = FinsmartClient(base_url, api_key, password)
        token = client.login()
        data = client.analyze_data(token, company_guid)
    """
    
    def __init__(self, base_url: str, api_key: str, password: str, timeout: int = 60):
        """
        Initialize the Finsmart client.
        
        Args:
            base_url: API base URL (e.g., "https://dev-datauploadapi.finsmart.ai")
            api_key: API key for authentication
            password: Password for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.password = password
        self.timeout = timeout
        self._token: Optional[str] = None
    
    def login(self) -> str:
        """
        Authenticate with the API and get a bearer token.
        
        POST /login with {apiKey, password}
        
        Returns:
            str: Bearer token for subsequent requests.
        
        Raises:
            FinsmartClientError: If authentication fails.
        """
        url = f"{self.base_url}/login"
        payload = {
            "apiKey": self.api_key,
            "password": self.password
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            # Handle different response structures
            token = data.get("token") or data.get("access_token")
            if not token:
                # Maybe the whole response is the token
                if isinstance(data, str):
                    token = data
                else:
                    raise FinsmartClientError(f"No token in response: {data}")
            
            self._token = token
            return token
            
        except requests.exceptions.RequestException as e:
            raise FinsmartClientError(f"Login failed: {e}") from e
    
    def analyze_data(self, token: str, company_guid: str) -> dict:
        """
        Fetch financial data for a company.
        
        POST /ai-insight/analyze-data with Bearer token and CompanyGuid.
        
        Args:
            token: Bearer token from login()
            company_guid: Company GUID to fetch data for
        
        Returns:
            dict: Parsed JSON response containing financial data.
        
        Raises:
            FinsmartClientError: If the request fails.
        """
        url = f"{self.base_url}/ai-insight/analyze-data"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"CompanyGuid": company_guid}
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise FinsmartClientError(f"analyze_data failed: {e}") from e
    
    def fetch_company_data(self, company_guid: str) -> dict:
        """
        Convenience method: login + analyze_data in one call.
        
        Args:
            company_guid: Company GUID to fetch data for
        
        Returns:
            dict: Parsed JSON response containing financial data.
        """
        token = self.login()
        return self.analyze_data(token, company_guid)


# Factory function for dependency injection
def create_finsmart_client(
    base_url: str,
    api_key: str,
    password: str
) -> FinsmartClient:
    """
    Create a FinsmartClient instance.
    
    This factory function makes it easy to mock the client in tests.
    
    Args:
        base_url: API base URL
        api_key: API key
        password: Password
    
    Returns:
        FinsmartClient instance
    """
    return FinsmartClient(base_url, api_key, password)
