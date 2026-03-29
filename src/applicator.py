"""
Application automation for LinkedIn Easy Apply, Workday, and Indeed.
Handles form filling, resume upload, and Q&A answering.
"""

import asyncio
import logging
import os
import re
import time
import random
from pathlib import Path

from .resume_profile import CONTACT, RESUMES, EDUCATION, WORK_HISTORY, COMMON_ANSWERS, CERTIFICATIONS
from .claude_helper import get_answer

logger = logging.getLogger(__name__)

APP_ROOT = Path(__file__).parent.parent


def _resume_path(resume_type: str) -> str:
    rel = RESUMES.get(resume_type, RESUMES['it_manager'])
    full = APP_ROOT / rel
    if not full.exists():
        raise FileNotFoundError(f"Resume not found: {full}")
    return str(full)


def _contact_for_resume(resume_type: str) -> dict:
    """Return correct contact details based on resume type (screening vs primary)."""
    if resume_type == 'contract':
        return {**CONTACT,
                'email': CONTACT['email_screening'],
                'phone': CONTACT['phone_screening']}
    return {**CONTACT,
            'email': CONTACT['email_primary'],
            'phone': CONTACT['phone_primary']}


def _random_delay(min_s=0.8, max_s=2.5):
    time.sleep(random.uniform(min_s, max_s))


async def _async_delay(min_s=1.0, max_s=3.0):
    await asyncio.sleep(random.uniform(min_s, max_s))


# ─────────────────────────────────────────────────────────
# COMMON ANSWER LOOKUP
# ─────────────────────────────────────────────────────────

def _lookup_common_answer(question: str) -> str:
    """
    Check if a question matches a pre-built answer from COMMON_ANSWERS.
    Returns the answer string, or empty string if no match.
    """
    if not question:
        return ''

    q_lower = question.lower().strip()

    # Salary questions
    if any(w in q_lower for w in ['salary', 'compensation', 'pay expectation', 'desired pay']):
        if 'minimum' in q_lower or 'min' in q_lower:
            return COMMON_ANSWERS.get('salary_min', '')
        if 'maximum' in q_lower or 'max' in q_lower:
            return COMMON_ANSWERS.get('salary_max', '')
        if 'hourly' in q_lower or 'rate' in q_lower:
            return COMMON_ANSWERS.get('hourly_rate', '')
        return COMMON_ANSWERS.get('salary_expectation', '')

    # Work authorization
    if any(w in q_lower for w in ['authorized', 'authorization', 'legally', 'eligible to work']):
        return COMMON_ANSWERS.get('work_authorization', '')

    # Sponsorship
    if any(w in q_lower for w in ['sponsorship', 'visa', 'sponsor']):
        return COMMON_ANSWERS.get('sponsorship_required', '')

    # Relocation
    if 'relocat' in q_lower:
        return COMMON_ANSWERS.get('willing_to_relocate', '')

    # Start date / notice period
    if any(w in q_lower for w in ['start date', 'when can you start', 'available to start']):
        return COMMON_ANSWERS.get('start_date', '')
    if 'notice' in q_lower:
        return COMMON_ANSWERS.get('notice_period', '')

    # Years of experience
    if 'years' in q_lower and 'experience' in q_lower:
        return COMMON_ANSWERS.get('years_of_experience', '')

    # Management experience
    if 'management' in q_lower and 'experience' in q_lower:
        return COMMON_ANSWERS.get('management_experience', '')

    # Education
    if any(w in q_lower for w in ['education', 'degree', 'highest level']):
        return COMMON_ANSWERS.get('highest_education', '')

    # Remote / work preference
    if any(w in q_lower for w in ['remote', 'hybrid', 'on-site', 'work arrangement']):
        return COMMON_ANSWERS.get('remote_preference', '')

    # Veteran status
    if 'veteran' in q_lower:
        return COMMON_ANSWERS.get('veteran_status', '')

    # Disability
    if 'disab' in q_lower:
        return COMMON_ANSWERS.get('disability_status', '')

    # Gender
    if 'gender' in q_lower:
        return COMMON_ANSWERS.get('gender', '')

    # Ethnicity / race
    if any(w in q_lower for w in ['ethnicity', 'race', 'demographic']):
        return COMMON_ANSWERS.get('ethnicity', '')

    return ''


