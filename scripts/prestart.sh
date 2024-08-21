#!/bin/sh -e

# Create initial data in DB
python /app/initial_data.py
python /app/initial_fake_data.py
