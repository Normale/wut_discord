import httpx
from time import sleep
from typing import List, Dict
import asyncio
from utilities import timer

BASE_URL = "https://apps.usos.pw.edu.pl"
SEARCH_URL = f"{BASE_URL}/services/courses/search"
COURSE_URL = f"{BASE_URL}/services/courses/course"


async def is_currently_conducted(course_id: str, current_sem_id: str) -> bool:
    fields_to_get = "id|name|homepage_url|profile_url|terms|ects_credits_simplified|description|bibliography|learning_outcomes|assessment_criteria|practical_placement|attributes|attributes2"
    async with httpx.AsyncClient() as client:
        json = (await client.get(COURSE_URL, params={"course_id": course_id,
                                                     "fields": fields_to_get,
                                                     })).json()
    if json["terms"][0]["id"] == current_sem_id:
        return True
    return False


async def conducted_filter(courses_list: List[str], current_sem_id: str) -> str:
    for item in courses_list:
        should_yield = await is_currently_conducted(item["course_id"], current_sem_id)
        if should_yield:
            yield item


async def get_courses_list(name: str, term: str = "2021L") -> List[Dict]:
    COURSES = []
    start_page = 1
    next_page = True
    async with httpx.AsyncClient() as client:
        while next_page:
            json = (await client.get(SEARCH_URL, params={"lang": "en",
                                                         "fac_id": "103000",
                                                         "fac_deep": True,
                                                         "fields": "course_id",
                                                         "name": name,
                                                         "start": start_page,
                                                         "num": 20
                                                         })).json()
            for item in json["items"]:
                COURSES.append(item)
            start_page += 20
            next_page = json["next_page"]

    conducted = [course async for course in conducted_filter(COURSES, term)]
    # prevent weird HTTPX+asyncio event loop error on windows.
    await asyncio.sleep(0.2)
    return conducted


if __name__ == "__main__":
    @timer
    def main():
        test_list1 = asyncio.run(get_courses_list("103A-ISA", "2021L"))
        test_list2 = asyncio.run(get_courses_list("103B-ISA", "2021L"))
        test_list1.extend(test_list2)
        for i, item in enumerate(test_list1):
            print(i, item)
    main()
