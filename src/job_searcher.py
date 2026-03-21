"""
Job searchers for LinkedIn, Indeed, and manual URL ingestion.
Uses Playwright for browser automation with stealth settings.
"""

import asyncio
import hashlib
import json
import logging
import re
import time
import random
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _make_job_id(platform: str, url: str) -> str:
    """Create a stable unique ID for a job posting."""
    return platform + '_' + hashlib.md5(url.encode()).hexdigest()[:12]


def _random_delay(min_s=1.5, max_s=4.0):
    """Human-like random pause."""
    time.sleep(random.uniform(min_s, max_s))


# ─────────────────────────────────────────────────────────
# Playwright stealth setup
# ─────────────────────────────────────────────────────────

async def _get_browser(playwright, headless=False):
    """
    Launch Chromium with stealth settings to reduce bot detection.
    headless=False makes it look more like a real browser.
    """
    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-size=1440,900',
        ]
    )
    context = await browser.new_context(
        viewport={'width': 1440, 'height': 900},
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        ),
        locale='en-US',
        timezone_id='America/Chicago',
        java_script_enabled=True,
    )
    # Remove automation indicators
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
    """)
    return browser, context


# ─────────────────────────────────────────────────────────
# LINKEDIN SEARCHER
# ─────────────────────────────────────────────────────────

async def search_linkedin(keywords: list, location: str,
                           max_results: int = 25,
                           li_session_cookie: str = None) -> list:
    """
    Search LinkedIn Jobs for management roles.
    Returns list of raw job dicts ready for analysis.

    NOTE: Requires LinkedIn to be logged in OR a valid li_at session cookie.
    The browser window will be visible so Randy can log in manually if needed.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return []

    jobs = []
    query = ' '.join(keywords)
    encoded_query = query.replace(' ', '%20')
    encoded_location = location.replace(' ', '%20').replace(',', '%2C')

    # LinkedIn job search URL – filters for full-time, experience level 4 (Director), 5 (VP+)
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={encoded_query}"
        f"&location={encoded_location}"
        f"&f_JT=F"           # Full-time
        f"&f_E=4%2C5"        # Director, VP level
        f"&f_TPR=r604800"    # Posted last 7 days
        f"&sortBy=DD"        # Most recent
    )

    async with async_playwright() as p:
        browser, context = await _get_browser(p, headless=False)
        page = await context.new_page()

        # Set cookie if provided
        if li_session_cookie:
            await context.add_cookies([{
                'name': 'li_at',
                'value': li_session_cookie,
                'domain': '.linkedin.com',
                'path': '/',
            }])

        try:
            logger.info(f"Searching LinkedIn: {query} in {location}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            # Check if logged out
            if 'authwall' in page.url or 'login' in page.url:
                logger.warning("LinkedIn requires login. Please log in the browser window.")
                # Wait up to 60 seconds for user to log in
                for _ in range(60):
                    await asyncio.sleep(1)
                    if 'linkedin.com/jobs' in page.url:
                        break

            # Scroll to load more results
            for scroll in range(3):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(random.uniform(1.5, 3))

            # Extract job cards
            job_cards = await page.query_selector_all('.job-search-card, .jobs-search__results-list li')

            for card in job_cards[:max_results]:
                try:
                    title_el = await card.query_selector('.base-search-card__title, .job-card-list__title')
                    company_el = await card.query_selector('.base-search-card__subtitle, .job-card-container__company-name')
                    location_el = await card.query_selector('.job-search-card__location, .job-card-container__metadata-item')
                    link_el = await card.query_selector('a.base-card__full-link, a.job-card-list__title')

                    title = (await title_el.inner_text()).strip() if title_el else ''
                    company = (await company_el.inner_text()).strip() if company_el else ''
                    loc = (await location_el.inner_text()).strip() if location_el else ''
                    link = await link_el.get_attribute('href') if link_el else ''

                    if not title or not link:
                        continue

                    # Clean up the URL
                    link = link.split('?')[0]
                    job_id = _make_job_id('linkedin', link)

                    jobs.append({
                        'job_id':    job_id,
                        'title':     title,
                        'company':   company,
                        'location':  loc or location,
                        'platform':  'linkedin',
                        'url':       link,
                        'description': '',  # fetched separately
                        'posted_date': '',
                        'salary':    '',
                        'job_type':  'Full-time',
                    })

                except Exception as e:
                    logger.debug(f"Error parsing LinkedIn card: {e}")
                    continue

        except Exception as e:
            logger.error(f"LinkedIn search error: {e}")
        finally:
            await browser.close()

    logger.info(f"LinkedIn search found {len(jobs)} jobs")
    return jobs


async def fetch_linkedin_description(url: str, li_session_cookie: str = None) -> str:
    """Fetch full job description from a LinkedIn job URL."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return ''

    async with async_playwright() as p:
        browser, context = await _get_browser(p, headless=True)
        if li_session_cookie:
            await context.add_cookies([{
                'name': 'li_at', 'value': li_session_cookie,
                'domain': '.linkedin.com', 'path': '/',
            }])
        page = await context.new_page()
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(2)
            # Try to click "Show more" to expand description
            try:
                btn = await page.query_selector('.show-more-less-html__button--more')
                if btn:
                    await btn.click()
                    await asyncio.sleep(1)
            except:
                pass
            desc_el = await page.query_selector('.show-more-less-html__markup, .description__text')
            desc = await desc_el.inner_text() if desc_el else ''
            return desc.strip()
        except Exception as e:
            logger.debug(f"Could not fetch LinkedIn description: {e}")
            return ''
        finally:
            await browser.close()


# ─────────────────────────────────────────────────────────
# INDEED SEARCHER
# ─────────────────────────────────────────────────────────

async def search_indeed(keywords: list, location: str, max_results: int = 25) -> list:
    """Search Indeed for management roles."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed.")
        return []

    jobs = []
    query = ' '.join(keywords)

    url = (
        f"https://www.indeed.com/jobs"
        f"?q={query.replace(' ', '+')}"
        f"&l={location.replace(' ', '+').replace(',', '%2C')}"
        f"&fromage=7"         # Posted in last 7 days
        f"&sort=date"
        f"&sc=0kf%3Ajt%28fulltime%29%3B"  # Full-time
    )

    async with async_playwright() as p:
        browser, context = await _get_browser(p, headless=False)
        page = await context.new_page()

        try:
            logger.info(f"Searching Indeed: {query} in {location}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            # Handle cookie/consent dialogs
            try:
                accept_btn = await page.query_selector('[id*="accept"], button[data-tn-component="accept"]')
                if accept_btn:
                    await accept_btn.click()
                    await asyncio.sleep(1)
            except:
                pass

            # Scroll to load all results
            for _ in range(3):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(random.uniform(1.5, 2.5))

            # Extract job cards
            job_cards = await page.query_selector_all('.job_seen_beacon, .jobCard_mainContent')

            for card in job_cards[:max_results]:
                try:
                    title_el = await card.query_selector('h2.jobTitle a span, .jobTitle span[title]')
                    company_el = await card.query_selector('[data-testid="company-name"], .companyName')
                    location_el = await card.query_selector('[data-testid="text-location"], .companyLocation')
                    link_el = await card.query_selector('h2.jobTitle a, a.jcs-JobTitle')
                    salary_el = await card.query_selector('.salary-snippet-container, .estimated-salary')

                    title = (await title_el.inner_text()).strip() if title_el else ''
                    company = (await company_el.inner_text()).strip() if company_el else ''
                    loc = (await location_el.inner_text()).strip() if location_el else ''
                    salary = (await salary_el.inner_text()).strip() if salary_el else ''

                    href = ''
                    if link_el:
                        href = await link_el.get_attribute('href') or ''
                        if href and not href.startswith('http'):
                            href = 'https://www.indeed.com' + href

                    if not title or not href:
                        continue

                    # Extract Indeed job key from URL
                    jk_match = re.search(r'jk=([a-f0-9]+)', href)
                    job_id = 'indeed_' + (jk_match.group(1) if jk_match else _make_job_id('indeed', href)[-12:])

                    jobs.append({
                        'job_id':      job_id,
                        'title':       title,
                        'company':     company,
                        'location':    loc or location,
                        'platform':    'indeed',
                        'url':         href,
                        'description': '',
                        'posted_date': '',
                        'salary':      salary,
                        'job_type':    'Full-time',
                    })

                except Exception as e:
                    logger.debug(f"Error parsing Indeed card: {e}")
                    continue

        except Exception as e:
            logger.error(f"Indeed search error: {e}")
        finally:
            await browser.close()

    logger.info(f"Indeed search found {len(jobs)} jobs")
    return jobs


async def fetch_indeed_description(url: str) -> str:
    """Fetch full job description from Indeed."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return ''

    async with async_playwright() as p:
        browser, context = await _get_browser(p, headless=True)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(2)
            desc_el = await page.query_selector('#jobDescriptionText, .jobsearch-jobDescriptionText')
            desc = await desc_el.inner_text() if desc_el else ''
            return desc.strip()
        except Exception as e:
            logger.debug(f"Could not fetch Indeed description: {e}")
            return ''
        finally:
            await browser.close()


# ─────────────────────────────────────────────────────────
# MANUAL URL INGESTION
# ─────────────────────────────────────────────────────────

async def fetch_job_from_url(url: str) -> Optional[dict]:
    """
    Parse a job from any URL (LinkedIn, Indeed, Workday, or generic).
    Returns a raw job dict.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    platform = 'manual'
    if 'linkedin.com' in url:
        platform = 'linkedin'
    elif 'indeed.com' in url:
        platform = 'indeed'
    elif 'myworkdayjobs.com' in url or 'workday.com' in url:
        platform = 'workday'

    async with async_playwright() as p:
        browser, context = await _get_browser(p, headless=False)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

            title = ''
            company = ''
            description = ''
            location = ''
            salary = ''

            if platform == 'linkedin':
                try:
                    title = await page.locator('h1.top-card-layout__title').inner_text(timeout=5000)
                    company = await page.locator('.topcard__org-name-link').inner_text(timeout=5000)
                    location = await page.locator('.topcard__flavor--bullet').inner_text(timeout=5000)
                    try:
                        btn = await page.query_selector('.show-more-less-html__button--more')
                        if btn: await btn.click(); await asyncio.sleep(1)
                    except: pass
                    desc_el = await page.query_selector('.show-more-less-html__markup')
                    description = await desc_el.inner_text() if desc_el else ''
                except: pass

            elif platform == 'indeed':
                try:
                    title = await page.locator('h1.jobsearch-JobInfoHeader-title').inner_text(timeout=5000)
                    company = await page.locator('[data-testid="inlineHeader-companyName"]').inner_text(timeout=5000)
                    location = await page.locator('[data-testid="inlineHeader-companyLocation"]').inner_text(timeout=5000)
                    desc_el = await page.query_selector('#jobDescriptionText')
                    description = await desc_el.inner_text() if desc_el else ''
                except: pass

            elif platform == 'workday':
                try:
                    title = await page.locator('[data-automation-id="jobPostingHeader"]').inner_text(timeout=5000)
                    company = url.split('.')[0].replace('https://', '').title()
                    location = await page.locator('[data-automation-id="locations"]').inner_text(timeout=5000)
                    desc_el = await page.query_selector('[data-automation-id="jobPostingDescription"]')
                    description = await desc_el.inner_text() if desc_el else ''
                except: pass

            else:
                # Generic fallback: try to grab title and page text
                try:
                    title = await page.title()
                    description = await page.inner_text('body')
                    description = description[:5000]  # Cap at 5k chars
                except: pass

            if not title:
                title = await page.title()

            return {
                'job_id':      _make_job_id(platform, url),
                'title':       title.strip(),
                'company':     company.strip(),
                'location':    location.strip(),
                'platform':    platform,
                'url':         url,
                'description': description.strip(),
                'posted_date': '',
                'salary':      salary,
                'job_type':    '',
            }

        except Exception as e:
            logger.error(f"Error fetching job from URL {url}: {e}")
            return None
        finally:
            await browser.close()


# ─────────────────────────────────────────────────────────
# EMAIL ALERT PARSER
# ─────────────────────────────────────────────────────────

def parse_job_alert_email(subject: str, body: str) -> list:
    """
    Extract job links from a LinkedIn or Indeed job alert email.
    Returns list of URLs.
    """
    urls = []

    # LinkedIn job alert links
    li_links = re.findall(
        r'https://www\.linkedin\.com/jobs/view/\d+[^\s<"\']*',
        body
    )
    urls.extend(li_links)

    # Indeed job alert links
    indeed_links = re.findall(
        r'https://(?:www\.)?indeed\.com/(?:rc/clk\?jk=[a-f0-9]+|viewjob\?jk=[a-f0-9]+)[^\s<"\']*',
        body
    )
    urls.extend(indeed_links)

    # Generic job board links
    generic = re.findall(
        r'https?://[^\s<>"\']+(?:jobs|careers|position|opening|requisition)[^\s<>"\']*',
        body, re.IGNORECASE
    )
    urls.extend(generic)

    # Deduplicate
    seen = set()
    unique = []
    for u in urls:
        clean = u.split('?')[0].rstrip('/')
        if clean not in seen:
            seen.add(clean)
            unique.append(u)

    return unique
