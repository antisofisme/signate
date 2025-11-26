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
    - Column C: Description (optional)
    - Column D: Category (optional)
    - Column E: Image URL (optional)
    - Column F: Video URL (optional)
    """

    REQUIRED_COLUMNS = ["Name"]
    OPTIONAL_COLUMNS = ["Price", "Description", "Category", "Image URL", "Video URL"]
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

                    # Extract category (optional)
                    category = None
                    if pd.notna(row.get("Category")):
                        category = str(row["Category"]).strip()
                        if category.lower() == 'nan' or not category:
                            category = None

                    # Extract image URL (optional)
                    image_url = None
                    if pd.notna(row.get("Image URL")):
                        image_url = str(row["Image URL"]).strip()
                        if image_url.lower() == 'nan' or not image_url:
                            image_url = None

                    # Extract video URL (optional)
                    video_url = None
                    if pd.notna(row.get("Video URL")):
                        video_url = str(row["Video URL"]).strip()
                        if video_url.lower() == 'nan' or not video_url:
                            video_url = None

                    # Create item dict
                    item_data = {
                        "menu_id": menu_id,
                        "organization_id": organization_id,
                        "name": name,
                        "description": description,
                        "price": price,
                        "category": category,
                        "image_url": image_url,
                        "video_url": video_url,
                        "display_order": idx,  # Auto-order by row index
                        "is_active": True,
                        "is_featured": False,
                        "is_available": True,
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
            "Description": [
                "Spicy fried rice with chicken and vegetables",
                "Stir-fried noodles with seafood",
                "Sweet iced tea",
            ],
            "Category": ["Main Course", "Main Course", "Beverages"],
            "Image URL": [
                "https://api.zhmhotels.online/content/nasi-goreng.jpg",
                "",
                "",
            ],
            "Video URL": ["", "", ""],
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
            "Description": [],
            "Category": [],
            "Image URL": [],
            "Video URL": [],
        }

        for item in items:
            data["Name"].append(item.get("name", ""))
            data["Price"].append(
                float(item["price"]) if item.get("price") else ""
            )
            data["Description"].append(item.get("description", ""))
            data["Category"].append(item.get("category", ""))
            data["Image URL"].append(item.get("image_url", ""))
            data["Video URL"].append(item.get("video_url", ""))

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
