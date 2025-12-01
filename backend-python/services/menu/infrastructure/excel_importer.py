"""Excel Import/Export for Menu Items"""

import pandas as pd
from typing import List, Tuple, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class ExcelImporter:
    """
    Excel importer for menu items

    Expected column format:
    - Column A: Name (required)
    - Column B: Price (optional, numeric)
    - Column C: Currency (optional, default IDR)
    - Column D: Description (optional)
    - Column E: Category (optional)
    - Column F: Subcategory (optional) - category-based grouping (Nasi, Mie, Ayam)
    - Column G: Variant (optional) - item variations (Hot, Cold, Large, Small)
    - Column H: Tags (optional)
    - Column I: Is Active (optional, boolean, default True)
    - Column J: Is Featured (optional, boolean, default False)
    - Column K: Is Available (optional, boolean, default True)
    """

    REQUIRED_COLUMNS = ["Name"]
    OPTIONAL_COLUMNS = [
        "Price", "Currency", "Description", "Category", "Subcategory", "Variant", "Tags",
        "Is Active", "Is Featured", "Is Available"
    ]
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

    def parse(
        self,
        file_content: bytes,
        menu_id: int,
        organization_id: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Parse Excel file and return valid items + errors

        Args:
            file_content: Excel file content as bytes
            menu_id: Menu ID
            organization_id: Organization ID

        Returns:
            Tuple of (valid_items, errors)
            - valid_items: List of dicts with item data
            - errors: List of dicts with row number and error message

        Raises:
            ValueError: If file format is invalid
        """
        valid_items = []
        errors = []

        try:
            # Read Excel file
            df = pd.read_excel(BytesIO(file_content))

            # Validate required columns exist
            if not all(col in df.columns for col in self.REQUIRED_COLUMNS):
                raise ValueError(
                    f"Missing required columns. Expected: {', '.join(self.REQUIRED_COLUMNS)}"
                )

            logger.info(f"Parsing Excel file with {len(df)} rows")

            # Process each row
            for idx, row in df.iterrows():
                row_num = idx + 2  # Excel row (1-indexed, header at row 1)

                try:
                    # Validate and extract name (required)
                    name = str(row.get("Name", "")).strip()
                    if not name or name.lower() == 'nan':
                        errors.append({
                            "row": row_num,
                            "error": "Name is required and cannot be empty"
                        })
                        continue

                    # Parse price (optional)
                    price = None
                    if pd.notna(row.get("Price")):
                        try:
                            price_value = float(row["Price"])
                            if price_value < 0:
                                raise ValueError("Price cannot be negative")
                            price = Decimal(str(price_value))
                        except (ValueError, InvalidOperation) as e:
                            errors.append({
                                "row": row_num,
                                "error": f"Invalid price format: {str(e)}"
                            })
                            continue

                    # Extract description (optional)
                    description = None
                    if pd.notna(row.get("Description")):
                        description = str(row["Description"]).strip()
                        if description.lower() == 'nan' or not description:
                            description = None

                    # Extract currency (optional, default IDR)
                    currency = "IDR"
                    if pd.notna(row.get("Currency")):
                        currency_val = str(row["Currency"]).strip().upper()
                        if currency_val and currency_val.lower() != 'nan':
                            currency = currency_val

                    # Extract category (optional)
                    category = None
                    if pd.notna(row.get("Category")):
                        category = str(row["Category"]).strip()
                        if category.lower() == 'nan' or not category:
                            category = None

                    # Extract subcategory (optional) - category-based grouping
                    subcategory = None
                    if pd.notna(row.get("Subcategory")):
                        subcategory = str(row["Subcategory"]).strip()
                        if subcategory.lower() == 'nan' or not subcategory:
                            subcategory = None

                    # Extract variant (optional) - item variations like Hot, Cold
                    variant = None
                    if pd.notna(row.get("Variant")):
                        variant = str(row["Variant"]).strip()
                        if variant.lower() == 'nan' or not variant:
                            variant = None

                    # Extract tags (optional)
                    tags = None
                    if pd.notna(row.get("Tags")):
                        tags = str(row["Tags"]).strip()
                        if tags.lower() == 'nan' or not tags:
                            tags = None

                    # Parse boolean fields
                    def parse_boolean(value, default: bool) -> bool:
                        if pd.isna(value):
                            return default
                        str_value = str(value).strip().lower()
                        if str_value in ('true', 'yes', '1', 'ya', 'aktif', 'active'):
                            return True
                        elif str_value in ('false', 'no', '0', 'tidak', 'inactive'):
                            return False
                        return default

                    is_active = parse_boolean(row.get("Is Active"), True)
                    is_featured = parse_boolean(row.get("Is Featured"), False)
                    is_available = parse_boolean(row.get("Is Available"), True)

                    # Create item dict
                    item_data = {
                        "menu_id": menu_id,
                        "organization_id": organization_id,
                        "name": name,
                        "description": description,
                        "price": price,
                        "currency": currency,
                        "category": category,
                        "subcategory": subcategory,
                        "variant": variant,
                        "tags": tags,
                        "display_order": idx,  # Auto-order by row index
                        "is_active": is_active,
                        "is_featured": is_featured,
                        "is_available": is_available,
                    }

                    valid_items.append(item_data)

                except Exception as e:
                    errors.append({
                        "row": row_num,
                        "error": f"Unexpected error: {str(e)}"
                    })
                    logger.warning(f"Error parsing row {row_num}: {e}")

            logger.info(
                f"Parsed Excel: {len(valid_items)} valid items, {len(errors)} errors"
            )

            return valid_items, errors

        except Exception as e:
            logger.error(f"Failed to parse Excel file: {e}")
            raise ValueError(f"Failed to parse Excel file: {str(e)}")


class ExcelExporter:
    """Excel exporter for menu items"""

    def generate_template(self) -> bytes:
        """
        Generate Excel template file for menu import

        Returns:
            Excel file content as bytes
        """
        # Create sample data
        data = {
            "Name": ["Nasi Goreng Special", "Mie Goreng Seafood", "Es Teh Manis"],
            "Price": [35000, 32000, 5000],
            "Currency": ["IDR", "IDR", "IDR"],
            "Description": [
                "Spicy fried rice with chicken and vegetables",
                "Stir-fried noodles with seafood",
                "Sweet iced tea",
            ],
            "Category": ["Main Course", "Main Course", "Beverages"],
            "Subcategory": ["Nasi", "Mie", ""],
            "Variant": ["Pedas", "Original", "Cold"],
            "Tags": ["spicy,chicken", "seafood", "cold,sweet"],
            "Is Active": ["Yes", "Yes", "Yes"],
            "Is Featured": ["Yes", "No", "No"],
            "Is Available": ["Yes", "Yes", "No"],
        }

        # Create DataFrame
        df = pd.DataFrame(data)

        # Write to Excel in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Menu Items')

            # Auto-adjust column widths
            worksheet = writer.sheets['Menu Items']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)

        output.seek(0)
        return output.getvalue()

    def export_menu(
        self,
        menu_name: str,
        items: List[Dict[str, Any]]
    ) -> bytes:
        """
        Export menu items to Excel

        Args:
            menu_name: Menu name for sheet title
            items: List of menu item dicts

        Returns:
            Excel file content as bytes
        """
        if not items:
            # Return template if no items
            return self.generate_template()

        # Prepare data for export
        data = {
            "Name": [],
            "Price": [],
            "Currency": [],
            "Description": [],
            "Category": [],
            "Subcategory": [],
            "Variant": [],
            "Tags": [],
            "Is Active": [],
            "Is Featured": [],
            "Is Available": [],
        }

        for item in items:
            data["Name"].append(item.get("name", ""))
            data["Price"].append(
                float(item["price"]) if item.get("price") else ""
            )
            data["Currency"].append(item.get("currency", "IDR"))
            data["Description"].append(item.get("description", ""))
            data["Category"].append(item.get("category", ""))
            data["Subcategory"].append(item.get("subcategory", ""))
            data["Variant"].append(item.get("variant", ""))
            data["Tags"].append(item.get("tags", ""))
            data["Is Active"].append("Yes" if item.get("is_active", True) else "No")
            data["Is Featured"].append("Yes" if item.get("is_featured", False) else "No")
            data["Is Available"].append("Yes" if item.get("is_available", True) else "No")

        # Create DataFrame
        df = pd.DataFrame(data)

        # Write to Excel in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=menu_name[:31])  # Excel sheet name max 31 chars

            # Auto-adjust column widths
            worksheet = writer.sheets[menu_name[:31]]
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)

        output.seek(0)
        return output.getvalue()
