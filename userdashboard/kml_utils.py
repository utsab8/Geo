import json
import csv
import zipfile
import os
import tempfile
import re
from io import StringIO, BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.core.files.storage import default_storage
import xml.etree.ElementTree as ET
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.wkt import loads
import pyogrio
from decimal import Decimal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class KMLParser:
    """Enhanced utility class for parsing KML files with all available fields"""
    
    def __init__(self, kml_file_path):
        self.kml_file_path = kml_file_path
        self.namespace = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'atom': 'http://www.w3.org/2005/Atom',
            'xal': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0',
        }
    
    def parse_kml(self):
        """Parse KML file and extract comprehensive data"""
        print(f"🔍 KMLParser.parse_kml() called for file: {self.kml_file_path}")
        logger.info(f"KMLParser.parse_kml() called for file: {self.kml_file_path}")
        
        try:
            tree = ET.parse(self.kml_file_path)
            root = tree.getroot()
            print(f"✅ XML tree parsed, root tag: {root.tag}")
            logger.info(f"XML tree parsed, root tag: {root.tag}")
            
            placemarks = root.findall('.//kml:Placemark', self.namespace)
            print(f"🔍 Found {len(placemarks)} placemarks in KML file")
            logger.info(f"Found {len(placemarks)} placemarks in KML file")
            
            if not placemarks:
                print("❌ No placemarks found in KML file")
                logger.warning("No placemarks found in KML file")
                return []
            
            parsed_data = []
            for i, placemark in enumerate(placemarks):
                print(f"🔍 Processing placemark {i+1}/{len(placemarks)}")
                try:
                    data = self._extract_comprehensive_placemark_data(placemark)
                    if data:
                        parsed_data.append(data)
                        print(f"  ✅ Placemark {i+1} processed successfully")
                    else:
                        print(f"  ⚠️ Placemark {i+1} returned no data (skipped)")
                except Exception as e:
                    print(f"  ❌ Error processing placemark {i+1}: {str(e)}")
                    logger.error(f"Error processing placemark {i+1}: {str(e)}")
                    continue
            
            print(f"✅ KML parsing completed. Successfully processed {len(parsed_data)} placemarks")
            logger.info(f"KML parsing completed. Successfully processed {len(parsed_data)} placemarks")
            return parsed_data
            
        except ET.ParseError as e:
            print(f"❌ KML parsing error: {e}")
            logger.error(f"KML parsing error: {e}")
            raise ValueError(f"Invalid KML file format: {e}")
        except Exception as e:
            print(f"❌ Unexpected error parsing KML: {e}")
            logger.error(f"Unexpected error parsing KML: {e}")
            raise ValueError(f"Error parsing KML file: {e}")
    
    def _extract_comprehensive_placemark_data(self, placemark):
        """Extract comprehensive data from a single placemark including all available fields"""
        try:
            # Extract basic information
            name = self._get_element_text(placemark, 'kml:name')
            description = self._get_element_text(placemark, 'kml:description')
            clean_description = self._clean_html_tags(description)
            
            print(f"    📝 Placemark name: {name or 'Unnamed'}")
            
            # Extract geometry
            geometry_data = self._extract_geometry(placemark)
            if not geometry_data:
                print(f"    ❌ No geometry found for placemark: {name or 'Unnamed'}")
                return None
            
            print(f"    🗺️ Geometry type: {geometry_data['type']}")
            
            # Extract custom data (kitta number, owner name)
            custom_data = self._extract_custom_data(placemark, description, name)
            
            # Extract extended data
            extended_data = self._extract_extended_data(placemark)
            
            # Extract time information
            time_data = self._extract_time_data(placemark)
            
            # Extract style information
            style_data = self._extract_style_data(placemark)
            
            # Extract altitude and other geometric properties
            altitude_data = self._extract_altitude_data(placemark)
            
            # Extract address information
            address_data = self._extract_address_data(placemark)
            
            # Extract phone number and website
            contact_data = {
                'phone_number': None,
            }
        
            # Combine all data
            comprehensive_data = {
                # Basic fields (shown in preview)
                'placemark_name': name,
                'kitta_number': custom_data.get('kitta_number', ''),
                'owner_name': custom_data.get('owner_name', ''),
                'geometry_type': geometry_data['type'],
                'coordinates': json.dumps(geometry_data['coordinates']),
                'area_hectares': geometry_data.get('area_hectares'),
                'area_sqm': geometry_data.get('area_sqm'),
                'description': clean_description,
                
                # Extended data (hidden in preview, included in CSV)
                'extended_data': json.dumps(extended_data),
                'time_begin': time_data.get('begin'),
                'time_end': time_data.get('end'),
                'time_when': time_data.get('when'),
                'altitude': altitude_data.get('altitude'),
                'altitude_mode': altitude_data.get('altitude_mode'),
                'tessellate': altitude_data.get('tessellate'),
                'extrude': altitude_data.get('extrude'),
                'style_id': style_data.get('style_id'),
                'style_url': style_data.get('style_url'),
                'address': address_data.get('address'),
                'country_code': address_data.get('country_code'),
                'administrative_area': address_data.get('administrative_area'),
                'sub_administrative_area': address_data.get('sub_administrative_area'),
                'locality': address_data.get('locality'),
                'sub_locality': address_data.get('sub_locality'),
                'thoroughfare': address_data.get('thoroughfare'),
                'postal_code': address_data.get('postal_code'),
                'phone_number': contact_data.get('phone_number'),
                'website': '', # Removed website field
                'snippet': self._get_element_text(placemark, 'kml:snippet'),
                'visibility': self._get_element_text(placemark, 'kml:visibility'),
                'open': self._get_element_text(placemark, 'kml:open'),
                'atom_author': self._get_element_text(placemark, 'atom:author'),
                'atom_link': self._get_element_text(placemark, 'atom:link'),
                'xal_address_details': self._get_element_text(placemark, 'xal:AddressDetails'),
            }
            
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error extracting comprehensive placemark data: {e}")
            return None
    
    def _extract_extended_data(self, placemark):
        """Extract all extended data from placemark"""
        extended_data = {}
        extended_data_elem = placemark.find('.//kml:ExtendedData', self.namespace)
        
        if extended_data_elem is not None:
            # Extract Data elements
            for data_elem in extended_data_elem.findall('kml:Data', self.namespace):
                name = data_elem.get('name')
                value_elem = data_elem.find('kml:value', self.namespace)
                if name and value_elem is not None and value_elem.text:
                    extended_data[name] = self._clean_html_tags(value_elem.text.strip())
            
            # Extract SimpleData elements
            for simple_data_elem in extended_data_elem.findall('kml:SimpleData', self.namespace):
                name = simple_data_elem.get('name')
                if name and simple_data_elem.text:
                    extended_data[name] = self._clean_html_tags(simple_data_elem.text.strip())
        
        return extended_data
    
    def _extract_time_data(self, placemark):
        """Extract time information from placemark"""
        time_data = {}
        
        # Check for TimeSpan
        timespan = placemark.find('.//kml:TimeSpan', self.namespace)
        if timespan is not None:
            time_data['begin'] = self._get_element_text(timespan, 'kml:begin')
            time_data['end'] = self._get_element_text(timespan, 'kml:end')
        
        # Check for TimeStamp
        timestamp = placemark.find('.//kml:TimeStamp', self.namespace)
        if timestamp is not None:
            time_data['when'] = self._get_element_text(timestamp, 'kml:when')
        
        return time_data
    
    def _extract_style_data(self, placemark):
        """Extract style information from placemark"""
        style_data = {}
        
        # Check for styleUrl
        style_url = placemark.find('kml:styleUrl', self.namespace)
        if style_url is not None and style_url.text:
            style_data['style_url'] = style_url.text.strip()
        
        # Check for inline styles
        style = placemark.find('.//kml:Style', self.namespace)
        if style is not None:
            style_data['style_id'] = style.get('id', '')
        
        return style_data
    
    def _extract_altitude_data(self, placemark):
        """Extract altitude and geometric properties"""
        altitude_data = {}
        
        # Check for altitude in Point
        point = placemark.find('.//kml:Point', self.namespace)
        if point is not None:
            altitude_mode = point.find('kml:altitudeMode', self.namespace)
            if altitude_mode is not None and altitude_mode.text:
                altitude_data['altitude_mode'] = altitude_mode.text.strip()
        
        # Check for altitude in LineString
        linestring = placemark.find('.//kml:LineString', self.namespace)
        if linestring is not None:
            altitude_mode = linestring.find('kml:altitudeMode', self.namespace)
            if altitude_mode is not None and altitude_mode.text:
                altitude_data['altitude_mode'] = altitude_mode.text.strip()
            tessellate = linestring.find('kml:tessellate', self.namespace)
            if tessellate is not None and tessellate.text:
                altitude_data['tessellate'] = tessellate.text.strip()
            extrude = linestring.find('kml:extrude', self.namespace)
            if extrude is not None and extrude.text:
                altitude_data['extrude'] = extrude.text.strip()
        
        # Check for altitude in Polygon
        polygon = placemark.find('.//kml:Polygon', self.namespace)
        if polygon is not None:
            altitude_mode = polygon.find('.//kml:altitudeMode', self.namespace)
            if altitude_mode is not None and altitude_mode.text:
                altitude_data['altitude_mode'] = altitude_mode.text.strip()
            tessellate = polygon.find('.//kml:tessellate', self.namespace)
            if tessellate is not None and tessellate.text:
                altitude_data['tessellate'] = tessellate.text.strip()
            extrude = polygon.find('.//kml:extrude', self.namespace)
            if extrude is not None and extrude.text:
                altitude_data['extrude'] = extrude.text.strip()
        
        return altitude_data
    
    def _extract_address_data(self, placemark):
        """Extract address information"""
        address_data = {}
        
        address = placemark.find('.//kml:address', self.namespace)
        if address is not None and address.text:
            address_data['address'] = address.text.strip()
        
        # Check for structured address
        structured_address = placemark.find('.//kml:AddressDetails', self.namespace)
        if structured_address is not None:
            address_data['country_code'] = self._get_element_text(structured_address, 'kml:Country/kml:countryCode')
            address_data['administrative_area'] = self._get_element_text(structured_address, 'kml:AdministrativeArea/kml:administrativeAreaName')
            address_data['sub_administrative_area'] = self._get_element_text(structured_address, 'kml:SubAdministrativeArea/kml:subAdministrativeAreaName')
            address_data['locality'] = self._get_element_text(structured_address, 'kml:Locality/kml:localityName')
            address_data['sub_locality'] = self._get_element_text(structured_address, 'kml:SubLocality/kml:subLocalityName')
            address_data['thoroughfare'] = self._get_element_text(structured_address, 'kml:Thoroughfare/kml:thoroughfareName')
            address_data['postal_code'] = self._get_element_text(structured_address, 'kml:PostalCode/kml:postalCodeNumber')
        
        return address_data
    
    def _extract_contact_data(self, placemark):
        """Extract contact information from placemark"""
        contact_data = {
            'phone_number': None,
        }
        
        # Extract phone number from description
        description = self._get_element_text(placemark, 'kml:description')
        if description:
            phone_match = re.search(r'phone[:\s]*([+\d\s\-\(\)]+)', description, re.IGNORECASE)
            if phone_match:
                contact_data['phone_number'] = phone_match.group(1).strip()
        
        return contact_data

    def _extract_placemark_data(self, placemark):
        """Legacy method for backward compatibility - extracts limited data for preview"""
        comprehensive_data = self._extract_comprehensive_placemark_data(placemark)
        if comprehensive_data:
            # Return only the fields needed for preview
            return {
                'placemark_name': comprehensive_data['placemark_name'],
                'description': comprehensive_data['description'],
                'geometry_type': comprehensive_data['geometry_type'],
                'coordinates': comprehensive_data['coordinates'],
                'area_hectares': comprehensive_data['area_hectares'],
                'area_sqm': comprehensive_data['area_sqm'],
                'kitta_number': comprehensive_data['kitta_number'],
                'owner_name': comprehensive_data['owner_name'],
            }
        return None
    
    def _get_element_text(self, parent, element_name):
        """Get text content of an XML element, handling missing prefixes gracefully"""
        try:
            element = parent.find(element_name, self.namespace)
            return element.text.strip() if element is not None and element.text else ''
        except Exception as e:
            logger.warning(f"Failed to get element text for {element_name}: {e}")
            return ''
    
    def _extract_geometry(self, placemark):
        """Extract geometry data from placemark"""
        # Check for Point geometry
        point = placemark.find('.//kml:Point', self.namespace)
        if point is not None:
            coords_elem = point.find('kml:coordinates', self.namespace)
            if coords_elem is not None and coords_elem.text:
                coords = self._parse_coordinates(coords_elem.text.strip())
                if coords:
                    return {
                        'type': 'Point',
                        'coordinates': coords[0]  # Take first coordinate pair
                    }
        
        # Check for Polygon geometry
        polygon = placemark.find('.//kml:Polygon', self.namespace)
        if polygon is not None:
            outer_boundary = polygon.find('.//kml:outerBoundaryIs//kml:coordinates', self.namespace)
            if outer_boundary is not None and outer_boundary.text:
                coords = self._parse_coordinates(outer_boundary.text.strip())
                if coords:
                    area_hectares, area_sqm = self._calculate_polygon_area(coords)
                    return {
                        'type': 'Polygon',
                        'coordinates': coords,
                        'area_hectares': area_hectares,
                        'area_sqm': area_sqm
                    }
        
        # Check for LineString geometry
        linestring = placemark.find('.//kml:LineString', self.namespace)
        if linestring is not None:
            coords_elem = linestring.find('kml:coordinates', self.namespace)
            if coords_elem is not None and coords_elem.text:
                coords = self._parse_coordinates(coords_elem.text.strip())
                if coords:
                    return {
                        'type': 'LineString',
                        'coordinates': coords
                    }
        
        return None
    
    def _parse_coordinates(self, coords_text):
        """Parse coordinate string into list of [lon, lat] pairs"""
        try:
            coords = []
            for coord_pair in coords_text.split():
                parts = coord_pair.split(',')
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coords.append([lon, lat])
            return coords
        except Exception as e:
            logger.error(f"Error parsing coordinates: {e}")
            return []
    
    def _calculate_polygon_area(self, coordinates):
        """Calculate area of polygon in hectares and square meters"""
        try:
            if len(coordinates) < 3:
                return None, None
            
            # Create polygon from coordinates
            polygon = Polygon(coordinates)
            
            # Calculate area in square meters (approximate)
            # This is a simplified calculation - for accurate results, 
            # you'd need proper projection and geodesic calculations
            area_sqm = polygon.area * 111320 * 111320  # Rough conversion
            area_hectares = area_sqm / 10000
            
            return Decimal(str(area_hectares)), Decimal(str(area_sqm))
            
        except Exception as e:
            logger.error(f"Error calculating polygon area: {e}")
            return None, None
    
    def _clean_html_tags(self, text):
        """Remove HTML tags from text"""
        if not text:
            return ''
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text
    
    def _extract_custom_data(self, placemark, description, placemark_name):
        """Extract custom data like kitta number and owner name"""
        custom_data = {
            'kitta_number': '',
            'owner_name': ''
        }
        
        # Clean description from HTML tags
        clean_description = self._clean_html_tags(description)
        
        # Try to extract from ExtendedData first
        extended_data = placemark.find('.//kml:ExtendedData', self.namespace)
        if extended_data is not None:
            for data in extended_data.findall('kml:Data', self.namespace):
                name = data.get('name')
                value_elem = data.find('kml:value', self.namespace)
                if name and value_elem is not None and value_elem.text:
                    clean_value = self._clean_html_tags(value_elem.text.strip())
                    if 'kitta' in name.lower():
                        custom_data['kitta_number'] = clean_value
                    elif 'owner' in name.lower() or 'name' in name.lower():
                        custom_data['owner_name'] = clean_value
        
        # Try to extract from description if not found in ExtendedData
        if not custom_data['kitta_number'] or not custom_data['owner_name']:
            # Look for kitta number patterns in clean description
            kitta_patterns = [
                r'kitta\s*number\s*:?\s*([^\s\n\r]+)',
                r'kitta\s*:?\s*([^\s\n\r]+)',
                r'kml_\d+_\d+_\d+',  # Pattern like KML_1_11_10
                r'kml-\d+-\d+-\d+',  # Pattern like KML-1-11-10
            ]
            
            for pattern in kitta_patterns:
                match = re.search(pattern, clean_description, re.IGNORECASE)
                if match:
                    custom_data['kitta_number'] = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    break
            
            # Look for owner name patterns
            owner_patterns = [
                r'owner\s*name\s*:?\s*([^\n\r]+)',
                r'owner\s*:?\s*([^\n\r]+)',
                r'name\s*:?\s*([^\n\r]+)',
            ]
            
            for pattern in owner_patterns:
                match = re.search(pattern, clean_description, re.IGNORECASE)
                if match:
                    potential_owner = match.group(1).strip()
                    # Skip if it's the same as kitta number or placemark name
                    if (potential_owner != custom_data['kitta_number'] and 
                        potential_owner != placemark_name):
                        custom_data['owner_name'] = potential_owner
                        break
        
        # If still no owner name, use placemark name as fallback
        if not custom_data['owner_name'] and placemark_name:
            custom_data['owner_name'] = placemark_name
        
        # Clean up any remaining HTML artifacts
        custom_data['kitta_number'] = self._clean_html_tags(custom_data['kitta_number'])
        custom_data['owner_name'] = self._clean_html_tags(custom_data['owner_name'])
        
        return custom_data

