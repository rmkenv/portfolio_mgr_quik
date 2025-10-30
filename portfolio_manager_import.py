import requests
import pandas as pd
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth
import time
from typing import Dict, List, Optional

class PortfolioManagerImporter:
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

    def get_account_id(self) -> Optional[int]:
        # Returns provider account ID
        try:
            url = f"{self.base_url}/account"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                account_id = root.find('.//id')
                if account_id is not None:
                    return int(account_id.text)
            print(f"Error getting provider account ID: {response.status_code} {response.text}")
            return None
        except Exception as e:
            print(f"Exception getting provider account ID: {str(e)}")
            return None

    def create_customer_account(self, customer_data: Dict) -> Optional[int]:
        try:
            url = f"{self.base_url}/customer"
            xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<account>
    <username>{customer_data['username']}</username>
    <password>{customer_data['password']}</password>
    <webserviceUser>true</webserviceUser>
    <searchable>false</searchable>
    <contact>
        <firstName>{customer_data.get('firstName', '')}</firstName>
        <lastName>{customer_data.get('lastName', '')}</lastName>
        <email>{customer_data.get('email', '')}</email>
        <phone>{customer_data.get('phone', '')}</phone>
    </contact>
    <organization name="{customer_data.get('organization', '')}">
        <primaryBusiness>Other</primaryBusiness>
    </organization>
</account>"""
            response = requests.post(url, data=xml_payload, auth=self.auth, headers=self.headers)
            if response.status_code in [200, 201]:
                root = ET.fromstring(response.content)
                account_id_elem = root.find('.//id')
                if account_id_elem is not None:
                    print(f"Created customer account '{customer_data['username']}' with ID {account_id_elem.text}")
                    return int(account_id_elem.text)
            print(f"Failed to create customer account: {response.status_code} {response.text}")
            return None
        except Exception as e:
            print(f"Exception creating customer account: {str(e)}")
            return None

    def create_property_xml(self, property_data: Dict) -> str:
        property_elem = ET.Element('property')

        name_elem = ET.SubElement(property_elem, 'name')
        name_elem.text = str(property_data.get('name', ''))

        primary_function_elem = ET.SubElement(property_elem, 'primaryFunction')
        primary_function_elem.text = str(property_data.get('primaryFunction', 'Office'))

        address_elem = ET.SubElement(property_elem, 'address')
        address_elem.set('address1', str(property_data.get('address1', '')))
        address_elem.set('city', str(property_data.get('city', '')))
        address_elem.set('state', str(property_data.get('state', '')))
        address_elem.set('postalCode', str(property_data.get('postalCode', '')))
        address_elem.set('country', str(property_data.get('country', 'US')))

        if property_data.get('address2'):
            address_elem.set('address2', str(property_data['address2']))

        if property_data.get('yearBuilt'):
            year_built_elem = ET.SubElement(property_elem, 'yearBuilt')
            year_built_elem.text = str(property_data['yearBuilt'])

        construction_status_elem = ET.SubElement(property_elem, 'constructionStatus')
        construction_status_elem.text = str(property_data.get('constructionStatus', 'Existing'))

        gfa_elem = ET.SubElement(property_elem, 'grossFloorArea')
        gfa_elem.set('temporary', str(property_data.get('gfaTemporary', 'false')).lower())
        gfa_elem.set('units', str(property_data.get('gfaUnits', 'Square Feet')))
        value_elem = ET.SubElement(gfa_elem, 'value')
        value_elem.text = str(property_data.get('grossFloorArea', ''))

        if property_data.get('occupancyPercentage'):
            occupancy_elem = ET.SubElement(property_elem, 'occupancyPercentage')
            occupancy_elem.text = str(property_data['occupancyPercentage'])

        is_federal_elem = ET.SubElement(property_elem, 'isFederalProperty')
        is_federal_elem.text = str(property_data.get('isFederalProperty', 'false')).lower()

        if property_data.get('notes'):
            notes_elem = ET.SubElement(property_elem, 'notes')
            notes_elem.text = f"<![CDATA[{property_data['notes']}]]>"

        if property_data.get('country', 'US') == 'CA' and property_data.get('isInstitutionalProperty'):
            institutional_elem = ET.SubElement(property_elem, 'isInstitutionalProperty')
            institutional_elem.text = str(property_data['isInstitutionalProperty']).lower()

        xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_string += ET.tostring(property_elem, encoding='unicode')
        return xml_string

    def create_property(self, account_id: int, property_data: Dict) -> Optional[Dict]:
        try:
            url = f"{self.base_url}/account/{account_id}/property"
            xml_payload = self.create_property_xml(property_data)

            response = requests.post(url, data=xml_payload, auth=self.auth, headers=self.headers)
            if response.status_code in [200, 201]:
                root = ET.fromstring(response.content)
                property_id_elem = root.find('.//id')
                return {
                    'status': 'success',
                    'property_name': property_data.get('name'),
                    'property_id': int(property_id_elem.text) if property_id_elem is not None else None,
                    'message': 'Property created successfully'
                }
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

    def import_from_csv(self, csv_file_path: str, customer_account_id: Optional[int] = None, delay_seconds: float = 1.0) -> List[Dict]:
        try:
            df = pd.read_csv(csv_file_path)
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            return []

        if customer_account_id is None:
            customer_account_id = self.get_account_id()
            if customer_account_id is None:
                print("Failed to retrieve account ID. Check credentials and connection.")
                return []

        print(f"Using customer account ID: {customer_account_id}")
        print(f"Importing {len(df)} properties...")
        print()

        results = []
        for idx, row in df.iterrows():
            property_data = row.to_dict()
            property_data = {k: v for k, v in property_data.items() if pd.notna(v)}

            print(f"Creating property {idx + 1}/{len(df)}: {property_data.get('name', 'Unknown')}")

            result = self.create_property(customer_account_id, property_data)
            results.append(result)

            if result['status'] == 'success':
                print(f"  ✓ Success - Property ID: {result['property_id']}")
            else:
                print(f"  ✗ Failed - {result['message']}")

            if idx < len(df) - 1:
                time.sleep(delay_seconds)
            print()
        return results

    def export_results(self, results: List[Dict], output_file: str = 'import_results.csv'):
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"Results exported to {output_file}")


if __name__ == "__main__":
    # Config
    USERNAME = "your_test_provider_username"
    PASSWORD = "your_test_provider_password"
    USE_TEST_ENV = True

    importer = PortfolioManagerImporter(USERNAME, PASSWORD, use_test_environment=USE_TEST_ENV)

    # Example: create a test customer account to import properties under
    customer_data = {
        'username': 'testcustomer1',
        'password': 'TestPass123!',
        'firstName': 'Test',
        'lastName': 'Customer',
        'email': 'testcustomer@example.com',
        'phone': '555-123-4567',
        'organization': 'Test Org Inc'
    }
    customer_account_id = importer.create_customer_account(customer_data)

    if customer_account_id:
        # Import properties under this customer account using CSV 'sample_properties.csv'
        results = importer.import_from_csv('sample_properties.csv', customer_account_id=customer_account_id)
        importer.export_results(results, 'import_results.csv')
    else:
        print("Customer account creation failed. Cannot proceed with import.")
