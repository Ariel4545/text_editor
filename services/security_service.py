import time
import base64
import re
import json
from collections import deque
import subprocess
import shlex
import os
import ipaddress
import socket
from urllib.parse import urlparse, urlunsplit, urljoin
import urllib.robotparser as robotparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class SecurityService:
    """A service to handle security-related logic for the email client."""

    ENCRYPTION_PREFIX = "EgonTE_ENC_v1::"

    def __init__(self, log_callback=None,
                 brute_force_protection_enabled=True, anomaly_detection_enabled=True,
                 login_lockout_duration=60, login_max_attempts=5,
                 anomaly_detection_window=300, anomaly_detection_threshold=3,
                 app_data=None):
        
        self.log_callback = log_callback
        self.app_data = app_data if app_data is not None else {}

        # --- Brute-Force and Anomaly Detection State ---
        self.failed_login_attempts = 0
        self.last_failed_login_time = 0
        self.failed_logins_by_source = deque(maxlen=20)

        # --- Configuration ---
        self.brute_force_protection_enabled = brute_force_protection_enabled
        self.anomaly_detection_enabled = anomaly_detection_enabled
        self.login_lockout_duration = login_lockout_duration
        self.login_max_attempts = login_max_attempts
        self.anomaly_detection_window = anomaly_detection_window
        self.anomaly_detection_threshold = anomaly_detection_threshold
        self.strict_sanitization_enabled = True
        self.data_encryption_active = False

        # --- Web Scraping Security Configuration ---
        self.https_only = True
        self.block_credentials_in_url = True
        self.block_ip_hosts = True
        self.block_private_ip = True
        self.same_origin_redirects = True
        self.sanitize_html = True
        self.respect_robots_txt = True
        self.max_kb_download = 2048
        self.warn_meta_robots = True
        self.BLOCKED_TLDS = {'.onion'}
        self.ALLOWED_CONTENT_TYPES = {'text/html', 'application/xhtml+xml', 'application/xml', 'text/xml', 'text/plain'}
        self.UA_HEADERS = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'DNT': '1',
        }
        self.REQ_TIMEOUT = 10
        self.TERMS_PATHS = ('/terms', '/terms-of-service', '/tos', '/legal/terms', '/terms-and-conditions')
        self._wbs_legal_ack = False

    def log_security_event(self, message, level="INFO"):
        """Adds a timestamped message to the security log with a severity level."""
        if self.log_callback:
            self.log_callback(message, level)

    def is_login_locked_out(self):
        """Checks if the login is currently locked out due to brute-force attempts."""
        if not self.brute_force_protection_enabled: return False, 0
        
        if self.failed_login_attempts >= self.login_max_attempts:
            time_since_last_fail = time.time() - self.last_failed_login_time
            if time_since_last_fail < self.login_lockout_duration:
                return True, int(self.login_lockout_duration - time_since_last_fail)
            else:
                self.reset_lockout()
                return False, 0
        return False, 0

    def register_failed_login(self, source_email):
        """Registers a failed login attempt and checks for anomalies."""
        self.failed_login_attempts += 1
        self.last_failed_login_time = time.time()

        if self.anomaly_detection_enabled:
            now = time.time()
            self.failed_logins_by_source.append((now, source_email))
            while self.failed_logins_by_source and (now - self.failed_logins_by_source[0][0] > self.anomaly_detection_window):
                self.failed_logins_by_source.popleft()

            unique_sources = {item[1] for item in self.failed_logins_by_source}
            if len(unique_sources) >= self.anomaly_detection_threshold:
                self.failed_login_attempts = self.login_max_attempts
                return True, len(unique_sources)
        return False, 0

    def reset_lockout(self):
        """Resets the lockout state."""
        self.failed_login_attempts = 0
        self.last_failed_login_time = 0
        self.failed_logins_by_source.clear()
        self.log_security_event("Login lockout state reset.")

    @staticmethod
    def xor_cipher(text, key):
        """Simple XOR cipher for demonstration. NOT SECURE."""
        if not key: return text
        key_len = len(key)
        return "".join(chr(ord(c) ^ ord(key[i % key_len])) for i, c in enumerate(text))

    @classmethod
    def encrypt_body(cls, text, key):
        """Encrypts with XOR and encodes with Base64."""
        if not key: return text
        encrypted = cls.xor_cipher(text, key)
        return base64.b64encode(encrypted.encode('utf-8')).decode('utf-8')

    @classmethod
    def decrypt_body(cls, b64_text, key):
        """Decodes from Base64 and decrypts with XOR."""
        if not key: return "DECRYPTION FAILED: No key provided."
        try:
            decoded_bytes = base64.b64decode(b64_text)
            decoded_text = decoded_bytes.decode('utf-8')
            return cls.xor_cipher(decoded_text, key)
        except Exception as e:
            return f"DECRYPTION FAILED: {e}"

    def encrypt_data_for_storage(self, data_dict, key):
        """Serializes, encrypts, and prefixes data for safe storage."""
        if not key: return data_dict
        json_data = json.dumps(data_dict)
        encrypted_data = self.encrypt_body(json_data, key)
        self.data_encryption_active = True
        return self.ENCRYPTION_PREFIX + encrypted_data

    def decrypt_data_from_storage(self, stored_data, key):
        """Detects prefix, decrypts, and deserializes data from storage."""
        if not isinstance(stored_data, str) or not stored_data.startswith(self.ENCRYPTION_PREFIX):
            try:
                self.data_encryption_active = False
                return json.loads(stored_data) if isinstance(stored_data, str) else stored_data
            except (json.JSONDecodeError, TypeError):
                return {}

        if not key:
            raise ValueError("A key is required to decrypt the data.")

        encrypted_part = stored_data[len(self.ENCRYPTION_PREFIX):]
        decrypted_json = self.decrypt_body(encrypted_part, key)
        
        try:
            self.data_encryption_active = True
            return json.loads(decrypted_json)
        except json.JSONDecodeError:
            raise ValueError("Decryption failed. The data may be corrupt or the key is incorrect.")

    def perform_security_audit(self):
        """Performs a security audit and returns a formatted report."""
        report = []
        report.append("--- Security Audit Report ---")
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("-----------------------------")

        status = "Enabled" if self.strict_sanitization_enabled else "Disabled"
        recommendation = "(Recommended: Enabled)" if not self.strict_sanitization_enabled else ""
        report.append(f"Input Sanitization: {status} {recommendation}")

        status = "Enabled" if self.brute_force_protection_enabled else "Disabled"
        recommendation = "(Recommended: Enabled)" if not self.brute_force_protection_enabled else ""
        report.append(f"Brute-Force Protection: {status} {recommendation}")

        status = "Enabled" if self.anomaly_detection_enabled else "Disabled"
        recommendation = "(Recommended: Enabled)" if not self.anomaly_detection_enabled else ""
        report.append(f"Login Anomaly Detection: {status} {recommendation}")

        status = "Active" if self.data_encryption_active else "Inactive"
        recommendation = "(Recommended: Active, use a strong Master Password)" if not self.data_encryption_active else ""
        report.append(f"Data-at-Rest Encryption: {status} {recommendation}")

        is_locked, time_left = self.is_login_locked_out()
        if is_locked:
            report.append(f"Current Login Lockout: Active (Remaining: {time_left}s)")
        else:
            report.append("Current Login Lockout: Inactive")

        report.append("-----------------------------")
        return "\n".join(report)

    @staticmethod
    def check_password_strength(password):
        """Analyzes password and returns strength level and color."""
        length = len(password)
        has_lower = re.search(r'[a-z]', password)
        has_upper = re.search(r'[A-Z]', password)
        has_digit = re.search(r'\d', password)
        has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)

        score = 0
        if length >= 8: score += 1
        if length >= 12: score += 1
        if has_lower and has_upper: score += 1
        if has_digit: score += 1
        if has_special: score += 1

        if length == 0: return "", ""
        elif score < 3: return "Weak", "red"
        elif score < 5: return "Medium", "orange"
        else: return "Strong", "green"

    def contains_malicious_chars(self, text):
        """Checks for characters often used in injection attacks."""
        if not self.strict_sanitization_enabled: return False
        malicious_chars = [';', '|', '&', '$', '<', '>', '`', '\\', '(', ')', '{', '}', '[', ']']
        return any(char in text for char in malicious_chars)

    def get_custom_browser_cmd(self):
        return self.app_data.get('web_tools_custom_browser_cmd', '')

    def set_custom_browser_cmd(self, cmd_tpl):
        self.app_data['web_tools_custom_browser_cmd'] = cmd_tpl

    def open_with_custom_command(self, url):
        tpl = self.get_custom_browser_cmd()
        if not tpl or '{url}' not in tpl:
            self.log_security_event("Custom browser command not configured or invalid.", "WARNING")
            return
        cmd = tpl.replace('{url}', url)
        try:
            if os.name == 'nt':
                subprocess.Popen(cmd, shell=True)
            else:
                subprocess.Popen(shlex.split(cmd))
        except Exception as e:
            self.log_security_event(f"Failed to run custom command: {e}", "ERROR")

    def get_bitly_token(self):
        return self.app_data.get('web_tools_bitly_token', '')

    def set_bitly_token(self, token):
        self.app_data['web_tools_bitly_token'] = token

    def sanitize_html_fragment(self, html_str):
        try:
            soup = BeautifulSoup(html_str, 'html.parser')
            for tag in soup(['script', 'iframe', 'object', 'embed', 'style', 'link', 'meta']):
                tag.decompose()
            for el in soup.find_all(True):
                for attr in list(el.attrs.keys()):
                    if attr.lower().startswith('on'):
                        el.attrs.pop(attr, None)
                    elif attr.lower() in {'href', 'src'}:
                        val = str(el.attrs.get(attr, ''))
                        if val.strip().lower().startswith('javascript:'):
                            el.attrs.pop(attr, None)
            return soup.prettify()
        except Exception:
            return html_str

    def robots_allows(self, url):
        try:
            parts = urlparse(url if '://' in url else f'https://{url}')
            if not parts.netloc:
                return True
            robots_url = urlunsplit((parts.scheme or 'https', parts.netloc, '/robots.txt', '', ''))
            rp = robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(self.UA_HEADERS.get('User-Agent', '*'), urlunsplit(parts))
        except Exception:
            return True

    def validate_url_policy(self, url):
        try:
            parsed = urlparse(url if '://' in url else f'https://{url}')
            scheme = (parsed.scheme or '').lower()
            host = (parsed.hostname or '').strip('[]') if parsed.hostname else ''
            if self.https_only and scheme != 'https':
                return False, 'Only HTTPS connections are allowed.', host
            if any(host.endswith(b) for b in self.BLOCKED_TLDS):
                return False, 'Domain TLD is blocked by policy.', host
            if self.block_credentials_in_url and (parsed.username or parsed.password):
                return False, 'Credentials in URL are blocked.', host

            def _is_ip_literal(h):
                try:
                    ipaddress.ip_address(h)
                    return True
                except ValueError:
                    return False

            if self.block_ip_hosts and _is_ip_literal(host):
                return False, 'Literal IP addresses are blocked.', host
            if self.block_private_ip and host:
                try:
                    addrs = {ai[4][0] for ai in socket.getaddrinfo(host, None)}
                    for a in addrs:
                        ip = ipaddress.ip_address(a)
                        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local or ip.is_multicast:
                            return False, 'Host resolves to a private/reserved address.', host
                except Exception:
                    pass
            return True, None, host
        except Exception as e:
            return False, f'URL validation failed: {e}', None

    def legal_disclaimer(self, host):
        if self._wbs_legal_ack:
            return True
        
        self.log_security_event(f"Legal disclaimer for {host} needs to be acknowledged by the user.", "INFO")
        # In a real application, this would prompt the user.
        # For this service, we assume acknowledgment is handled by the UI layer.
        return False

    def acknowledge_legal_disclaimer(self):
        self._wbs_legal_ack = True

    def offer_policy_links(self, host):
        try:
            base = f'https://{host}'
            self.log_security_event(f"Offering to open policy links for {host}", "INFO")
            # In a real app, this would interact with the UI to open a browser
        except Exception as e:
            self.log_security_event(f"Error offering policy links: {e}", "ERROR")

    def check_meta_robots_and_warn(self, soup):
        if not self.warn_meta_robots:
            return
        try:
            tag = soup.find('meta', attrs={'name': lambda v: v and v.lower() == 'robots'})
            if not tag:
                return
            content = (tag.get('content') or '').lower()
            flags = {s.strip() for s in content.split(',')}
            if {'noindex', 'nosnippet', 'noarchive'} & flags:
                self.log_security_event("Page indicates restrictive meta robots policy (e.g., noindex/nosnippet).", "WARNING")
        except Exception:
            pass

    def fetch_url_securely(self, url):
        if self.respect_robots_txt and not self.robots_allows(url):
            self.log_security_event(f"Scraping disallowed by robots.txt for {url}", "WARNING")
            return None, "robots.txt disallows scraping this URL path."
        
        ok, err, host = self.validate_url_policy(url)
        if not ok:
            self.log_security_event(f"URL blocked by policy: {err} ({url})", "ERROR")
            return None, err

        if not self._wbs_legal_ack:
            return None, "Legal disclaimer not acknowledged."

        try:
            sess = requests.Session()
            resp = sess.get(url, headers=self.UA_HEADERS, timeout=self.REQ_TIMEOUT, allow_redirects=True, stream=True)
            resp.raise_for_status()

            if self.same_origin_redirects and resp.history:
                orig_host = urlparse(url if '://' in url else f'https://{url}').hostname.lower()
                for h in resp.history:
                    redir_host = urlparse(h.url).hostname.lower()
                    if redir_host and redir_host != orig_host:
                        return None, "Cross-origin redirect blocked by policy."

            ct = (resp.headers.get('Content-Type') or '').split(';')[0].strip().lower()
            if ct and ct not in self.ALLOWED_CONTENT_TYPES:
                return None, f"Blocked by Content-Type policy: {ct}"

            max_bytes = self.max_kb_download * 1024
            chunks = []
            total = 0
            for chunk in resp.iter_content(chunk_size=8192):
                total += len(chunk)
                if total > max_bytes:
                    return None, f"Content exceeds size limit ({self.max_kb_download} KB)."
                chunks.append(chunk)
            
            data = b''.join(chunks)
            soup = BeautifulSoup(data, 'html.parser')
            self.check_meta_robots_and_warn(soup)
            
            return soup, None
        except requests.RequestException as e:
            self.log_security_event(f"Error fetching URL: {e}", "ERROR")
            return None, f"Error fetching URL: {e}"
        except Exception as e:
            self.log_security_event(f"Unexpected error during fetch: {e}", "ERROR")
            return None, f"Unexpected error: {e}"
