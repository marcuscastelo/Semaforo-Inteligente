#!/bin/bash

echo Ensure you are on your virtual environment (if you have one)
read -n1 -r -p "Yes, i am ready to install darkflow at the actual environment [Any key]" key
git clone https://github.com/thtrieu/darkflow
cp init.py darkflow/
cd darkflow
pip install cython
pip install -e .