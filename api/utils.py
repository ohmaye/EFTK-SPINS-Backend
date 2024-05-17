def find_course(courses, course_id):
    if course_id:
        for course in courses:
            if course.get("id") == course_id:
                return course
    return {}


def get_active_slots(slots):
    # Sort the slots by startTime
    sorted_slots = sorted(slots, key=lambda slot: slot["startTime"])
    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    activeSlots = []
    for day in DAYS:
        activeSlots = activeSlots + [
            day + " " + slot["startTime"]
            for slot in sorted_slots
            if slot["active"] is True and slot["weekday"] == day
        ]
    return activeSlots