# ─────────────────────────────────────────────────────────
# SHARED FORM HELPERS
# ─────────────────────────────────────────────────────────

async def _safe_fill(page, selector: str, value: str, timeout=3000):
    """Fill a form field safely, handling various input types."""
    try:
        el = await page.wait_for_selector(selector, timeout=timeout)
        if el:
            tag = await el.get_attribute('type') or 'text'
            if tag in ('radio', 'checkbox'):
                await el.check()
            else:
                await el.triple_click()
                await el.fill(value)
            return True
    except:
        pass
    return False


async def _fill_by_label(page, label_text: str, value: str) -> bool:
    """Try to fill an input by finding its label."""
    try:
        # Try aria-label or placeholder
        selectors = [
            f'input[aria-label*="{label_text}" i]',
            f'input[placeholder*="{label_text}" i]',
            f'textarea[aria-label*="{label_text}" i]',
            f'label:has-text("{label_text}") + input',
            f'label:has-text("{label_text}") ~ input',
        ]
        for sel in selectors:
            el = await page.query_selector(sel)
            if el:
                await el.triple_click()
                await el.fill(value)
                return True
    except:
        pass
    return False


async def _answer_screening_question(page, question_text: str, job_context: str,
                                      resume_type: str, input_el=None) -> str:
    """Get Claude's answer for a screening question and fill it in."""
    answer = await get_answer(question_text, job_context, resume_type)
    if input_el and answer:
        try:
            tag = await input_el.evaluate('el => el.tagName.toLowerCase()')
            if tag == 'textarea' or tag == 'input':
                await input_el.triple_click()
                await input_el.fill(answer)
            elif tag == 'select':
                await input_el.select_option(label=answer)
        except Exception as e:
            logger.debug(f"Could not fill answer: {e}")
    return answer


# ─────────────────────────────────────────────────────────
# LINKEDIN EASY APPLY
# ─────────────────────────────────────────────────────────

