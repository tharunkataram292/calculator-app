# Calc

A small, responsive calculator with a Python-powered arithmetic API. It uses only the Python standard library.

## Run

1. Install Python 3.10 or later.
2. From this folder, run `python app.py`.
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Set the `HOST` or `PORT` environment variables to change the server address. The default binds to localhost.

## Features

- Addition, subtraction, multiplication, division, parentheses, percentages, powers, and square roots.
- Keyboard input, clear and delete controls, and a recent-calculations list saved in the browser.
- Responsive layout and accessible labels.
- Arithmetic is parsed and evaluated by a restricted Python AST evaluator; Python code execution is not used.

## Tests

Run `python -m unittest` from this folder.
