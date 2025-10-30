"""
Portfolio Manager Utilities
Additional helper functions for working with Portfolio Manager API
"""

import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import pandas as pd
from typing import Dict, List, Optional


class PortfolioManagerUtils:
    """
    Utility functions for Portfolio Manager operations
    """

    def __init__(self, username: str, password: str, use_test_environment: bool = True):
        self.username = username
        self.password = password

        if use_test_environment:
            self.base_url = "https://portfoliomanager.energystar.gov/wstest"
        else:
            self.base_url = "https://portfoliomanager.energystar.gov/ws"

        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }

    def test_connection(self) -> bool:
        """
        Test connection to Portfolio Manager API

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/account"
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=10)

            if response.status_code == 200:
                print("✓ Connection successful!")
                print(f"  Environment: {'TEST' if 'wstest' in self.base_url else 'PRODUCTION'}")
                return True
            else:
                print(f"✗ Connection failed with status code: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Connection error: {str(e)}")
            return False

    def get_account_info(self) -> Optional[Dict]:
        """
        Get detailed account information

        Returns:
            Dictionary with account details or None if failed
        """
        try:
            url = f"{self.base_url}/account"
            response = requests.get(url, auth=self.auth, headers=self.headers)

            if response.status_code == 200:
                root = ET.fromstring(response.content)

                # Parse account information
                account_info = {
                    'id': root.find('.//id').text if root.find('.//id') is not None else None,
                    'username': root.find('.//username').text if root.find('.//username') is not None else None,
                    'webserviceUser': root.find('.//webserviceUser').text if root.find('.//webserviceUser') is not None else None,
                }

                # Parse contact info if available
                contact = root.find('.//contact')
                if contact is not None:
                    account_info['firstName'] = contact.find('firstName').text if contact.find('firstName') is not None else None
                    account_info['lastName'] = contact.find('lastName').text if contact.find('lastName') is not None else None
                    account_info['email'] = contact.find('email').text if contact.find('email') is not None else None

                return account_info
            else:
                print(f"Error getting account info: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception getting account info: {str(e)}")
            return None

    def list_properties(self, account_id: Optional[int] = None) -> Optional[List[Dict]]:
        """
        List all properties for an account

        Args:
            account_id: Account ID (will be auto-retrieved if not provided)

        Returns:
            List of property dictionaries or None if failed
        """
        try:
            if account_id is None:
                account_info = self.get_account_info()
                if account_info:
                    account_id = int(account_info['id'])
                else:
                    return None

            url = f"{self.base_url}/account/{account_id}/property/list"
            response = requests.get(url, auth=self.auth, headers=self.headers)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                properties = []

                for link in root.findall('.//link'):
                    prop_dict = {
                        'property_id': link.get('id'),
                        'name': link.get('name'),
                        'link': link.get('link')
                    }
                    properties.append(prop_dict)

                return properties
            else:
                print(f"Error listing properties: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception listing properties: {str(e)}")
            return None

    def get_property_details(self, property_id: int) -> Optional[Dict]:
        """
        Get detailed information for a specific property

        Args:
            property_id: Property ID

        Returns:
            Dictionary with property details or None if failed
        """
        try:
            url = f"{self.base_url}/property/{property_id}"
            response = requests.get(url, auth=self.auth, headers=self.headers)

            if response.status_code == 200:
                root = ET.fromstring(response.content)

                property_info = {
                    'name': root.find('.//name').text if root.find('.//name') is not None else None,
                    'primaryFunction': root.find('.//primaryFunction').text if root.find('.//primaryFunction') is not None else None,
                    'constructionStatus': root.find('.//constructionStatus').text if root.find('.//constructionStatus') is not None else None,
                    'yearBuilt': root.find('.//yearBuilt').text if root.find('.//yearBuilt') is not None else None,
                }

                # Parse address
                address = root.find('.//address')
                if address is not None:
                    property_info['address1'] = address.get('address1')
                    property_info['city'] = address.get('city')
                    property_info['state'] = address.get('state')
                    property_info['postalCode'] = address.get('postalCode')
                    property_info['country'] = address.get('country')

                # Parse gross floor area
                gfa = root.find('.//grossFloorArea')
                if gfa is not None:
                    gfa_value = gfa.find('value')
                    if gfa_value is not None:
                        property_info['grossFloorArea'] = gfa_value.text
                        property_info['gfaUnits'] = gfa.get('units')

                return property_info
            else:
                print(f"Error getting property details: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception getting property details: {str(e)}")
            return None

    def export_properties_to_csv(self, output_file: str = 'existing_properties.csv') -> bool:
        """
        Export all properties to a CSV file

        Args:
            output_file: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get list of properties
            properties = self.list_properties()
            if not properties:
                print("No properties found or error retrieving properties")
                return False

            print(f"Found {len(properties)} properties. Fetching details...")

            # Get details for each property
            detailed_properties = []
            for idx, prop in enumerate(properties):
                print(f"  Fetching property {idx + 1}/{len(properties)}: {prop['name']}")
                details = self.get_property_details(int(prop['property_id']))
                if details:
                    details['property_id'] = prop['property_id']
                    detailed_properties.append(details)

            # Export to CSV
            df = pd.DataFrame(detailed_properties)
            df.to_csv(output_file, index=False)
            print(f"\n✓ Exported {len(detailed_properties)} properties to {output_file}")
            return True

        except Exception as e:
            print(f"Exception exporting properties: {str(e)}")
            return False

    def validate_csv(self, csv_file: str) -> Dict:
        """
        Validate a CSV file before import

        Args:
            csv_file: Path to CSV file

        Returns:
            Dictionary with validation results
        """
        required_fields = ['name', 'primaryFunction', 'address1', 'city', 'state', 
                          'postalCode', 'country', 'grossFloorArea', 'constructionStatus']

        try:
            df = pd.read_csv(csv_file)

            validation_results = {
                'valid': True,
                'total_rows': len(df),
                'errors': [],
                'warnings': []
            }

            # Check for required columns
            missing_columns = [col for col in required_fields if col not in df.columns]
            if missing_columns:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")

            # Check for empty required fields
            for col in required_fields:
                if col in df.columns:
                    empty_count = df[col].isna().sum()
                    if empty_count > 0:
                        validation_results['valid'] = False
                        validation_results['errors'].append(f"Column '{col}' has {empty_count} empty values")

            # Check property types
            valid_property_types = [
                'Office', 'Bank Branch', 'Financial Office', 'K-12 School', 'College/University',
                'Hospital (General Medical & Surgical)', 'Medical Office', 'Hotel', 'Restaurant',
                'Non-Refrigerated Warehouse', 'Distribution Center', 'Data Center', 'Retail Store',
                'Other'
            ]

            if 'primaryFunction' in df.columns:
                invalid_types = df[~df['primaryFunction'].isin(valid_property_types)]['primaryFunction'].unique()
                if len(invalid_types) > 0:
                    validation_results['warnings'].append(f"Unknown property types (may be valid): {', '.join(str(x) for x in invalid_types)}")

            # Check construction status
            valid_statuses = ['Existing', 'Project', 'Design', 'Construction', 'Test']
            if 'constructionStatus' in df.columns:
                invalid_statuses = df[~df['constructionStatus'].isin(valid_statuses)]['constructionStatus'].unique()
                if len(invalid_statuses) > 0:
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Invalid construction status values: {', '.join(str(x) for x in invalid_statuses)}")

            # Print results
            print("\n" + "=" * 60)
            print("CSV VALIDATION RESULTS")
            print("=" * 60)
            print(f"File: {csv_file}")
            print(f"Total rows: {validation_results['total_rows']}")
            print(f"Status: {'VALID ✓' if validation_results['valid'] else 'INVALID ✗'}")
            print()

            if validation_results['errors']:
                print("ERRORS:")
                for error in validation_results['errors']:
                    print(f"  ✗ {error}")
                print()

            if validation_results['warnings']:
                print("WARNINGS:")
                for warning in validation_results['warnings']:
                    print(f"  ⚠ {warning}")
                print()

            if validation_results['valid'] and not validation_results['warnings']:
                print("✓ CSV file is valid and ready for import!")

            print("=" * 60)

            return validation_results

        except Exception as e:
            return {
                'valid': False,
                'total_rows': 0,
                'errors': [f"Error reading CSV: {str(e)}"],
                'warnings': []
            }


