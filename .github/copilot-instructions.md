# Project General Coding Guidelines

## Workflows

- When working on a feature or bugfix, create your work plan and keep it in a local markdown file to track your progress. this is a todo list. Track implicit decisions you make along the way in this file.
- This repo uses a local .venv for python dependencies and poetry for dependency management. note also the makefile

## Code Style

- Avoid writing comments at all costs. If you see comments, refactor the code until they are not needed.

## Code Quality

- Follow the DRY (Don't Repeat Yourself) principle to minimize code duplication. Sometimes this means creating helper functions or classes, or searching if they already exist. If there are existing functions or classes that solve the problem, use them instead of reinventing the wheel. Sometimes small changes to expand existing functionality are acceptable.
- Write modular code that is easy to maintain and extend. Break down large functions or classes into smaller, reusable components.
- Ensure that your code is efficient and optimized for performance, especially in critical sections of the application.
- Write clear and descriptive variable and function names that convey their purpose and usage
- Follow SOLID principles to create maintainable and scalable code. Pay particular attention to the Single Responsibility Principle and the Open/Closed Principle.

## Testing Conventions

- Write tests that are easy to read and understand.
- Use the convention of test_cases = [(test_input, expected_output), ...] and a for loop to iterate through them in order to reduce code duplication and increase readability.
- Write functional tests that cover a wide range of scenarios, including edge cases.
- Do NOT use mocking or stubbing unless absolutely necessary. Prefer testing the actual behavior of the code.

## Running Commands

- This project has a virtual environment located at `.venv/`.
- Activate the virtual environment before running any commands: `source .venv/bin/activate`
- This project uses a Makefile to streamline common tasks.
