import re
from typing import List, Optional
from config import logger

class LinkReplacer:
    def __init__(self, replacement_link: str):
        self.replacement_link = replacement_link
        
        # Comprehensive regex patterns for different URL formats
        self.url_patterns = [
            # Standard HTTP/HTTPS URLs
            r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
            # URLs starting with www
            r'www\.(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
            # URLs without protocol but with domain extension
            r'(?:[-\w.])+\.(?:com|org|net|edu|gov|mil|int|co|uk|de|fr|it|es|ru|jp|cn|au|ca|br|in|za|mx|ar|cl|pe|ve|bo|py|uy|ec|gf|sr|gy|fk|io|ly|me|tv|cc|tk|ml|ga|cf|to|ws|biz|info|name|mobi|tel|travel|museum|aero|coop|jobs|post|xxx|asia|cat|pro|xxx|app|dev|page|tech|online|site|store|shop|blog|news|link|click|today|world|global|earth|space|cloud|ai|bot|app|web|digital|cyber|data|network|systems|solutions|services|group|team|company|corp|inc|ltd|llc|plc|gmbh|sarl|srl|bv|ab|as|oy|kft|spa|sas|eurl|snc|scp|sei|scarl|scrl|cvba|cvoa|eeig|se|scic|sccl|cic|community|foundation|ngo|charity|academy|university|school|college|institute|center|centre|club|society|association|union|federation|alliance|network|forum|board|council|committee|commission|organization|organisation|agency|bureau|office|department|ministry|government|administration|authority|court|tribunal|parliament|congress|senate|assembly|legislature|chamber|house|city|state|county|province|region|district|municipality|town|village|parish|ward|zone|area|sector|quarter|block|street|avenue|road|lane|drive|way|path|trail|route|highway|bridge|tunnel|port|airport|station|terminal|platform|stop|junction|crossing|square|plaza|park|garden|field|ground|yard|court|place|building|tower|center|mall|market|shop|store|restaurant|hotel|inn|motel|hostel|resort|spa|gym|club|bar|pub|cafe|coffee|tea|pizza|burger|food|drink|wine|beer|music|movie|cinema|theater|theatre|museum|gallery|library|bookstore|school|university|college|hospital|clinic|pharmacy|bank|atm|gas|fuel|car|auto|bike|bus|train|plane|boat|ship|taxi|uber|lyft|delivery|post|mail|package|gift|flower|pet|vet|beauty|hair|nail|spa|massage|fitness|yoga|dance|sport|game|toy|baby|kid|child|family|wedding|party|event|meeting|conference|seminar|workshop|training|course|class|lesson|tutor|coach|guide|tour|travel|trip|vacation|holiday|flight|ticket|booking|reservation|rental|lease|sale|buy|sell|trade|exchange|market|auction|bid|offer|deal|discount|coupon|promo|sale|free|cheap|best|top|new|hot|cool|awesome|amazing|great|good|nice|beautiful|lovely|cute|sweet|funny|interesting|useful|helpful|important|special|unique|rare|limited|exclusive|premium|luxury|quality|professional|expert|master|guru|pro|super|mega|ultra|max|plus|extra|more|less|big|small|large|tiny|huge|mini|micro|nano|giant|jumbo|king|queen|royal|noble|elite|vip|gold|silver|bronze|diamond|platinum|crystal|pearl|ruby|emerald|sapphire|amber|jade|coral|ivory|marble|granite|wood|metal|glass|plastic|paper|cloth|leather|silk|cotton|wool|fur|feather|stone|rock|sand|dirt|mud|water|fire|air|wind|rain|snow|ice|sun|moon|star|planet|earth|sky|cloud|mountain|hill|valley|river|lake|sea|ocean|beach|island|forest|tree|flower|grass|leaf|fruit|vegetable|meat|fish|bird|animal|insect|bug|spider|snake|cat|dog|horse|cow|pig|sheep|goat|chicken|duck|fish|shark|whale|dolphin|turtle|frog|butterfly|bee|ant|lion|tiger|elephant|bear|wolf|fox|deer|rabbit|mouse|rat|hamster|bird|eagle|hawk|owl|parrot|penguin|flamingo|peacock|swan|crane|stork|pelican|seagull|pigeon|crow|raven|sparrow|robin|blue|red|green|yellow|orange|purple|pink|black|white|gray|grey|brown|tan|beige|cream|gold|silver|bronze|copper|iron|steel|aluminum|plastic|rubber|glass|wood|stone|brick|concrete|marble|granite|diamond|pearl|crystal|jewel|gem|ring|necklace|bracelet|earring|watch|clock|time|hour|minute|second|day|week|month|year|century|millennium|past|present|future|old|new|young|adult|child|baby|boy|girl|man|woman|male|female|person|people|human|family|friend|love|heart|soul|mind|body|health|life|death|birth|happiness|joy|peace|hope|dream|wish|luck|success|win|victory|champion|hero|star|celebrity|famous|popular|best|worst|good|bad|right|wrong|true|false|real|fake|original|copy|first|last|next|previous|before|after|up|down|left|right|front|back|inside|outside|top|bottom|high|low|fast|slow|quick|easy|hard|difficult|simple|complex|big|small|long|short|wide|narrow|thick|thin|heavy|light|strong|weak|hot|cold|warm|cool|wet|dry|clean|dirty|fresh|old|new|young|modern|ancient|classic|vintage|retro|future|past|present|now|today|tomorrow|yesterday|morning|afternoon|evening|night|midnight|noon|dawn|dusk|sunrise|sunset|spring|summer|autumn|fall|winter|january|february|march|april|may|june|july|august|september|october|november|december|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            # Shortened URLs (bit.ly, tinyurl, etc.)
            r'(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|short\.link|tiny\.cc|is\.gd|buff\.ly|ift\.tt|youtu\.be|amzn\.to|fb\.me|ln\.is|tiny\.one|rb\.gy|cutt\.ly|short\.io|link\.tree|linktr\.ee)/[\w\-._~:/?#[\]@!$&\'()*+,;=]+',
            # Email addresses (sometimes used as contact links)
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Telegram links
            r't\.me/[\w\-._~:/?#[\]@!$&\'()*+,;=]+',
            # Discord invite links
            r'discord\.gg/[\w\-._~:/?#[\]@!$&\'()*+,;=]+',
            # WhatsApp links
            r'wa\.me/[\w\-._~:/?#[\]@!$&\'()*+,;=]+',
            # Generic domain patterns
            r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:/[\w\-._~:/?#[\]@!$&\'()*+,;=]*)?'
        ]
        
        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.url_patterns]
    
    def find_links(self, text: str) -> List[str]:
        """Find all links in the given text."""
        if not text:
            return []
        
        found_links = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            found_links.extend(matches)
        
        # Remove duplicates while preserving order
        unique_links = []
        for link in found_links:
            if link not in unique_links:
                unique_links.append(link)
        
        logger.info(f"Found {len(unique_links)} unique links: {unique_links}")
        return unique_links
    
    def replace_links(self, text: str) -> tuple[str, int]:
        """Replace all links in text with the replacement link."""
        if not text:
            return text, 0
        
        original_text = text
        replacements_made = 0
        
        # Apply each pattern to replace links
        for pattern in self.compiled_patterns:
            matches = list(pattern.finditer(text))
            if matches:
                # Replace from right to left to maintain string indices
                for match in reversed(matches):
                    start, end = match.span()
                    original_link = text[start:end]
                    
                    # Skip if the link is already our replacement link
                    if original_link.strip() != self.replacement_link.strip():
                        text = text[:start] + self.replacement_link + text[end:]
                        replacements_made += 1
                        logger.info(f"Replaced '{original_link}' with '{self.replacement_link}'")
        
        logger.info(f"Made {replacements_made} link replacements")
        return text, replacements_made
    
    def process_text(self, text: Optional[str]) -> Optional[str]:
        """Process text and replace links if any are found."""
        if not text:
            return text
        
        modified_text, count = self.replace_links(text)
        
        if count > 0:
            logger.info(f"Processed text: {count} links replaced")
            return modified_text
        else:
            logger.info("No links found to replace")
            return text
