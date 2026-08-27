# TikTok Personal Analytics Platform

This project is intended to be a Flask-based web application that processes a user's exported TikTok watch history and presents the results through a simple frontend using analytics and visualisations.

It uses data processing and feature engineering to turn raw viewing records into behavioural insights such as activity patterns, usage trends, peak viewing times, and estimated viewing sessions.

## Why am I building it?

This project was inspired by sites such as Wasted on LoL, where a user enters their username and is shown statistics based on their League of Legends activity.

I wanted to build a similar experience for TikTok. After spending a lot of time scrolling, I was curious about how much time I had actually spent on the platform and what patterns could be found in my usage.

The aim is to present that data in a more interesting and visually appealing way, while also using the project to improve my skills in Python, Flask, Pandas, data processing, backend development, and data visualisation.

## Current Progress

Currently implemented:

* Parsing TikTok watch-history JSON
* Converting watch history into Pandas DataFrames
* Time-based feature engineering
* Daily, weekly, hourly, and weekday usage analytics
* Estimated viewing-session detection
* Session statistics such as duration and videos watched
* Matplotlib visualisations
* Displaying analytics and visualisations through Flask

Currently working on:

* Building the basic dashboard interface
* Adding more visualisations
* Preparing the project for user-uploaded TikTok exports
* Eventually replacing Matplotlib charts with interactive Plotly visualisations
* Deploying the application

> This project is still under active development.
