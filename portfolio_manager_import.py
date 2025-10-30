"""
EPA Energy Star Portfolio Manager - CSV Property Import Script
This script reads property data from a CSV file and creates properties in Portfolio Manager via API
"""

import requests
import pandas as pd
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth
import sys
import time
from typing import Dict, List, Optional

class PortfolioManagerImporter:
    """
    A class to handle bulk property imports to EPA Energy Star Portfolio Manager
    """

    def __init__(self, username: str, password: str, use_test_environment: bool = True):
        """
        Initialize the importer with credentials

        Args:
            username: Portfolio Manager username
            password: Portfolio Manager password
            use_test_environment: If True, uses test environment. Set to False for production.
        """
        self.username = username
        self.password = password

        # Set base URL based on environment
        if use_test_environment:
            self.base_url = "https://portfoliomanager.energystar.gov/wstest"
        else:
            self.base_url = "https://portfoliomanager.energystar.gov/ws"

        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }

    def get_account_id(self) -> Optional[int]:
        """
        Retrieve the account ID for the authenticated user

        Returns:
            Account ID as integer, or None if request fails
        """
        try:
            url = f"{self.base_url}/account"
            response = requests.get(url, auth=self.auth, headers=self.headers)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                # Parse account ID from response
                account_id = root.find('.//id')
                if account_id is not None:
                    return int(account_id.text)
            else:
                print(f"Error getting account ID: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Exception getting account ID: {str(e)}")
            return None

    def create_property_xml(self, property_data: Dict) -> str:
        """
        Create XML payload for property creation

        Args:
            property_data: Dictionary containing property information

        Returns:
            XML string for API request
        """
        # Create root element
        property_elem = ET.Element('property')

        # Required fields
        name_elem = ET.SubElement(property_elem, 'name')
        name_elem.text = str(property_data.get('name', ''))

        primary_function_elem = ET.SubElement(property_elem, 'primaryFunction')
        primary_function_elem.text = str(property_data.get('primaryFunction', 'Office'))

        # Address
        address_elem = ET.SubElement(property_elem, 'address')
        address_elem.set('address1', str(property_data.get('address1', '')))
        address_elem.set('city', str(property_data.get('city', '')))
        address_elem.set('state', str(property_data.get('state', '')))
        address_elem.set('postalCode', str(property_data.get('postalCode', '')))
        address_elem.set('country', str(property_data.get('country', 'US')))

        # Optional address2
        if property_data.get('address2'):
            address_elem.set('address2', str(property_data['address2']))

        # Year Built
        if property_data.get('yearBuilt'):
            year_built_elem = ET.SubElement(property_elem, 'yearBuilt')
            year_built_elem.text = str(property_data['yearBuilt'])

        # Construction Status
        construction_status_elem = ET.SubElement(property_elem, 'constructionStatus')
        construction_status_elem.text = str(property_data.get('constructionStatus', 'Existing'))

        # Gross Floor Area
        gfa_elem = ET.SubElement(property_elem, 'grossFloorArea')
        gfa_elem.set('temporary', str(property_data.get('gfaTemporary', 'false')).lower())
        gfa_elem.set('units', str(property_data.get('gfaUnits', 'Square Feet')))
        value_elem = ET.SubElement(gfa_elem, 'value')
        value_elem.text = str(property_data.get('grossFloorArea', ''))

        # Occupancy Percentage
        if property_data.get('occupancyPercentage'):
            occupancy_elem = ET.SubElement(property_elem, 'occupancyPercentage')
            occupancy_elem.text = str(property_data['occupancyPercentage'])

        # Federal Property
        is_federal_elem = ET.SubElement(property_elem, 'isFederalProperty')
        is_federal_elem.text = str(property_data.get('isFederalProperty', 'false')).lower()

        # Notes
        if property_data.get('notes'):
            notes_elem = ET.SubElement(property_elem, 'notes')
            notes_elem.text = f"<![CDATA[{property_data['notes']}]]>"

        # For Canadian properties only
        if property_data.get('country', 'US') == 'CA' and property_data.get('isInstitutionalProperty'):
            institutional_elem = ET.SubElement(property_elem, 'isInstitutionalProperty')
            institutional_elem.text = str(property_data['isInstitutionalProperty']).lower()

        # Convert to string with XML declaration
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_string += ET.tostring(property_elem, encoding='unicode')

        return xml_string

    def create_property(self, account_id: int, property_data: Dict) -> Optional[Dict]:
        """
        Create a single property in Portfolio Manager

        Args:
            account_id: The account ID to create the property under
            property_data: Dictionary containing property information

        Returns:
            Dictionary with property_id and status, or None if failed
        """
        try:
            url = f"{self.base_url}/account/{account_id}/property"
            xml_payload = self.create_property_xml(property_data)

            response = requests.post(
                url, 
                data=xml_payload, 
                auth=self.auth, 
                headers=self.headers
            )

            if response.status_code in [200, 201]:
                # Parse response to get property ID
                root = ET.fromstring(response.content)
                property_id_elem = root.find('.//id')

                result = {
                    'status': 'success',
                    'property_name': property_data.get('name'),
                    'property_id': int(property_id_elem.text) if property_id_elem is not None else None,
                    'message': 'Property created successfully'
                }
                return result
            else:
                return {
                    'status': 'error',
                    'property_name': property_data.get('name'),
                    'property_id': None,
                    'message': f"Error {response.status_code}: {response.text}"
                }

        except Exception as e:
            return {
                'status': 'error',
                'property_name': property_data.get('name'),
                'property_id': None,
                'message': f"Exception: {str(e)}"
            }

    def import_from_csv(self, csv_file_path: str, delay_seconds: float = 1.0) -> List[Dict]:
        """
        Import multiple properties from a CSV file

        Args:
            csv_file_path: Path to the CSV file containing property data
            delay_seconds: Delay between API calls to avoid rate limiting

        Returns:
            List of dictionaries with results for each property
        """
        # Read CSV file
        try:
            df = pd.read_csv(csv_file_path)
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            return []

        # Get account ID
        account_id = self.get_account_id()
        if account_id is None:
            print("Failed to retrieve account ID. Check credentials and connection.")
            return []

        print(f"Account ID: {account_id}")
        print(f"Importing {len(df)} properties...")
        print()

        results = []

        # Process each row
        for idx, row in df.iterrows():
            property_data = row.to_dict()

            # Remove NaN values
            property_data = {k: v for k, v in property_data.items() if pd.notna(v)}

            print(f"Creating property {idx + 1}/{len(df)}: {property_data.get('name', 'Unknown')}")

            result = self.create_property(account_id, property_data)
            results.append(result)

            if result['status'] == 'success':
                print(f"  ✓ Success - Property ID: {result['property_id']}")
            else:
                print(f"  ✗ Failed - {result['message']}")

            # Add delay to avoid rate limiting
            if idx < len(df) - 1:
                time.sleep(delay_seconds)

            print()

        return results

    def export_results(self, results: List[Dict], output_file: str = 'import_results.csv'):
        """
        Export import results to a CSV file

        Args:
            results: List of result dictionaries
            output_file: Path to output CSV file
        """
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"Results exported to {output_file}")