async def apply_linkedin(page, job: dict, li_session_cookie: str = None) -> dict:
    """
    Apply to a LinkedIn job via Easy Apply.
    page: an already-open Playwright page, logged into LinkedIn.
    Returns {'success': bool, 'qa_pairs': [...], 'error': str}
    """
    result = {'success': False, 'qa_pairs': [], 'error': ''}
    contact = _contact_for_resume(job['resume_type'])
    resume_file = _resume_path(job['resume_type'])
    job_context = f"Title: {job['title']} at {job['company']}\n{job.get('description','')[:2000]}"

    try:
        await page.goto(job['url'], wait_until='domcontentloaded', timeout=30000)
        await _async_delay(2, 4)

        # Click Easy Apply button
        easy_apply_btn = await page.query_selector(
            'button.jobs-apply-button, .jobs-apply-button--top-card button, '
            'button[aria-label*="Easy Apply"]'
        )
        if not easy_apply_btn:
            result['error'] = 'No Easy Apply button found - may require external application'
            return result

        await easy_apply_btn.click()
        await _async_delay(1.5, 3)

        # Walk through the multi-step Easy Apply modal
        max_steps = 15
        for step in range(max_steps):
            await _async_delay(0.5, 1.5)

            # -- Phone --
            await _fill_by_label(page, 'phone', contact['phone'])
            await _fill_by_label(page, 'mobile phone', contact['phone'])

            # -- Email (usually pre-filled) --
            # Don't overwrite LinkedIn's email field

            # -- Resume upload --
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(resume_file)
                await _async_delay(1, 2)

            # -- Answer text questions --
            text_inputs = await page.query_selector_all(
                '.jobs-easy-apply-form-element input[type="text"], '
                '.jobs-easy-apply-form-element textarea'
            )
            for inp in text_inputs:
                try:
                    label_el = await page.query_selector(
                        f'label[for="{await inp.get_attribute("id")}"]'
                    )
                    question = (await label_el.inner_text()).strip() if label_el else ''

                    current_val = await inp.input_value()
                    if current_val:  # Already filled
                        continue

                    # Try common answer lookup first
                    answer = _lookup_common_answer(question)
                    if not answer:
                        answer = await _answer_screening_question(
                            page, question, job_context, job['resume_type'], inp
                        )
                        if answer:
                            result['qa_pairs'].append({'q': question, 'a': answer})
                    else:
                        await inp.triple_click()
                        await inp.fill(answer)
                        result['qa_pairs'].append({'q': question, 'a': answer})
                except Exception as e:
                    logger.debug(f"Error filling text input: {e}")

            # -- Answer select/dropdown questions --
            selects = await page.query_selector_all('.jobs-easy-apply-form-element select')
            for sel_el in selects:
                try:
                    label_el = await page.query_selector(
                        f'label[for="{await sel_el.get_attribute("id")}"]'
                    )
                    question = (await label_el.inner_text()).strip() if label_el else ''
                    options = await sel_el.query_selector_all('option')
                    option_texts = [await o.inner_text() for o in options]

                    answer = _lookup_common_answer(question)
                    if not answer:
                        answer = await get_answer(
                            question + f'\nOptions: {", ".join(option_texts)}',
                            job_context, job['resume_type']
                        )
                    if answer:
                        try:
                            await sel_el.select_option(label=answer)
                        except:
                            # Try selecting by value or partial match
                            for opt in option_texts:
                                if answer.lower() in opt.lower():
                                    await sel_el.select_option(label=opt)
                                    break
                        result['qa_pairs'].append({'q': question, 'a': answer})
                except Exception as e:
                    logger.debug(f"Error filling select: {e}")

            # -- Radio buttons --
            radio_groups = await page.query_selector_all('.jobs-easy-apply-form-element fieldset')
            for group in radio_groups:
                try:
                    legend = await group.query_selector('legend')
                    question = (await legend.inner_text()).strip() if legend else ''
                    radios = await group.query_selector_all('input[type="radio"]')
                    radio_labels = []
                    for r in radios:
                        rid = await r.get_attribute('id')
                        lbl = await page.query_selector(f'label[for="{rid}"]')
                        radio_labels.append((await lbl.inner_text()).strip() if lbl else '')

                    answer = _lookup_common_answer(question)
                    if not answer:
                        answer = await get_answer(
                            question + f'\nOptions: {", ".join(radio_labels)}',
                            job_context, job['resume_type']
                        )

                    if answer:
                        for i, lbl in enumerate(radio_labels):
                            if answer.lower() in lbl.lower():
                                await radios[i].click()
                                result['qa_pairs'].append({'q': question, 'a': lbl})
                                break
                except Exception as e:
                    logger.debug(f"Error with radio group: {e}")

            # -- Navigation --
            # Check for Submit button (final step)
            submit_btn = await page.query_selector(
                'button[aria-label*="Submit application"], '
                'button.jobs-easy-apply-content button[type="submit"]'
            )
            if submit_btn:
                await submit_btn.click()
                await _async_delay(2, 4)
                result['success'] = True
                return result

            # Check for Next / Review / Continue button
            next_btn = await page.query_selector(
                'button[aria-label*="Continue"], button[aria-label*="Next"], '
                'button[aria-label*="Review"], .artdeco-button--primary'
            )
            if next_btn:
                btn_text = (await next_btn.inner_text()).strip().lower()
                if 'submit' in btn_text:
                    await next_btn.click()
                    await _async_delay(2, 4)
                    result['success'] = True
                    return result
                await next_btn.click()
                await _async_delay(1, 2.5)
            else:
                break

        result['error'] = 'Reached max steps without submitting'

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"LinkedIn apply error: {e}")

    return result


# ─────────────────────────────────────────────────────────
# WORKDAY APPLICATOR
# ─────────────────────────────────────────────────────────

