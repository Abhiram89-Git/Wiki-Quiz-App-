import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def scrape_wikipedia(url: str, preview: bool = False) -> Dict:
    """
    Scrape Wikipedia article and extract structured content.
    
    Args:
        url: Wikipedia article URL
        preview: If True, only fetch title (fast validation)
    
    Returns:
        Dictionary containing title, summary, sections, entities, and raw HTML
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('h1', class_='firstHeading')
        title_text = title.get_text() if title else "Unknown"
        
        if preview:
            return {"title": title_text}
        
        # Extract summary (first paragraph)
        summary = extract_summary(soup)
        
        # Extract sections and content
        sections = extract_sections(soup)
        
        # Combine all content for LLM
        full_content = f"Title: {title_text}\n\nSummary: {summary}\n\n"
        for section in sections:
            full_content += f"## {section['title']}\n{section['content']}\n\n"
        
        # Extract key entities (people, organizations, locations)
        key_entities = extract_entities(soup)
        
        logger.info(f"Successfully scraped: {title_text}")
        
        return {
            "title": title_text,
            "summary": summary,
            "sections": [s["title"] for s in sections],
            "content": full_content,
            "key_entities": key_entities,
            "raw_html": response.text  # Store original HTML
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error scraping {url}: {str(e)}")
        raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        raise Exception(f"Error processing Wikipedia page: {str(e)}")

def extract_summary(soup: BeautifulSoup) -> str:
    """Extract the first paragraph as summary."""
    try:
        content = soup.find('div', {'id': 'mw-content-text'})
        if not content:
            return ""
        
        # Find first paragraph that has substantial text
        paragraphs = content.find_all('p', recursive=False)
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 100:
                return text
        
        return paragraphs[0].get_text() if paragraphs else ""
    except Exception as e:
        logger.warning(f"Error extracting summary: {str(e)}")
        return ""

def extract_sections(soup: BeautifulSoup, max_sections: int = 10) -> List[Dict]:
    """
    Extract major sections with their content.
    Bonus: Section-wise organization for UI.
    """
    try:
        sections = []
        content_div = soup.find('div', {'id': 'mw-content-text'})
        
        if not content_div:
            return sections
        
        # Find all h2 headers (main sections)
        h2_tags = content_div.find_all('h2', limit=max_sections)
        
        for h2 in h2_tags:
            section_title = h2.get_text().strip()
            
            # Skip edit links
            if '[edit]' in section_title:
                section_title = section_title.replace('[edit]', '').strip()
            
            # Extract content between this h2 and next h2
            content_text = ""
            current = h2.next_sibling
            
            while current and current.name != 'h2':
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if len(text) > 0 and text not in ['\n', ' ']:
                        content_text += text + " "
                current = current.next_sibling
            
            if content_text.strip():
                sections.append({
                    "title": section_title,
                    "content": content_text[:1000]  # Limit content length
                })
        
        return sections
    except Exception as e:
        logger.warning(f"Error extracting sections: {str(e)}")
        return []

def extract_entities(soup: BeautifulSoup) -> Dict[str, List[str]]:
    """
    Extract named entities (people, organizations, locations).
    This is a simple heuristic-based approach.
    """
    try:
        entities = {"people": [], "organizations": [], "locations": []}
        
        # Look for links in the article that might indicate entities
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            return entities
        
        # Find all internal Wikipedia links
        links = content_div.find_all('a', href=re.compile(r'^/wiki/'))
        
        for link in links[:20]:  # Limit to first 20 links
            link_text = link.get_text().strip()
            href = link.get('href', '')
            
            # Simple heuristic: if link ends with common suffixes, classify
            if any(suffix in href for suffix in ['University', 'College', 'Institute']):
                entities["organizations"].append(link_text)
            elif any(suffix in href for suffix in ['City', 'Country', 'Region', 'State']):
                entities["locations"].append(link_text)
            elif link_text and len(link_text) < 30:  # Names are usually short
                entities["people"].append(link_text)
        
        # Remove duplicates
        entities = {k: list(set(v))[:5] for k, v in entities.items()}
        
        return entities
    except Exception as e:
        logger.warning(f"Error extracting entities: {str(e)}")
        return {"people": [], "organizations": [], "locations": []}