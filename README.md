# EPA Energy Star Portfolio Manager - Bulk Property Import

This tool allows you to quickly import multiple properties from a CSV file into EPA Energy Star Portfolio Manager using their Web Services API.

## Features

- **Bulk Import**: Import multiple properties from a single CSV file
- **Error Handling**: Comprehensive error handling and reporting
- **Test Environment**: Test your imports safely before going to production
- **Progress Tracking**: Real-time feedback on import progress
- **Results Export**: Export detailed results of your import operation

## Prerequisites

1. **Portfolio Manager Account**: You need an active EPA Energy Star Portfolio Manager account
2. **Web Services Access**: Your account must be enabled for web services access
3. **Python Libraries**: Install required dependencies:

```bash
pip install requests pandas
```

## Quick Start

### Step 1: Prepare Your CSV File

Create a CSV file with your property data. See `sample_properties.csv` for a template.

**Required Columns:**
- `name` - Property name
- `primaryFunction` - Property type (see Property Types section below)
- `address1` - Street address
- `city` - City name
- `state` - State/Province code (e.g., VA, MD, DC, ON)
- `postalCode` - ZIP or postal code
- `country` - Country code (US or CA)
- `grossFloorArea` - Total square footage
- `constructionStatus` - Must be "Existing" or "Under Construction"

**Optional Columns:**
- `address2` - Additional address info (suite, unit, etc.)
- `yearBuilt` - Year the building was built
- `occupancyPercentage` - Occupancy rate (0-100)
- `gfaUnits` - Floor area units (default: "Square Feet")
- `gfaTemporary` - Set to "true" if GFA is temporary (default: "false")
- `isFederalProperty` - Set to "true" for federal properties (default: "false")
- `notes` - Any additional notes about the property
- `isInstitutionalProperty` - For Canadian properties only (true/false)

### Step 2: Configure the Script

Edit `portfolio_manager_import.py` and update the following:

```python
USERNAME = "your_username_here"  # Your Portfolio Manager username
PASSWORD = "your_password_here"  # Your Portfolio Manager password
USE_TEST_ENV = True  # Set to False for production
```

### Step 3: Run the Import

```python
python portfolio_manager_import.py
```

Or use the script programmatically:

```python
from portfolio_manager_import import PortfolioManagerImporter

# Initialize
importer = PortfolioManagerImporter(
    username="your_username",
    password="your_password",
    use_test_environment=True
)

# Import from CSV
results = importer.import_from_csv('your_properties.csv')

# Export results
importer.export_results(results, 'import_results.csv')
```

## Property Types (primaryFunction)

Here are the most common property types. Use these exact names in your CSV:

### Commercial Properties
- `Office`
- `Bank Branch`
- `Financial Office`
- `Retail Store`
- `Supermarket/Grocery Store`
- `Convenience Store with Gas Station`
- `Convenience Store without Gas Station`
- `Wholesale Club/Supercenter`

### Education
- `K-12 School`
- `College/University`
- `Adult Education`
- `Vocational School/Trade School`
- `Pre-school/Daycare`

### Healthcare
- `Hospital (General Medical & Surgical)`
- `Medical Office`
- `Ambulatory Surgical Center`
- `Urgent Care/Clinic/Other Outpatient`
- `Senior Care Community`

### Hospitality
- `Hotel`
- `Restaurant`
- `Fast Food Restaurant`
- `Bar/Nightclub`

### Industrial/Warehouse
- `Non-Refrigerated Warehouse`
- `Distribution Center`
- `Manufacturing/Industrial Plant`
- `Refrigerated Warehouse`
- `Self-Storage Facility`

### Public Services
- `Courthouse`
- `Police Station`
- `Fire Station`
- `Library`
- `Mailing Center/Post Office`

### Other
- `Data Center`
- `Parking`
- `Worship Facility`
- `Laboratory`
- `Museum`
- `Other`

For a complete list, see: https://www.energystar.gov/buildings/benchmark/understand-metrics/property-types

## Understanding the Results

After import, you'll get a results file with:
- `status` - "success" or "error"
- `property_name` - Name of the property
- `property_id` - Portfolio Manager property ID (if successful)
- `message` - Success confirmation or error details

## Troubleshooting

### Authentication Errors
- Verify your username and password
- Ensure your account has web services access enabled
- Check if you're using the correct environment (test vs. production)

### Property Creation Errors
- Verify all required fields are present
- Check that property type matches Portfolio Manager's list
- Ensure gross floor area is a valid number
- Verify state/province codes are correct

### Connection Issues
- Check your internet connection
- Verify the API endpoint is accessible
- Test environment: https://portfoliomanager.energystar.gov/wstest
- Production: https://portfoliomanager.energystar.gov/ws

## API Rate Limiting

The script includes a 1-second delay between requests by default. If you experience rate limiting issues, increase the delay:

```python
results = importer.import_from_csv('properties.csv', delay_seconds=2.0)
```

## Security Notes

- **Never commit credentials** to version control
- Use environment variables for credentials in production:

```python
import os
USERNAME = os.environ.get('PM_USERNAME')
PASSWORD = os.environ.get('PM_PASSWORD')
```

## Additional Resources

- [Portfolio Manager Web Services Documentation](https://portfoliomanager.energystar.gov/webservices/home)
- [Property Types Guide](https://www.energystar.gov/sites/default/files/2024-11/US_PropertyTypesUseDetails_Definitions_Oct2024_508.pdf)
- [Portfolio Manager Help](https://energystar.my.site.com/PortfolioManager/s/)

## Support

For API-related issues, contact EPA's Portfolio Manager support team through your account.