async def apply_workday(page, job: dict) -> dict:
    """
    Apply via Workday ATS (standard across many companies).
    Handles the typical Workday multi-step application flow.
    """
    result = {'success': False, 'qa_pairs': [], 'error': ''}
    contact = _contact_for_resume(job['resume_type'])
    resume_file = _resume_path(job['resume_type'])
    job_context = f"Title: {job['title']} at {job['company']}\n{job.get('description','')[:2000]}"

    try:
        await page.goto(job['url'], wait_until='domcontentloaded', timeout=30000)
        await _async_delay(2, 4)

        # Click Apply button
        apply_btn = await page.query_selector(
            'a[data-automation-id="applyNowButton"], '
            'button[data-automation-id="applyNowButton"]'
        )
        if not apply_btn:
            apply_btn = await page.query_selector('a:has-text("Apply"), button:has-text("Apply Now")')

        if not apply_btn:
            result['error'] = 'No Apply button found on Workday page'
            return result

        await apply_btn.click()
        await _async_delay(2, 4)

        # Handle login wall - Workday requires an account per company
        if 'signin' in page.url or 'login' in page.url or 'auth' in page.url:
            result['error'] = 'Workday requires login - please set up account for this company'
            return result

        # Workday multi-step form: My Information -> My Experience -> Application Questions
        max_steps = 20
        for step in range(max_steps):
            await _async_delay(1, 2)

            # -- Resume upload --
            file_inputs = await page.query_selector_all('input[type="file"]')
            for fi in file_inputs:
                try:
                    await fi.set_input_files(resume_file)
                    await _async_delay(1, 2)
                    break
                except:
                    pass

            # -- Personal info fields --
            field_map = {
                'firstName': contact['first_name'],
                'lastName': contact['last_name'],
                'email': contact['email'],
                'phone': contact['phone'],
                'city': contact['city'],
                'state': contact['state_full'],
                'postalCode': contact['zip'],
                'addressLine1': '',
                'legalName': contact['full_name'],
            }
            for field_id, value in field_map.items():
                if value:
                    try:
                        el = await page.query_selector(
                            f'input[data-automation-id="{field_id}"]'
                        )
                        if el:
                            current = await el.input_value()
                            if not current:
                                await el.fill(value)
                    except:
                        pass

            # -- Text inputs with labels --
            text_inputs = await page.query_selector_all(
                'input[data-automation-id]:not([type="file"]):not([type="hidden"]), '
                'textarea[data-automation-id]'
            )
            for inp in text_inputs:
                try:
                    automation_id = await inp.get_attribute('data-automation-id') or ''
                    current_val = await inp.input_value()
                    if current_val or not automation_id:
                        continue

                    # Find associated label
                    label_text = ''
                    label_el = await page.query_selector(f'label[for*="{automation_id}"]')
                    if label_el:
                        label_text = (await label_el.inner_text()).strip()

                    if not label_text:
                        continue

                    answer = _lookup_common_answer(label_text)
                    if not answer:
                        answer = await get_answer(label_text, job_context, job['resume_type'])
                    if answer:
                        await inp.fill(answer)
                        result['qa_pairs'].append({'q': label_text, 'a': answer})
                except Exception as e:
                    logger.debug(f"Workday text input error: {e}")

            # -- Dropdowns --
            dropdowns = await page.query_selector_all('[data-automation-id*="select"] button')
            for dd in dropdowns:
                try:
                    label_text = await dd.inner_text()
                    if label_text and 'select' in label_text.lower():
                        # Open dropdown
                        await dd.click()
                        await _async_delay(0.5, 1)
                        options = await page.query_selector_all('li[role="option"]')
                        if options:
                            opt_texts = [await o.inner_text() for o in options]
                            answer = await get_answer(
                                label_text + f'\nOptions: {", ".join(opt_texts[:10])}',
                                job_context, job['resume_type']
                            )
                            if answer:
                                for i, opt in enumerate(opt_texts):
                                    if answer.lower() in opt.lower():
                                        await options[i].click()
                                        result['qa_pairs'].append({'q': label_text, 'a': opt})
                                        break
                                else:
                                    await options[0].click()  # Select first option as fallback
                        await _async_delay(0.5, 1)
                except Exception as e:
                    logger.debug(f"Workday dropdown error: {e}")

            # -- Check for Next / Save and Continue --
            next_btn = await page.query_selector(
                'button[data-automation-id="bottom-navigation-next-btn"], '
                'button[data-automation-id="saveAndContinueButton"]'
            )
            submit_btn = await page.query_selector(
                'button[data-automation-id="bottom-navigation-submit-btn"]'
            )

            if submit_btn:
                await submit_btn.click()
                await _async_delay(3, 5)
                result['success'] = True
                return result

            if next_btn:
                await next_btn.click()
                await _async_delay(1.5, 3)
            else:
                # Try generic Save/Next/Continue buttons
                generic_next = await page.query_selector(
                    'button:has-text("Next"), button:has-text("Continue"), '
                    'button:has-text("Save and Continue")'
                )
                if generic_next:
                    await generic_next.click()
                    await _async_delay(1.5, 3)
                else:
                    break

        result['error'] = 'Could not complete Workday application'

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Workday apply error: {e}")

    return result


