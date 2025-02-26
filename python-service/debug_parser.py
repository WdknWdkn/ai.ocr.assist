#!/usr/bin/env python3
import pandas as pd
import io
import sys
import json
import logging
from parse_order_lambda import parse_excel

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_excel_parsing(file_path):
    """Debug Excel parsing with detailed logging."""
    try:
        # Read the Excel file
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # Log file info
        logger.debug(f"File size: {len(content)} bytes")
        
        # Read with pandas directly first
        df = pd.read_excel(io.BytesIO(content), header=None)
        logger.debug("\nRaw data structure:")
        logger.debug("Shape: %s", df.shape)
        logger.debug("\nFirst row (title):")
        logger.debug(df.iloc[0].to_dict())
        logger.debug("\nSecond row (headers):")
        logger.debug(df.iloc[1].to_dict())
        logger.debug("\nFirst data row:")
        logger.debug(df.iloc[2].to_dict())
        
        # Now try with proper header
        df = pd.read_excel(io.BytesIO(content), header=1)  # Use second row as header
        logger.debug("\nDataFrame with headers:")
        logger.debug("Columns: %s", list(df.columns))
        logger.debug("\nFirst two data rows:")
        logger.debug(df.head(2).to_dict('records'))
        
        # Try parsing with our function
        logger.debug("\nParsing with parse_excel function:")
        result = parse_excel(content)
        logger.debug("\nParse result:")
        logger.debug(f"Total rows: {result['total_rows']}")
        logger.debug(f"Valid rows: {result['valid_rows']}")
        logger.debug(f"Skipped rows: {result['skipped_rows']}")
        if result['orders']:
            logger.debug("\nFirst valid order:")
            logger.debug(json.dumps(result['orders'][0], ensure_ascii=False, indent=2))
            
        return result
    except Exception as e:
        logger.error(f"Error parsing file: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 debug_parser.py <excel_file>")
        sys.exit(1)
        
    debug_excel_parsing(sys.argv[1])
