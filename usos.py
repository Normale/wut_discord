import httpx
from time import sleep
from typing import List, Dict, Tuple
import asyncio
from utilities import timer
from bs4 import BeautifulSoup
import lxml

BASE_URL = "https://apps.usos.pw.edu.pl"
SEARCH_URL = f"{BASE_URL}/services/courses/search"
COURSE_URL = f"{BASE_URL}/services/courses/course"


async def is_currently_conducted(client: httpx.AsyncClient, course_id: str, current_sem_id: str) -> bool:
    fields_to_get = "id|name|homepage_url|profile_url|terms|ects_credits_simplified|description|bibliography|learning_outcomes|assessment_criteria|practical_placement|attributes|attributes2"
    json = (await client.get(COURSE_URL, params={"course_id": course_id,
                                                 "fields": fields_to_get,
                                                 })).json()
    if json["terms"][0]["id"] == current_sem_id:
        return True
    return False


async def conducted_filter(client: httpx.AsyncClient, courses_list: List[str], current_sem_id: str) -> str:
    for item in courses_list:
        should_yield = await is_currently_conducted(client, item["course_id"], current_sem_id)
        if should_yield:
            yield item


async def get_units_ids(client: httpx.AsyncClient, course: Dict, term_id: str) -> None:
    URL = f"{BASE_URL}/services/courses/course_edition"
    json = (await client.get(URL, params={
        "course_id": course["course_id"],
        "term_id": term_id,
        "fields": "course_units_ids"
    })).json()
    course["course_units_ids"] = json["course_units_ids"]


def parse_day(day: str) -> Tuple[str, str]:
    day = day.strip().split(' ')
    even_string = ""
    if day[0] == "co":
        if day[-1] == "(parzyste)":
            even_string = 'p'
        elif day[-1] == "(nieparzyste)":
            even_string = 'n'
        else:
            raise NotImplementedError(
                f"day[-1] is {day[-1]}.Expected '(parzyste)' or '(nieparzyste)'. Check if your language polish.")
        day = day[2]
    else:
        day = day[1]
    return (even_string, day)


def parse_hour(hour: str) -> str:
    return hour.strip().split(":")[0]


def parse(html):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select_one('title').text
    start, stop = title.find('(') + 1, title.find(')')
    unit_type = title[start:stop]
    table = soup.find_all('table')[-1]
    rows = table.findAll(name='tr')[1:-1]
    timeframes = []
    for row in rows:
        timeframe = row.findAll('td')[2].text.lstrip()
        if timeframe.startswith("(brak danych)"):
            timeframes.append(("idk", "idk", "idk"))
            continue
        day, hour, *_ = timeframe.split(',')
        even, day = parse_day(day)
        hour = parse_hour(hour)
        timeframes.append((day, hour, even))
    return unit_type, timeframes


async def fetch_and_parse(client, url):
    html = (await client.get(url)).content
    loop = asyncio.get_event_loop()
    unit_type, timeframes = await loop.run_in_executor(None, parse, html)
    return unit_type, timeframes


async def add_course_timeframes(client: httpx.AsyncClient, course: Dict, term_id: str):
    course["timeframes"] = dict()
    for unit in course["course_units_ids"]:
        URL = f"https://usosweb.usos.pw.edu.pl/kontroler.php?_action=katalog2/przedmioty/pokazGrupyZajec&zaj_cyk_id={unit}"
        unit_type, timeframes = await fetch_and_parse(client, URL)
        course["timeframes"][unit_type] = timeframes


async def get_courses_list(name: str, term: str = "2021L") -> List[Dict]:
    COURSES = []
    start_page = 1
    next_page = True
    async with httpx.AsyncClient() as client:
        while next_page:
            json = (await client.get(SEARCH_URL, params={"lang": "en",
                                                         "fac_id": "103000",
                                                         "fac_deep": True,
                                                         "fields": "course_id|name",
                                                         "name": name,
                                                         "start": start_page,
                                                         "num": 20
                                                         })).json()
            for item in json["items"]:
                COURSES.append(item)
            start_page += 20
            next_page = json["next_page"]

        conducted = [course async for course in conducted_filter(client, COURSES, term)]
        updates = [get_units_ids(client, course, term) for course in conducted]
        await asyncio.gather(*updates)
        updates = [add_course_timeframes(
            client, course, term) for course in conducted]
        await asyncio.gather(*updates)
    # prevent weird HTTPX+asyncio event loop error on windows.
    await asyncio.sleep(0.2)
    return conducted


async def get_courses_with_data():
    coroutines = [get_courses_list(
        "103A-ISA", "2021L"), get_courses_list("103B-ISA", "2021L")]
    list1, list2 = await asyncio.gather(*coroutines)
    list1.extend(list2)
    return list1

if __name__ == "__main__":
    # Mockup of usage
    @timer
    def main():
        courses_list = asyncio.run(get_courses_with_data())
        return courses_list
    main()
