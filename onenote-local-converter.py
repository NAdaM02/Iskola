import argparse
from pathlib import Path
import struct
import re
import uuid
from dataclasses import dataclass
from bs4 import BeautifulSoup
import logging

@dataclass
class OneNoteObject:
    title: str
    content: str
    created: str
    modified: str
    
class OneNoteConverter:
    def __init__(self, file_path: Path, output_dir: Path):
        self.file_path = file_path
        self.output_dir = output_dir
        self.space_re = re.compile(r"[ \t]")
        self.lines_re = re.compile(r"([\r\n] *){3,}")
        self.in_code_block = False
        
    def parse_one_file(self) -> OneNoteObject:
        """
        Parse a .one file and extract its content.
        Note: This is a simplified implementation - actual .one files have a more complex structure
        """
        try:
            with open(self.file_path, 'rb') as f:
                # Read the .one file header (simplified)
                header = f.read(16)
                if header[:2] != b'ON':  # OneNote file signature
                    raise ValueError("Not a valid OneNote file")
                
                # Skip to content (simplified)
                f.seek(1024)  # Skip header section
                
                # Read the content length
                content_length = struct.unpack('<I', f.read(4))[0]
                
                # Read the raw content
                raw_content = f.read(content_length)
                
                # Try to decode as UTF-16
                try:
                    content = raw_content.decode('utf-16')
                except UnicodeDecodeError:
                    content = raw_content.decode('utf-8', errors='ignore')
                
                # Extract HTML content (simplified)
                html_start = content.find('<html')
                html_end = content.find('</html>')
                if html_start >= 0 and html_end >= 0:
                    html_content = content[html_start:html_end + 7]
                else:
                    html_content = f"<html><body>{content}</body></html>"
                
                return OneNoteObject(
                    title=self.file_path.stem,
                    content=html_content,
                    created="Unknown",  # In a real implementation, extract from file metadata
                    modified="Unknown"
                )
        except Exception as e:
            logging.error(f"Error parsing {self.file_path}: {str(e)}")
            raise

    def convert_to_markdown(self, note: OneNoteObject) -> str:
        """Convert the OneNote HTML content to Markdown"""
        # Create metadata section
        markdown = f"""---
title: "{note.title}"
created: '{note.created}'
modified: '{note.modified}'
---

"""
        # Parse HTML
        soup = BeautifulSoup(note.content, 'html.parser')
        
        # Convert content
        markdown += self._convert_html_to_markdown(soup)
        return markdown

    def _convert_html_to_markdown(self, element) -> str:
        if isinstance(element, str):
            return element
        
        content = ""
        
        # Handle different HTML elements
        if element.name == 'h1':
            content = f"# {element.get_text().strip()}\n\n"
        elif element.name == 'h2':
            content = f"## {element.get_text().strip()}\n\n"
        elif element.name == 'h3':
            content = f"### {element.get_text().strip()}\n\n"
        elif element.name == 'p':
            if self._is_code_block(element):
                content = f"```\n{element.get_text()}\n```\n\n"
            else:
                content = f"{element.get_text()}\n\n"
        elif element.name == 'ul':
            for li in element.find_all('li', recursive=False):
                content += f"* {li.get_text()}\n"
            content += "\n"
        elif element.name == 'ol':
            for i, li in enumerate(element.find_all('li', recursive=False), 1):
                content += f"{i}. {li.get_text()}\n"
            content += "\n"
        elif element.name == 'img':
            src = element.get('src', '')
            alt = element.get('alt', '')
            if src:
                # Handle embedded images
                img_filename = f"{uuid.uuid4()}.png"
                # In a real implementation, extract and save the image
                content = f"![{alt}](attachments/{img_filename})\n\n"
        else:
            # Recursively process child elements
            for child in element.children:
                if isinstance(child, str):
                    content += child
                else:
                    content += self._convert_html_to_markdown(child)
        
        return content

    def _is_code_block(self, element) -> bool:
        """Check if the element represents a code block"""
        style = element.get('style', '').lower()
        return 'consolas' in style or 'courier' in style

    def convert(self):
        """Main conversion method"""
        try:
            # Create output directories
            self.output_dir.mkdir(parents=True, exist_ok=True)
            attachments_dir = self.output_dir / 'attachments'
            attachments_dir.mkdir(exist_ok=True)
            
            # Parse and convert
            note = self.parse_one_file()
            markdown = self.convert_to_markdown(note)
            
            # Save markdown file
            output_file = self.output_dir / f"{note.title}.md"
            output_file.write_text(markdown, encoding='utf-8')
            
            logging.info(f"Successfully converted {self.file_path} to {output_file}")
            
        except Exception as e:
            logging.error(f"Conversion failed: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Convert local OneNote (.one) files to Markdown')
    parser.add_argument('input_file', help='Path to the .one file')
    parser.add_argument('output_dir', help='Directory to save the converted markdown and attachments')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # Convert file
    converter = OneNoteConverter(Path(args.input_file), Path(args.output_dir))
    converter.convert()

if __name__ == '__main__':
    main()
