import re

# hot path — should keep/upgrade warnings
def handle_request(data):
    results = []
    for item in data:
        for sub in item:
            results.append(sub)
    return results

# cold path — should downgrade warnings
def setup_database():
    for i in range(10):
        process_item(i)
        sort_data([3,2,1])

# called once, low confidence — should be suppressed without --all
def migrate_schema():
    items = [1, 2, 3]
    for item in items:
        custom_transform(item)

def sort_data(lst):
    return sorted(lst)

def process_item(x):
    return x * 2

def custom_transform(x):
    return x + 1