#!/usr/bin/python

import os
import re
import sys

# We use that to get all start/end lines
CATEGORY = "^------ .* ------$"

# Most starting lines look like this
CATEGORY_START = "^------ {} (.*) ------$"

# Some of them do not comply, e.g. KERNEL LOG (dmesg)
CATEGORY_START_SPECIAL = "^------ {} ------$"

# End lines (used for initial search)
CATEGORY_END = "^------ [\0-9]+\.[0-9]+s was the duration of '(.+)' ------$"
BAD_CHARS = r"[\(\)\[\]\s\<\>\\\/\:\?\*\|\'\"]"

def get_headers(file):
    expr = re.compile(CATEGORY)
    headers = []
    offset = 0
    n = 0

    for line in file:
        if (expr.match(line)):
            headers.append({ "text" : line, "offset" : offset, "line" : n })
        offset = offset + len(line)
        n = n + 1
    return headers

def get_categories(headers):
    expr = re.compile(CATEGORY_END)
    expr_chars = re.compile(BAD_CHARS)
    categories = [ ]
    name_counts = { }

    # Now find the start string
    for index_end in range(len(headers)):
        header_end = headers[index_end]

        # Search by end header string
        matches = expr.match(header_end["text"])
        if (matches):
            name = matches.group(1)

            # Some ending headers DO NOT have a starting one, therefore we
            # need to check if they are all alone.
            # However, the start/end is serialized, meaning, for correct ending
            # headers, the starting header is ALWAYS the one before that
            header_start = headers[index_end - 1]
            text = header_start["text"]
            name_escaped = re.escape(name)
            r = CATEGORY_START.format(name_escaped)
            r_special = CATEGORY_START_SPECIAL.format(name_escaped)

            if re.match(r, text) or re.match(r_special, text):
                # Remove bad chars as it will be used as path
                name = expr_chars.sub('_', name)

                # Check if name is unique. If not, append a number
                if (name in name_counts):
                    name_counts[name] = name_counts[name] + 1
                    name = name + "-" + str(name_counts[name])
                else:
                    name_counts[name] = 1

                lines = header_end["line"] - header_start["line"]

                category = { "name" : name, "offset" : header_start["offset"], "lines" : lines }
                categories.append(category)
            else:
                print "Warning: Could not find start header for " + name

    return categories

if len(sys.argv) < 2:
    print "Please, provide filename"
    raise

filename = sys.argv[1]

with open(filename) as f:
    # Get the category headers (start/end lines) with their line numbers
    headers = get_headers(f)

    # Get categories
    categories = get_categories(headers)
    print "Found {} categories from {} headers in {}".format(len(categories), len(headers), filename)

    folder = filename + "_out"

    # Create output folder
    if not os.path.exists(folder):
        os.makedirs(folder)

    for c in categories:
        with open(folder + "/" + c["name"] + ".txt", "w") as out:
            f.seek(c["offset"])
            for x in range(c["lines"]):
                out.write(f.readline())