# Example usage and command-line interface
if __name__ == "__main__":
    import sys

    print("Portfolio Manager Utilities")
    print("=" * 60)
    print()

    # Configuration
    USERNAME = "your_username_here"
    PASSWORD = "your_password_here"
    USE_TEST_ENV = True

    utils = PortfolioManagerUtils(USERNAME, PASSWORD, USE_TEST_ENV)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test":
            print("Testing connection...")
            utils.test_connection()

        elif command == "info":
            print("Getting account information...")
            info = utils.get_account_info()
            if info:
                print("\nAccount Information:")
                for key, value in info.items():
                    print(f"  {key}: {value}")

        elif command == "list":
            print("Listing properties...")
            properties = utils.list_properties()
            if properties:
                print(f"\nFound {len(properties)} properties:")
                for prop in properties:
                    print(f"  ID: {prop['property_id']} - {prop['name']}")

        elif command == "export":
            output_file = sys.argv[2] if len(sys.argv) > 2 else 'existing_properties.csv'
            print(f"Exporting properties to {output_file}...")
            utils.export_properties_to_csv(output_file)

        elif command == "validate":
            if len(sys.argv) < 3:
                print("Error: Please provide CSV file path")
                print("Usage: python pm_utilities.py validate <csv_file>")
            else:
                csv_file = sys.argv[2]
                utils.validate_csv(csv_file)
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  test      - Test API connection")
            print("  info      - Get account information")
            print("  list      - List all properties")
            print("  export    - Export properties to CSV")
            print("  validate  - Validate a CSV file")
    else:
        print("Usage: python pm_utilities.py <command>")
        print("\nAvailable commands:")
        print("  test      - Test API connection")
        print("  info      - Get account information")
        print("  list      - List all properties")
        print("  export    - Export properties to CSV")
        print("  validate  - Validate a CSV file")
        print()
        print("Example: python pm_utilities.py test")