def create_sample_csv(filename: str = 'sample_properties.csv'):
    """
    Create a sample CSV file with property data template
    """
    sample_data = {
        'name': ['Main Office Building', 'Warehouse Facility', 'Retail Store Downtown'],
        'primaryFunction': ['Office', 'Non-Refrigerated Warehouse', 'Retail Store'],
        'address1': ['123 Main Street', '456 Industrial Ave', '789 Commerce Blvd'],
        'address2': ['Suite 100', '', 'Unit 5'],
        'city': ['Washington', 'Baltimore', 'Arlington'],
        'state': ['DC', 'MD', 'VA'],
        'postalCode': ['20001', '21201', '22201'],
        'country': ['US', 'US', 'US'],
        'yearBuilt': [2005, 1998, 2010],
        'constructionStatus': ['Existing', 'Existing', 'Existing'],
        'grossFloorArea': [50000, 100000, 15000],
        'gfaUnits': ['Square Feet', 'Square Feet', 'Square Feet'],
        'gfaTemporary': ['false', 'false', 'false'],
        'occupancyPercentage': [85, 90, 95],
        'isFederalProperty': ['false', 'false', 'false'],
        'notes': ['Headquarters building', 'Distribution center', 'Flagship store']
    }

    df = pd.DataFrame(sample_data)
    df.to_csv(filename, index=False)
    print(f"Sample CSV created: {filename}")
    return filename


# Example usage
if __name__ == "__main__":
    print("EPA Energy Star Portfolio Manager - Property Import Tool")
    print("=" * 60)
    print()

    # Configuration
    USERNAME = "your_username_here"  # Replace with your Portfolio Manager username
    PASSWORD = "your_password_here"  # Replace with your Portfolio Manager password
    USE_TEST_ENV = True  # Set to False for production environment

    # Create sample CSV if needed
    print("Creating sample CSV file...")
    sample_file = create_sample_csv('sample_properties.csv')
    print()

    # Initialize importer
    print("Initializing importer...")
    importer = PortfolioManagerImporter(
        username=USERNAME,
        password=PASSWORD,
        use_test_environment=USE_TEST_ENV
    )
    print()

    # Import properties from CSV
    # Uncomment the following lines to run the actual import:
    # results = importer.import_from_csv('sample_properties.csv', delay_seconds=1.0)
    # importer.export_results(results, 'import_results.csv')

    print("Setup complete!")
    print()
    print("NEXT STEPS:")
    print("1. Update USERNAME and PASSWORD with your Portfolio Manager credentials")
    print("2. Prepare your CSV file with property data (or use sample_properties.csv as template)")
    print("3. Set USE_TEST_ENV = True for testing, False for production")
    print("4. Uncomment the import lines and run the script")
    print()
    print("CSV FILE FORMAT:")
    print("Required columns: name, primaryFunction, address1, city, state, postalCode,")
    print("                  country, grossFloorArea, constructionStatus")
    print()
    print("Optional columns: address2, yearBuilt, occupancyPercentage, gfaUnits,")
    print("                  gfaTemporary, isFederalProperty, notes")
