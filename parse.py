import requests
import json
import aiohttp
import asyncio
import re
from itertools import islice

f = open('data.json')

data = json.load(f)

# TODO: replace with async get
def g(i):
    pid = i['pid']
    url = f'https://vanderbilt.kuali.co/api/v1/catalog/course/6074bfff280c13001c065999/{pid}'
    return json.loads(requests.get(url).content)

# courses = islice(map(g,filter(lambda i: i['subjectCode']['name'] == 'CS', data)),10)
course_urls = islice(filter(lambda i: i['subjectCode']['name'] == 'CS', data),15)
courses = []
async def process(l):
    async with aiohttp.ClientSession() as session:
        for i in l:
            pid = i['pid']
            url = f'https://vanderbilt.kuali.co/api/v1/catalog/course/6074bfff280c13001c065999/{pid}'
            async with session.get(url) as resp:
                x = await resp.json()
                # print(x)
                courses.append(x)

asyncio.run(process(course_urls))
print(courses)

COURSE_REGEX = re.compile(r'(CS[0-9]{4})\. ([^.]+)')
PREREQ_REGEX = re.compile(r'(?:Prerequisite|Prereq): ([^.]+)')
DUP_REGEX = re.compile(r'\(Also listed as (CS [0-9]{4})\)')

prereqs = {}
labels = {}
for x in courses:
    desc = x['description']
    name = x['__catalogCourseId']
    course = f'{name}. {desc}'
    course = course.strip().replace('\n', ' ')

    fc = re.findall(COURSE_REGEX, course)[0]
    found_course = (fc[0][:2] + ' ' + fc[0][-4:], fc[1])
    labels[found_course[0]] = found_course[1]

    match = re.findall(PREREQ_REGEX, course)
    final_reqs = []
    if match:
        reqs = match[0].strip().split(';')
        for req in reqs:
            req = req.strip()
            category = None
            courses = []
            foundOr = False
            for token in req.split(' '):
                token = token.replace(',', '')
                # Ignore some of the noncourse related words
                if token in ['equivalent', 'consent', 'of', 'instructor', 'one']:
                    foundOr = False
                    category = None
                    # Found or
                elif token == 'or':
                    foundOr = True
                    # Found subject (CS, MATH, EECE, etc.)
                elif token.isupper() and len(token) > 1 or token == 'Math':
                    token = token.upper()
                    if not foundOr and courses:
                        # Sequence is like: CS 3250, CS 3251
                        final_reqs.append(courses.copy())
                        courses.clear()
                        category = token
                        # Found course number
                elif token.isdigit():
                    courses.append(f'{category} {token}')
                    if foundOr:
                        if len(courses) == 1:
                            # Sequence is like: a or b or c
                            final_reqs[-1].append(courses[0])
                        else:
                            # Sequence is like: a, b, or c
                            final_reqs.append(courses.copy())
                            courses.clear()
                            foundOr = False
                            # Other stuff
                else:
                    print("Unused Token:", token)
            for course in courses:
                final_reqs.append([course])
                prereqs[found_course] = [' or '.join(req) for req in final_reqs]
                
f.close()

print(prereqs)
