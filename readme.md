# Lighthouse

Use moving head lighting fixtures, a camera and a computer as a follow spot system.

## List of dependancies

Python 3.11 used for development

Python virtual environment recommended.

Then activate environment
source ./.venv/bin/activate

Then python packages installed using:
pip install -r requirements.txt

## IDE setup

VSCode extensions:
- CodeLLDB
- Python
- Black Formatter (switched to format on save)
- Pylance

Change default python autoformatter to autopep8 with format on save switched on.


## Compiling psn

macos
Got it working with
c++ -std=c++14 -shared -fPIC -Wl,-undefined,dynamic_lookup main.cpp -I/usr/local/lib/python3.11/site-packages/pybind11/include -I/usr/local/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/include/python3.11 -I../vendors/psn/include -o psn-py$(python3-config --extension-suffix)

Later found in the docs (https://pybind11.readthedocs.io/en/stable/compiling.html#building-manually):
c++ -O3 -Wall -shared -std=c++11 -undefined dynamic_lookup $(python3 -m pybind11 --includes) main.cpp -o example$(python3-config --extension-suffix)
