import hashlib
import os
import pathlib
import urllib.parse
from typing import Any

import yaml
from playwright.sync_api import sync_playwright, Browser

PAGES = (
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-1/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-2/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-3/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-4/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-5/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-6/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-7/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-8/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-9/",
    "https://lifeintheuktestweb.co.uk/british-naturalization-test-10/",
    "https://lifeintheuktestweb.co.uk/audio-british-citizenship-test-11/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-practice-questions-12/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-13/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-14/",
    "https://lifeintheuktestweb.co.uk/british-citizenship-test-15/",
    "https://lifeintheuktestweb.co.uk/life-in-the-uk-exam-16/",
    "https://lifeintheuktestweb.co.uk/exam-17/",
)

Question = dict[str, Any]


def make_question_id(url: str, qid: str) -> str:
    contents = f"{url}-{qid}"
    return hashlib.sha256(contents.encode('utf-8')).hexdigest()


def download_page(browser: Browser, url: str) -> dict[str, Question]:
    page = browser.new_page()
    page.goto(url)

    solution = page.evaluate("solution")
    solution = {k: v.split(",") for k, v in solution.items()}

    questions = {}

    for c in page.query_selector_all(".container_question"):
        q_text = c.query_selector(".question").inner_text().strip()
        q_id = c.get_attribute("data-id_question")
        choices = {}

        for li in c.query_selector_all(".container_answer > li"):
            a_text = li.query_selector("label").inner_text().strip()
            a_id = li.query_selector("label > input").get_attribute("data-id_answer")
            choices[a_id] = a_text

        explication = c.query_selector(".container_explication").inner_text().strip()

        question = {
            "text": q_text,
            "choices": choices,
            "solution": solution[q_id],
            "explication": explication
        }

        questions[make_question_id(url, q_id)] = question

    return questions


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        for i, url in enumerate(PAGES):
            questions = download_page(browser, url)

            print(f"({i + 1}/{len(PAGES)}) Downloaded {url}")

            output_path = os.path.join(
                os.path.dirname(__file__),
                "exams",
                pathlib.Path(urllib.parse.urlparse(url).path).stem + ".yaml"
            )

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump({"questions": questions}, f)


if __name__ == "__main__":
    main()