# ─────────────────────────────────────────────────────────
# INDEED APPLICATOR
# ─────────────────────────────────────────────────────────

async def apply_indeed(page, job: dict) -> dict:
    """Apply to an Indeed job (Indeed Apply flow)."""
    result = {'success': False, 'qa_pairs': [], 'error': ''}
    contact = _contact_for_resume(job['resume_type'])
    resume_file = _resume_path(job['resume_type'])
    job_context = f"Title: {job['title']} at {job['company']}\n{job.get('description','')[:2000]}"

    try:
        await page.goto(job['url'], wait_until='domcontentloaded', timeout=30000)
        await _async_delay(2, 4)

        # Click Apply Now button
        apply_btn = await page.query_selector(
            'button#indeedApplyButton, '
            'button[data-indeed-apply-button], '
            'button:has-text("Apply now"), '
            'a:has-text("Apply now")'
        )
        if not apply_btn:
            result['error'] = 'No Apply button found on Indeed page'
            return result

        await apply_btn.click()
        await _async_delay(2, 4)

        # Indeed Apply is a multi-step modal/page flow
        max_steps = 15
        for step in range(max_steps):
            await _async_delay(0.5, 1.5)

            # -- Resume upload --
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                try:
                    await file_input.set_input_files(resume_file)
                    await _async_delay(1, 2)
                except:
                    pass

            # -- Contact info fields --
            await _fill_by_label(page, 'First name', contact['first_name'])
            await _fill_by_label(page, 'Last name', contact['last_name'])
            await _fill_by_label(page, 'Email', contact['email'])
            await _fill_by_label(page, 'Phone', contact['phone'])
            await _fill_by_label(page, 'City', contact['city'])

            # -- Text questions --
            text_inputs = await page.query_selector_all(
                'input[type="text"]:not([readonly]), textarea:not([readonly])'
            )
            for inp in text_inputs:
                try:
                    current_val = await inp.input_value()
                    if current_val:
                        continue

                    # Find associated label
                    inp_id = await inp.get_attribute('id') or ''
                    label_el = await page.query_selector(f'label[for="{inp_id}"]') if inp_id else None
                    if not label_el:
                        # Try parent label
                        label_el = await inp.evaluate_handle(
                            'el => el.closest("label") || el.parentElement?.querySelector("label")'
                        )
                    question = ''
                    if label_el:
                        try:
                            question = (await label_el.inner_text()).strip()
                        except:
                            pass

                    if not question:
                        continue

                    answer = _lookup_common_answer(question)
                    if not answer:
                        answer = await _answer_screening_question(
                            page, question, job_context, job['resume_type'], inp
                        )
                    else:
                        await inp.triple_click()
                        await inp.fill(answer)

                    if answer:
                        result['qa_pairs'].append({'q': question, 'a': answer})
                except Exception as e:
                    logger.debug(f"Indeed text input error: {e}")

            # -- Select/dropdown questions --
            selects = await page.query_selector_all('select')
            for sel_el in selects:
                try:
                    sel_id = await sel_el.get_attribute('id') or ''
                    label_el = await page.query_selector(f'label[for="{sel_id}"]') if sel_id else None
                    question = (await label_el.inner_text()).strip() if label_el else ''

                    if not question:
                        continue

                    options = await sel_el.query_selector_all('option')
                    option_texts = [await o.inner_text() for o in options]

                    answer = _lookup_common_answer(question)
                    if not answer:
                        answer = await get_answer(
                            question + f'\nOptions: {", ".join(option_texts)}',
                            job_context, job['resume_type']
                        )

                    if answer:
                        try:
                            await sel_el.select_option(label=answer)
                        except:
                            for opt in option_texts:
                                if answer.lower() in opt.lower():
                                    await sel_el.select_option(label=opt)
                                    break
                        result['qa_pairs'].append({'q': question, 'a': answer})
                except Exception as e:
                    logger.debug(f"Indeed select error: {e}")

            # -- Radio buttons --
            radio_groups = await page.query_selector_all('fieldset')
            for group in radio_groups:
                try:
                    legend = await group.query_selector('legend, .ia-BasePage-heading')
                    question = (await legend.inner_text()).strip() if legend else ''
                    if not question:
                        continue

                    radios = await group.query_selector_all('input[type="radio"]')
                    radio_labels = []
                    for r in radios:
                        rid = await r.get_attribute('id')
                        lbl = await page.query_selector(f'label[for="{rid}"]')
                        radio_labels.append((await lbl.inner_text()).strip() if lbl else '')

                    answer = _lookup_common_answer(question)
                    if not answer:
                        answer = await get_answer(
                            question + f'\nOptions: {", ".join(radio_labels)}',
                            job_context, job['resume_type']
                        )

                    if answer:
                        for i, lbl in enumerate(radio_labels):
                            if answer.lower() in lbl.lower():
                                await radios[i].click()
                                result['qa_pairs'].append({'q': question, 'a': lbl})
                                break
                except Exception as e:
                    logger.debug(f"Indeed radio group error: {e}")

            # -- Navigation --
            submit_btn = await page.query_selector(
                'button[type="submit"]:has-text("Submit"), '
                'button:has-text("Submit your application")'
            )
            if submit_btn:
                await submit_btn.click()
                await _async_delay(2, 4)
                result['success'] = True
                return result

            # Continue / Next button
            next_btn = await page.query_selector(
                'button:has-text("Continue"), '
                'button:has-text("Next"), '
                'button[data-testid="next-button"]'
            )
            if next_btn:
                btn_text = (await next_btn.inner_text()).strip().lower()
                if 'submit' in btn_text:
                    await next_btn.click()
                    await _async_delay(2, 4)
                    result['success'] = True
                    return result
                await next_btn.click()
                await _async_delay(1, 2.5)
            else:
                break

        result['error'] = 'Could not complete Indeed application'

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Indeed apply error: {e}")

    return result


