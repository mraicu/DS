## 1. HTML + CSS + JS assignment

Create a web page for your personal profile. The page should have three sections: The first section (which should also be the main section (“index.html”/home section)) should contain information about yourself: name, date of birth, education, places you’ve lived, etc. (information that you also have on your personal Facebook page). The second section should contain information about your professional work experience/education (which you also have on your Linkedin profile). And the third section should contain information about your hobbies/passions etc. The page should have a clean design (of your choice) and should contain at least 3 relevant animations (done with CSS) (of your choice). The details (name, date of birth, etc.) you expose on this page should be kept in one or multiple (at your choice) JSON objects in a javascript file. You should take that information and build the HTML document dynamically (create HTML elements/tags dynamically). You can use any CSS & JS library that you want.

Evaluation criteria:

- 1p by default
- 2p if you have the 3 sub-pages (sections) with relevant information
- 2p for design
- 2p for CSS animations
- 3p for using JS to build/create the HTML document dynamically (if you only populate the HTML tags with data from the JSON file you will get only 2 points)
  Deadline Lab 3.

## 2. Python assignment

Starting from the previous assignment (“1. HTML+CSS+JS Assignment”), we need to create a backend. Before, you had to keep all the data in a JSON object, and now we are moving that data to a database (SQLite is not accepted). Create a database with three tables, one containing data displayed in each section (e.g.: personal data, work experience, and hobbies). Create 3 APIs that will return this data. Use these APIs to get the data on UI for each particular section.

Evaluation criteria:

1p by default
3p for creating the database and the tables containing the proper data
3p for creating the 3 APIs
3p for using these APIs on the UI
Deadline Lab 4.

How to run: `uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`
