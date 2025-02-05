from collections import UserDict
import yaml
import glob
import re
import os
import subprocess


def extend_examples(api):
    if "examples" in api:
        extended = []
        for ex in api["examples"]:
            if isinstance(ex, str):
                for file in glob.glob(ex):
                    lines = open(file).read().split("\n")
                    name = re.sub(r"^#\s*", "", lines[0])
                    extended.append({"name": name, "query": "\n".join(lines)})
            else:
                extended.append(ex)
        api["examples"] = extended
    else:
        ap["examples"] = []


class Config(UserDict):
    def __init__(self, file, debug):
        try:
            with open(file) as stream:
                self.data = yaml.safe_load(stream)
        except yaml.YAMLError as err:
            msg = "Error in %s" % (file)
            if hasattr(err, 'problem_mark'):
                mark = err.problem_mark
                msg += " at line %s char %s" % (mark.line + 1, mark.column + 1)
            raise Exception(msg)

        if debug:
            self.data["debug"] = True
        elif not "debug" in self.data:
            self.data["debug"] = False

        if "import" in self.data:
            for name in ["collections", "terminologies"]:
                if name in self.data["import"]:
                    path = self.data["import"][name]
                    if not os.path.isdir(path):
                        raise Exception(f"Missing {name} path: {path}")
        else:
            self.data["import"] = {}

        extend_examples(self.data["sparql"])
        if "cypher" in self.data:
            extend_examples(self.data["cypher"])

        if not "tools" in self.data:
            self.data["tools"] = []

        try:
            self.data["githash"] = subprocess.run(['git', 'rev-parse', '--short=8', 'HEAD'],
                                                  stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        except Exception as e:
            self.data["githash"] = None
            pass