# ─────────────────────────────────────────────────────────
# MAIN DISPATCHER
# ─────────────────────────────────────────────────────────

async def apply_to_job(job: dict, settings: dict) -> dict:
    """
    Apply to a job using the appropriate platform handler.
    Launches a Playwright browser, routes to the correct applicator,
    and returns the result.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {'success': False, 'qa_pairs': [], 'error': 'Playwright not installed'}

    platform = job.get('platform', 'manual')
    result = {'success': False, 'qa_pairs': [], 'error': ''}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
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
        )
        # Remove automation indicators
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
        """)

        # Add LinkedIn cookie if available
        li_cookie = settings.get('linkedin_session_cookie', '')
        if li_cookie and platform == 'linkedin':
            await context.add_cookies([{
                'name': 'li_at',
                'value': li_cookie,
                'domain': '.linkedin.com',
                'path': '/',
            }])

        page = await context.new_page()

        try:
            if platform == 'linkedin':
                result = await apply_linkedin(page, job, li_cookie)
            elif platform == 'workday':
                result = await apply_workday(page, job)
            elif platform == 'indeed':
                result = await apply_indeed(page, job)
            else:
                result['error'] = f'Unsupported platform: {platform}. Please apply manually at {job.get("url", "")}'
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Application error for {job.get('title', '?')}: {e}")
        finally:
            await browser.close()

    return result