class KMLExporter:
    """Utility class for exporting KML data to various formats"""
    
    @staticmethod
    def export_to_csv(kml_data_list, filename):
        """Export comprehensive KML data to CSV with all available fields"""
        try:
            # Use the comprehensive data from the enhanced model
            csv_data = []
            for kml_data in kml_data_list:
                # Use the get_all_fields_for_csv method from the enhanced model
                row_data = kml_data.get_all_fields_for_csv()
                csv_data.append(row_data)
            
            if not csv_data:
                raise ValueError("No data available for export")
            
            # Create DataFrame and export to CSV
            df = pd.DataFrame(csv_data)
            
            # Create response
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            
            # Write CSV with proper encoding
            df.to_csv(response, index=False, encoding='utf-8-sig')  # UTF-8 with BOM for Excel compatibility
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise ValueError(f"Failed to export CSV: {str(e)}")
    
    @staticmethod
    def export_to_shapefile(kml_data_list, filename):
        """Export KML data to Shapefile format"""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            shapefile_path = os.path.join(temp_dir, f"{filename}.shp")
            
            # Prepare data for GeoDataFrame
            features = []
            for kml_data in kml_data_list:
                try:
                    coords = json.loads(kml_data.coordinates)
                    
                    if kml_data.geometry_type == 'Point':
                        geom = Point(coords[0], coords[1])
                    elif kml_data.geometry_type == 'Polygon':
                        geom = Polygon(coords)
                    elif kml_data.geometry_type == 'LineString':
                        from shapely.geometry import LineString
                        geom = LineString(coords)
                    else:
                        continue
                    
                    # Create feature with all available fields
                    feature = {
                        'geometry': geom,
                        'placemark_name': kml_data.placemark_name or '',
                        'kitta_number': kml_data.kitta_number or '',
                        'owner_name': kml_data.owner_name or '',
                        'geometry_type': kml_data.geometry_type,
                        'area_hectares': float(kml_data.area_hectares) if kml_data.area_hectares else None,
                        'area_sqm': float(kml_data.area_sqm) if kml_data.area_sqm else None,
                        'description': kml_data.description or '',
                        'snippet': kml_data.snippet or '',
                        'visibility': kml_data.visibility or '',
                        'open_status': kml_data.open_status or '',
                        'time_begin': kml_data.time_begin or '',
                        'time_end': kml_data.time_end or '',
                        'time_when': kml_data.time_when or '',
                        'altitude': kml_data.altitude or '',
                        'altitude_mode': kml_data.altitude_mode or '',
                        'tessellate': kml_data.tessellate or '',
                        'extrude': kml_data.extrude or '',
                        'style_id': kml_data.style_id or '',
                        'style_url': kml_data.style_url or '',
                        'address': kml_data.address or '',
                        'country_code': kml_data.country_code or '',
                        'administrative_area': kml_data.administrative_area or '',
                        'sub_administrative_area': kml_data.sub_administrative_area or '',
                        'locality': kml_data.locality or '',
                        'sub_locality': kml_data.sub_locality or '',
                        'thoroughfare': kml_data.thoroughfare or '',
                        'postal_code': kml_data.postal_code or '',
                        'phone_number': kml_data.phone_number or '',
                        'website': '', # Removed website field
                        'atom_author': kml_data.atom_author or '',
                        'atom_link': kml_data.atom_link or '',
                        'xal_address_details': kml_data.xal_address_details or '',
                        'extended_data': json.dumps(kml_data.extended_data) if kml_data.extended_data else '',
                    }
                    features.append(feature)
                    
                except Exception as e:
                    logger.warning(f"Error processing feature for shapefile: {e}")
                    continue
            
            if not features:
                raise ValueError("No valid features found for shapefile export")
            
            # Create GeoDataFrame
            gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
            
            # Save to shapefile
            gdf.to_file(shapefile_path, engine='pyogrio')
            
            # Create zip file
            zip_path = os.path.join(temp_dir, f"{filename}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in os.listdir(temp_dir):
                    if file.endswith(('.shp', '.shx', '.dbf', '.prj', '.cpg')):
                        file_path = os.path.join(temp_dir, file)
                        zipf.write(file_path, file)
            
            # Read zip file and create response
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            response = HttpResponse(zip_content, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'
            
            # Cleanup
            cleanup_temp_files([temp_dir])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting to shapefile: {e}")
            # Cleanup on error
            if 'temp_dir' in locals():
                cleanup_temp_files([temp_dir])
            raise ValueError(f"Failed to export shapefile: {str(e)}")

    @staticmethod
    def export_to_kml(kml_data_list, filename):
        """Export KML data to a KML file"""
        try:
            from xml.dom.minidom import Document
            doc = Document()
            kml_elem = doc.createElement('kml')
            kml_elem.setAttribute('xmlns', 'http://www.opengis.net/kml/2.2')
            doc.appendChild(kml_elem)
            document_elem = doc.createElement('Document')
            kml_elem.appendChild(document_elem)

            for data in kml_data_list:
                placemark = doc.createElement('Placemark')
                # Name
                name_elem = doc.createElement('name')
                name_elem.appendChild(doc.createTextNode(data.placemark_name or ''))
                placemark.appendChild(name_elem)
                # Description
                desc_elem = doc.createElement('description')
                desc_elem.appendChild(doc.createTextNode(data.description or ''))
                placemark.appendChild(desc_elem)
                # ExtendedData
                ext_elem = doc.createElement('ExtendedData')
                # Kitta Number
                if data.kitta_number:
                    data_elem = doc.createElement('Data')
                    data_elem.setAttribute('name', 'Kitta Number')
                    value_elem = doc.createElement('value')
                    value_elem.appendChild(doc.createTextNode(data.kitta_number))
                    data_elem.appendChild(value_elem)
                    ext_elem.appendChild(data_elem)
                # Owner Name
                if data.owner_name:
                    data_elem = doc.createElement('Data')
                    data_elem.setAttribute('name', 'Owner Name')
                    value_elem = doc.createElement('value')
                    value_elem.appendChild(doc.createTextNode(data.owner_name))
                    data_elem.appendChild(value_elem)
                    ext_elem.appendChild(data_elem)
                placemark.appendChild(ext_elem)
                # Geometry
                if data.geometry_type == 'Point':
                    point_elem = doc.createElement('Point')
                    coords_elem = doc.createElement('coordinates')
                    coords = json.loads(data.coordinates)
                    coords_elem.appendChild(doc.createTextNode(f"{coords[0]},{coords[1]}"))
                    point_elem.appendChild(coords_elem)
                    placemark.appendChild(point_elem)
                elif data.geometry_type == 'Polygon':
                    poly_elem = doc.createElement('Polygon')
                    outer_elem = doc.createElement('outerBoundaryIs')
                    linear_elem = doc.createElement('LinearRing')
                    coords_elem = doc.createElement('coordinates')
                    coords = json.loads(data.coordinates)
                    coords_str = ' '.join([f"{c[0]},{c[1]}" for c in coords])
                    coords_elem.appendChild(doc.createTextNode(coords_str))
                    linear_elem.appendChild(coords_elem)
                    outer_elem.appendChild(linear_elem)
                    poly_elem.appendChild(outer_elem)
                    placemark.appendChild(poly_elem)
                elif data.geometry_type == 'LineString':
                    line_elem = doc.createElement('LineString')
                    coords_elem = doc.createElement('coordinates')
                    coords = json.loads(data.coordinates)
                    coords_str = ' '.join([f"{c[0]},{c[1]}" for c in coords])
                    coords_elem.appendChild(doc.createTextNode(coords_str))
                    line_elem.appendChild(coords_elem)
                    placemark.appendChild(line_elem)
                document_elem.appendChild(placemark)
            kml_str = doc.toprettyxml(indent='  ', encoding='utf-8')
            response = HttpResponse(kml_str, content_type='application/vnd.google-earth.kml+xml')
            response['Content-Disposition'] = f'attachment; filename="{filename}.kml"'
            return response
        except Exception as e:
            logger.error(f"Error exporting to KML: {e}")
            raise ValueError(f"Error creating KML export: {e}")

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_download(user, kml_file, download_type, file_path, file_size, request):
    """Log file download"""
    from .models import DownloadLog
    
    DownloadLog.objects.create(
        user=user,
        kml_file=kml_file,
        download_type=download_type,
        file_path=file_path,
        file_size=file_size,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

def cleanup_temp_files(file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Error cleaning up temp file {file_path}: {e}") 