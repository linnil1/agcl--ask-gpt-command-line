# AGCL (Ask-GPT-Command-Line)

## Overview

AGCL leverages the power of GPT/LLM (Large Language Models) to assist users in running commands without needing to remember the syntax or options. This project aims to simplify command-line usage by providing intelligent suggestions and fixes, similar to the functionality provided by tools like Shell-GPT(`sgpt`) and `thefuck`.

## Features

1. GPT-Powered Command Suggestions:
   * AGCL helps users by `agcl ask` suggesting command-line commands based on a simple description of what they want to achieve.
   * Users can choose from recommended commands provided by GPT.

2. Command Fixing with GPT:
   * If a command fails, users can call the `agcl fix` function.
   * AGCL will read the last command and its output (stdout/stderr) and suggest a fix.
   * The process may repeat, with GPT continually suggesting fixes until the issue is resolved or the user stops the process.

3. Other features in `sgpt` will not be implemented, I'm not going to replace it.


## Usage

### Example1: Asking command with option
``` bash
$ agcl ask list the python file in src/
This command lists all the Python files in the 'src' directory.

> Choose the command: ls src/*.py
src/config.py
src/history.py
src/interact.py
src/main.py
src/suggest.py
src/test.py

> Is problem solved? Yes
```


### Example2: Fixing Commands

```bash
$ python tests/example_bad_script.py
  File "/home/linnil1/agcl/tests/example_bad_script.py", line 1
    def plus(a, b)
                  ^
SyntaxError: expected ':'

$ agcl fix
Run the Python script again with the corrected syntax or fix the syntax error in the script file before running it.
> Choose the command: Fix the syntax error in the 'example_bad_script.py' file by adding a colon (:) after the function parameters.
/bin/sh: 1: Syntax error: "(" unexpected
Is problem solved? No

Add a colon (:) after the function parameters in the 'example_bad_script.py' file using sed command.
> Choose the command: sed -i 's/def plus(a, b)/def plus(a, b):/' /home/linnil1/agcl/tests/example_bad_script.py
Is problem solved? Yes

$ python tests/example_bad_script.py
8
```


## LICENSE
MIT