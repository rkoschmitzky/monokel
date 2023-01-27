#!/usr/bin/env python

import hashlib
import re

MOUNT_POINTS_IDENTIFIER = "paths"

with open("config.py") as f:
    config = f.read()
    # Let's strip all line breaks and spaces where it matters
    config = re.sub("(\n+\s+|\s*(?=:)|(?<=:)\s*)", "", config)

    mount_points = re.findall(
        r"(?<=\")([^\s,]*?)(?=\")",
        "{}".format(
            " ".join(
                re.findall(
                    r"(?<=(?:'|\"){}(?:'|\"):\[).*?(?=\])".format(MOUNT_POINTS_IDENTIFIER),
                    config
                )
            )
        )
    )

# Let's remove any potential duplicates
mount_points = set(mount_points)

# parse template and substitute placeholders
content = ""
with open("docker-compose.template") as f:
    template = f.read()
    # Look up our {VOLUMES\ place holder and identify the indent we need to use
    indent_length = len(re.findall(r"(?<=\n)\s+(?=\{VOLUMES\})", template)[0])
    replacement = "".join(
        [
            (r"\n" + " " * indent_length) + "- " +
            f"{_}:/{hashlib.sha256(_.encode()).hexdigest()[:7]}" for _ in mount_points
        ]
    )
    content = re.sub("\s+\{VOLUMES\}", replacement, template)

# write the compose yml file
with open("docker-compose.yml", "w+") as f:
    f.write(content)

